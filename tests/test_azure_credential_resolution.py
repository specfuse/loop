#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The resolver must hand the SDKs a credential OBJECT, not a dict (#302).

`build_azure_transport` and `build_app_insights_transport` pass their `credential`
argument straight into `ServiceBusClient(credential=...)` and `LogsQueryClient(...)`,
both of which want an Azure `TokenCredential` — something with `get_token()`.

`_default_transport_resolver` was passing the *resolved credentials mapping*:

    resolved_credentials = {key: os.environ.get(value) for key, value in credentials.items()}
    ...
    _call_filtered(factory, credential=resolved_credentials or None, ...)

So `credential={'connection_string': 'Endpoint=sb://...'}` reached an SDK expecting an
object. Every real Azure call would fail. No test caught it because they all inject a
stub transport, and a stub accepts any `credential` argument — the same shape as #300,
one layer deeper.

`credential` and `credentials` are now distinct, which the factory signatures already
implied: **`credential` is the auth object; `credentials` stays the env-resolved
values** for any future factory that genuinely wants a secret string.

The credential is built by the **provider module**, looked up reflectively by the core
as `build_credential` — the first attempt at this fix put the SDK import in `cli.py`
and was caught by `test_no_provider_identifier_reaches_the_core`, the guard T01 shipped
to keep the dispatcher provider-agnostic.

`azure.identity` is not installed here and never will be — the package keeps zero
runtime dependencies (`verification.yml`) — so the missing-SDK test exercises the real
provider's real path rather than a simulated one.
"""

from __future__ import annotations

import types
import unittest

from specfuse.monitor.cli import MonitorCliError, _default_transport_resolver


class _FakeCredential:
    """Stands in for azure.identity.DefaultAzureCredential."""

    def get_token(self, *scopes, **kwargs):  # pragma: no cover - never called
        raise NotImplementedError


class _RecordingModule(types.ModuleType):
    """A provider module exposing one transport factory that records its kwargs."""

    def __init__(self):
        super().__init__("fake_provider")
        self.seen: dict = {}

        def build_azure_transport(*, fully_qualified_namespace, topic_name, credential):
            self.seen = {
                "fully_qualified_namespace": fully_qualified_namespace,
                "topic_name": topic_name,
                "credential": credential,
            }
            return object()

        self.build_azure_transport = build_azure_transport

        # Real provider modules expose this; the core looks it up reflectively.
        self.build_credential = _FakeCredential


_BINDING = {
    "provider": "azure-service-bus",
    "fully_qualified_namespace": "ns.servicebus.windows.net",
    "topic_name": "orders",
    "credentials": {"connection_string": "SCRATCH_SB_CONNECTION_STRING"},
}


class TestCredentialIsAnObject(unittest.TestCase):

    def test_factory_receives_a_credential_object_not_a_mapping(self):
        """The #302 regression: a dict here fails on the first real SDK call."""
        module = _RecordingModule()
        _default_transport_resolver(module, "dlq", _BINDING)

        credential = module.seen["credential"]
        self.assertNotIsInstance(
            credential, dict,
            "credential must be an Azure TokenCredential object; a mapping is what "
            "#302 was filed for and what every real SDK call rejects")
        self.assertTrue(
            hasattr(credential, "get_token"),
            f"credential {credential!r} does not look like a TokenCredential")

    def test_the_binding_coordinates_still_reach_the_factory(self):
        """The credential change must not disturb the `extra` passthrough."""
        module = _RecordingModule()
        _default_transport_resolver(module, "dlq", _BINDING)

        self.assertEqual(
            module.seen["fully_qualified_namespace"], "ns.servicebus.windows.net")
        self.assertEqual(module.seen["topic_name"], "orders")

    def test_a_provider_without_the_hook_gets_no_credential(self):
        """Not every provider needs one; the reflective lookup must degrade."""
        module = _RecordingModule()
        del module.build_credential
        _default_transport_resolver(module, "dlq", _BINDING)
        self.assertIsNone(module.seen["credential"])

    def test_missing_azure_identity_is_diagnosed_not_a_raw_importerror(self):
        """The first thing a new operator hits if the SDK extra is not installed.

        Exercises the REAL provider's `build_credential`; `azure.identity` is
        genuinely absent in this repo, so this is the real path, not a simulated one.
        """
        from specfuse.monitor.providers import azure_service_bus

        with self.assertRaises(MonitorCliError) as ctx:
            azure_service_bus.build_credential()

        message = str(ctx.exception)
        self.assertIn("azure-identity", message,
                      "the error must name the missing package")
        self.assertIn("specfuse-loop[azure]", message,
                      "the error must name how to install it")


if __name__ == "__main__":
    unittest.main()
