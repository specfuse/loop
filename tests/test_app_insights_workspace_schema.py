# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Regression tests for #3468: the App Insights adapters must query the
Log Analytics workspace schema.

``build_app_insights_transport`` runs every query through
``LogsQueryClient.query_workspace``, which resolves only workspace tables
(``AppExceptions``, ``AppRequests``, ``AppEvents``) and columns
(``AppRoleName``, ``TimeGenerated``, ``Properties``, ...). The classic
Application Insights names (``exceptions``, ``requests``, ``customEvents``,
``cloud_RoleName``, ``timestamp``, ``customDimensions``) fail there with
"Failed to resolve table or column expression". Each query must also alias
its columns back to the keys the adapters read from the returned rows, so
nothing downstream of the transport changes.
"""

from __future__ import annotations

import re
import unittest

from specfuse.monitor.providers import azure_app_insights as aai

_CLASSIC_TABLES = ("exceptions", "requests", "customEvents")
_CLASSIC_FILTER_COLUMNS = ("cloud_RoleName", "customDimensions", "resultCode startswith")


def _source_table(query: str) -> str:
    return query.split("|", 1)[0].strip()


def _projected_keys(query: str) -> list[str]:
    """The output column names of the query's final ``project`` stage."""
    project = query.rsplit("| project ", 1)[1]
    return [item.split("=", 1)[0].strip() for item in project.split(",")]


class TestWorkspaceSchemaQueries(unittest.TestCase):
    def assert_no_classic_names(self, query: str) -> None:
        self.assertNotIn(_source_table(query), _CLASSIC_TABLES)
        for name in _CLASSIC_FILTER_COLUMNS:
            self.assertNotIn(name, query)
        self.assertIsNone(re.search(r"\bmax\(timestamp\)", query))

    def test_error_logs_query_reads_app_exceptions(self):
        query = aai._error_logs_query("backend-api")
        self.assertEqual(_source_table(query), "AppExceptions")
        self.assertIn("AppRoleName == 'backend-api'", query)
        self.assert_no_classic_names(query)
        self.assertEqual(
            _projected_keys(query),
            [
                "timestamp", "operation_Id", "operation_ParentId", "type", "outerMessage",
                "instance", "loggerCategory", "loggerTemplate", "requestName",
                "requestResult", "frameMethod", "frameAssembly", "clientAbort",
            ],
        )
        self.assertIn("timestamp = TimeGenerated", query)
        self.assertIn("type = ExceptionType", query)
        self.assertIn("outerMessage = OuterMessage", query)

    def test_http_5xx_query_reads_app_requests(self):
        query = aai._http_5xx_query("backend-api")
        self.assertEqual(_source_table(query), "AppRequests")
        self.assertIn("AppRoleName == 'backend-api'", query)
        self.assertIn("ResultCode startswith '5'", query)
        self.assert_no_classic_names(query)
        self.assertEqual(
            _projected_keys(query), ["timestamp", "operation_Id", "name", "resultCode"]
        )
        self.assertIn("name = Name", query)
        self.assertIn("resultCode = ResultCode", query)

    def test_heartbeat_query_reads_app_events(self):
        query = aai._heartbeat_query("backend-worker")
        self.assertEqual(_source_table(query), "AppEvents")
        self.assertIn("AppRoleName == 'backend-worker'", query)
        self.assertIn("Name == 'ScheduleHeartbeat'", query)
        self.assert_no_classic_names(query)
        # The adapter reads `name` and `last_heartbeat` from each row.
        self.assertIn("last_heartbeat = max(TimeGenerated)", query)
        self.assertIn("by name = tostring(Properties.scheduleName)", query)


if __name__ == "__main__":
    unittest.main()
