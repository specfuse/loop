# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3471: every built-in App Insights query is checked against the Log
Analytics workspace schema it runs on.

#3468 shipped because the adapter tests use a stub transport that ignores the
query text, so KQL naming tables and columns a workspace does not have passed
the suite for months. Two checks close that gap:

- ``TestBuiltInQueriesMatchWorkspaceSchema`` runs in CI with no Azure access.
  It extracts the source table and the source columns from each built-in
  query and fails when either falls outside ``WORKSPACE_SCHEMA`` below.
- ``TestBuiltInQueriesRunAgainstLiveWorkspace`` is opt-in: it runs each
  built-in query with ``| take 0`` against a real workspace, so a maintainer
  can confirm the checked-in reference still matches Azure.

The extractor is a tokenizer scoped to the shapes these queries take
(``Table | where ... | project/summarize ...``), not a KQL parser. An
identifier it does not recognise is treated as a column and must be in the
reference, so a new KQL keyword fails loudly here (add it to
``_KQL_KEYWORDS``) rather than letting a wrong column through.
"""

from __future__ import annotations

import os
import re
import unittest

from specfuse.monitor.providers import azure_app_insights as aai

# Source: Microsoft Learn, "Azure Monitor Logs reference" table pages (page
# date 2026-07-27, MicrosoftDocs/azure-monitor-docs-pr @ 0797475):
#   https://learn.microsoft.com/azure/azure-monitor/reference/tables/appexceptions
#   https://learn.microsoft.com/azure/azure-monitor/reference/tables/apprequests
#   https://learn.microsoft.com/azure/azure-monitor/reference/tables/appevents
# Columns are the documented Columns tables, minus the underscore-prefixed
# system columns (_BilledSize, _IsBillable, _ResourceId, _SubscriptionId).
# Re-confirm against Azure with the opt-in live check below when updating.
_COMMON_APP_COLUMNS = frozenset({
    "AppRoleInstance", "AppRoleName", "AppVersion",
    "ClientBrowser", "ClientCity", "ClientCountryOrRegion", "ClientIP",
    "ClientModel", "ClientOS", "ClientStateOrProvince", "ClientType",
    "IKey", "ItemCount", "Measurements", "OperationId", "OperationName",
    "ParentId", "Properties", "ResourceGUID", "SDKVersion", "SessionId",
    "SourceSystem", "SyntheticSource", "TenantId", "TimeGenerated", "Type",
    "UserAccountId", "UserAuthenticatedId", "UserId",
})

WORKSPACE_SCHEMA: dict[str, frozenset[str]] = {
    "AppExceptions": _COMMON_APP_COLUMNS | {
        "Assembly", "Details", "ExceptionType", "HandledAt",
        "InnermostAssembly", "InnermostMessage", "InnermostMethod",
        "InnermostType", "Message", "Method", "OuterAssembly", "OuterMessage",
        "OuterMethod", "OuterType", "ProblemId", "SeverityLevel",
    },
    "AppRequests": _COMMON_APP_COLUMNS | {
        "DurationMs", "Id", "Name", "ReferencedItemId", "ReferencedType",
        "ResultCode", "Source", "Success", "Url",
    },
    "AppEvents": _COMMON_APP_COLUMNS | {"Name"},
    "AppDependencies": _COMMON_APP_COLUMNS | {
        "Data", "DependencyType", "DurationMs", "Id", "Name", "ResultCode",
        "Success", "Target",
    },
}

# Operators, keywords and literals the built-in queries use. Function calls
# (an identifier followed by ``(``) are skipped without being listed here.
_KQL_KEYWORDS = frozenset({
    "where", "project", "summarize", "extend", "by", "take", "limit",
    "and", "or", "not", "startswith", "endswith", "contains", "has", "in",
    "true", "false", "asc", "desc", "order", "sort",
    "join", "kind", "inner", "leftouter", "on", "mv", "expand",
})

# Tabular operator names KQL reserves: a bare output alias spelled like one
# does not parse in a workspace (#3506, `sample = take_anyif(...)`), so an
# alias here is a violation even though it is never read as a column.
_RESERVED_ALIASES = frozenset({
    "as", "by", "consume", "count", "distinct", "evaluate", "extend", "facet",
    "find", "fork", "getschema", "invoke", "join", "limit", "lookup", "on",
    "order", "parse", "print", "project", "range", "reduce", "render", "sample",
    "search", "serialize", "sort", "summarize", "take", "top", "union", "where",
})

_STRING_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
# An identifier, with what precedes it (a ``.`` marks a dynamic property
# access, not a column) and what follows it (``(`` is a call, a lone ``=``
# is an output alias).
_IDENT = re.compile(r"(?P<dot>\.\s*)?\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b(?=\s*(?P<after>\(|==|=)?)")
# An output name defined anywhere in the query, so a later stage may read it.
_ALIAS = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)")


def schema_violations(query: str) -> list[str]:
    """Names in *query* that are not in ``WORKSPACE_SCHEMA``, as messages.

    The first pipe stage is the source table; every other identifier that
    is not a keyword, a function name, a dynamic-property segment, or an
    alias defined on the left of ``=`` must be a column of that table.
    """
    text = _STRING_LITERAL.sub("''", query)
    table, _, rest = text.partition("|")
    table = table.strip()
    columns = WORKSPACE_SCHEMA.get(table)
    if columns is None:
        return [f"table {table!r} is not a workspace table"]
    # A joined subquery reads its own table: its columns are valid too.
    for joined in re.findall(r"\(\s*(\w+)\s*\|", rest):
        columns = columns | WORKSPACE_SCHEMA.get(joined, frozenset())
    aliases = set(_ALIAS.findall(rest))
    problems = [
        f"alias {name!r} is a reserved KQL operator name"
        for name in sorted(aliases) if name.lower() in _RESERVED_ALIASES
    ]
    for match in _IDENT.finditer(rest):
        name, after = match.group("name"), match.group("after")
        if match.group("dot") or after in ("(", "="):
            continue
        if name.lower() in _KQL_KEYWORDS or name in columns or name in aliases\
                or name in WORKSPACE_SCHEMA:
            continue
        problems.append(f"column {name!r} is not a column of {table}")
    return problems


_BUILT_IN_QUERIES = {
    "error-logs": aai._error_logs_query,
    "http-5xx": aai._http_5xx_query,
    "heartbeat": aai._heartbeat_query,
    "http-status-regression": lambda component: aai._http_status_regression_query(
        component, 3600, ["401", "403"]
    ),
}


class TestBuiltInQueriesMatchWorkspaceSchema(unittest.TestCase):
    def test_every_built_in_query_uses_only_workspace_names(self):
        for check, build in _BUILT_IN_QUERIES.items():
            with self.subTest(check=check):
                query = build("backend-api")
                self.assertEqual(schema_violations(query), [], query)

    def test_component_value_is_not_read_as_a_column(self):
        # The component lands in a string literal; whatever it says, it is
        # data, not a column reference.
        query = aai._http_5xx_query("StatusCode")
        self.assertEqual(schema_violations(query), [])


class TestSchemaCheckRejectsWrongNames(unittest.TestCase):
    """The checker must catch the defects it exists for — including the
    pre-#3469 classic App Insights queries."""

    def test_classic_table_is_rejected(self):
        query = "exceptions | where cloud_RoleName == 'x' | project timestamp, operation_Id"
        self.assertEqual(schema_violations(query), ["table 'exceptions' is not a workspace table"])

    def test_classic_pre_3469_queries_are_rejected(self):
        for query in (
            "exceptions | where cloud_RoleName == 'x' "
            "| project timestamp, operation_Id, operation_ParentId, type, outerMessage",
            "requests | where cloud_RoleName == 'x' and resultCode startswith '5' "
            "| project timestamp, operation_Id, name, resultCode",
            "customEvents | where cloud_RoleName == 'x' and name == 'ScheduleHeartbeat' "
            "| summarize last_heartbeat = max(timestamp) by name = tostring(customDimensions.scheduleName)",
        ):
            with self.subTest(query=query):
                self.assertNotEqual(schema_violations(query), [])

    def test_classic_columns_on_a_workspace_table_are_rejected(self):
        query = "AppExceptions | where cloud_RoleName == 'x' | project timestamp, operation_Id"
        self.assertEqual(
            schema_violations(query),
            [
                "column 'cloud_RoleName' is not a column of AppExceptions",
                "column 'timestamp' is not a column of AppExceptions",
                "column 'operation_Id' is not a column of AppExceptions",
            ],
        )

    def test_column_from_another_table_is_rejected(self):
        # ResultCode exists on AppRequests, not on AppEvents.
        query = "AppEvents | where ResultCode startswith '5' | project Name"
        self.assertEqual(
            schema_violations(query), ["column 'ResultCode' is not a column of AppEvents"]
        )

    def test_mutated_http_5xx_filter_is_rejected(self):
        # The issue's repro: filter on a column AppRequests does not have.
        query = aai._http_5xx_query("backend-api").replace(
            "ResultCode startswith", "StatusCode startswith"
        )
        self.assertEqual(
            schema_violations(query), ["column 'StatusCode' is not a column of AppRequests"]
        )

    def test_classic_dynamic_column_is_rejected_but_property_path_is_not(self):
        bad = "AppEvents | summarize max(TimeGenerated) by tostring(customDimensions.scheduleName)"
        self.assertEqual(
            schema_violations(bad), ["column 'customDimensions' is not a column of AppEvents"]
        )
        good = "AppEvents | summarize max(TimeGenerated) by tostring(Properties.scheduleName)"
        self.assertEqual(schema_violations(good), [])

    def test_alias_is_an_output_name_but_its_source_is_checked(self):
        self.assertEqual(
            schema_violations("AppRequests | project timestamp = TimeGenerated"), []
        )
        self.assertEqual(
            schema_violations("AppRequests | project TimeGenerated = timestamp"),
            ["column 'timestamp' is not a column of AppRequests"],
        )


# Opt-in live check. Same opt-in variable as the GitHub live tests
# (tests/_live.py, #3223), plus the workspace to query.
_LIVE_OPT_IN_VAR = "SPECFUSE_LIVE_TESTS"
_LIVE_WORKSPACE_VAR = "SPECFUSE_LIVE_WORKSPACE_ID"


def _live_workspace_skip_reason() -> str:
    if os.environ.get(_LIVE_OPT_IN_VAR, "") != "1":
        return f"{_LIVE_OPT_IN_VAR} is not set to 1 — live tests are opt-in"
    if not os.environ.get(_LIVE_WORKSPACE_VAR, "").strip():
        return f"{_LIVE_WORKSPACE_VAR} must name the Log Analytics workspace ID"
    try:
        import azure.identity  # noqa: F401
        import azure.monitor.query  # noqa: F401
    except ImportError:
        return "azure-monitor-query and azure-identity must be installed"
    return ""


class TestBuiltInQueriesRunAgainstLiveWorkspace(unittest.TestCase):
    """Runs each built-in query, with ``| take 0``, against a real workspace.

    Credentials come from the provider's own ``build_credential``
    (``DefaultAzureCredential``). A table or column the workspace cannot
    resolve raises ``HttpResponseError`` from ``query_workspace``.
    """

    @classmethod
    def setUpClass(cls):
        reason = _live_workspace_skip_reason()
        if reason:
            raise unittest.SkipTest(reason)

    def test_every_built_in_query_resolves_in_the_workspace(self):
        from azure.monitor.query import LogsQueryClient, LogsQueryStatus

        from specfuse.monitor.providers._azure_auth import build_credential

        client = LogsQueryClient(build_credential())
        workspace_id = os.environ[_LIVE_WORKSPACE_VAR].strip()
        for check, build in _BUILT_IN_QUERIES.items():
            with self.subTest(check=check):
                response = client.query_workspace(
                    workspace_id=workspace_id,
                    query=build("specfuse-schema-probe") + " | take 0",
                    timespan=None,
                )
                self.assertEqual(response.status, LogsQueryStatus.SUCCESS)


if __name__ == "__main__":
    unittest.main()


class TestReservedAliasIsAViolation(unittest.TestCase):
    """#3506: `sample = ...` passed this check and failed to parse live."""

    def test_reserved_alias_is_reported(self):
        self.assertIn(
            "alias 'sample' is a reserved KQL operator name",
            schema_violations("AppRequests | summarize sample = take_any(OperationId) by Name"),
        )

    def test_ordinary_alias_is_not(self):
        self.assertEqual(
            schema_violations("AppRequests | summarize sampleOp = take_any(OperationId) by Name"), []
        )

