from google.cloud import bigquery
import datetime
import json
import os

PROJECT_ID = "gke10-agentic-portfolio"
TABLE_ID = f"{PROJECT_ID}.agent_audit.tool_calls"


def log_tool_call(user_id: str, tool_name: str, params: dict, result: dict):
    """Streams a tool call audit record to BigQuery."""
    try:
        client = bigquery.Client()

        row_to_insert = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": user_id,
            "tool_name": tool_name,
            "parameters": json.dumps(params),
            "result": json.dumps(result),
        }

        errors = client.insert_rows_json(TABLE_ID, [row_to_insert])
        if errors:
            print(
                f"BQ Logging Error: Encountered errors while inserting rows: {errors}"
            )
        else:
            print(f"✅ Successfully logged '{tool_name}' call to BigQuery.")

    except Exception as e:
        print(f"BQ Logging CRITICAL ERROR: Failed to log to BigQuery. Reason: {e}")
