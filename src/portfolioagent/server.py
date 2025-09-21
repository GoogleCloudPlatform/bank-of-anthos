import grpc
from concurrent import futures
import time
import json
import importlib
import random  # Needed for dummy trade confirmation IDs

import agent_gateway_pb2
import agent_gateway_pb2_grpc
import jwt
import bq_logger

# --- Configuration & Authentication ---
SECRET_KEY = (
    "your-super-secret-key-that-is-not-in-code"  # Loaded from secure config in real app
)


class JwtAuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        """Intercepts RPCs for JWT authentication."""
        auth_metadata = None
        for key, value in handler_call_details.invocation_metadata:
            if key == "authorization":
                auth_metadata = value
                break

        if auth_metadata is None:
            context = grpc.ServicerContext()
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED, "Missing authorization token."
            )
            return None

        token = auth_metadata.replace("Bearer ", "")
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            context = grpc.ServicerContext()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")
            return None

        return continuation(handler_call_details)


# --- Tool-Calling Infrastructure ---
def load_tool_registry():
    """Loads the tool registry from the JSON file."""
    with open("tools.json", "r") as f:
        return json.load(f)


TOOL_REGISTRY = load_tool_registry()


def execute_tool(user_id: str, tool_name: str, params: dict):
    """Executes a tool with retries and logs the final result to BigQuery."""
    if tool_name not in TOOL_REGISTRY:
        result = {"status": "error", "message": f"Tool '{tool_name}' not found."}
        bq_logger.log_tool_call(user_id, tool_name, params, result)
        return result

    tool_info = TOOL_REGISTRY[tool_name]
    max_retries = 2
    final_result = {}

    for attempt in range(max_retries):
        try:
            module = importlib.import_module(tool_info["module"])
            tool_callable = getattr(module, tool_info["callable"])
            result = tool_callable(**params)
            if result.get("status") == "error":
                raise Exception(result.get("message", "Tool execution failed"))
            final_result = result
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} for tool '{tool_name}' failed: {e}")
            final_result = {
                "status": "error",
                "message": f"Tool '{tool_name}' failed after {attempt + 1} attempts.",
            }

    bq_logger.log_tool_call(user_id, tool_name, params, final_result)
    return final_result


# --- gRPC Service Implementation for Human-in-the-Loop ---

# NEW: In-memory store for proposed actions.
# In a production system, this would be a persistent store (e.g., Redis, database).
# Structure: {action_id: {"user_id": ..., "tool_name": ..., "params": ..., "proposed_changes": ...}}
PROPOSED_ACTIONS_STORE = {}

# NEW: Define sensitive tools that require pre-checks before execution
SENSITIVE_TOOLS = ["execute_trade"]


class AgentGatewayServicer(agent_gateway_pb2_grpc.AgentGatewayServicer):
    """
    Implements the AgentGateway service with Human-in-the-Loop (HITL) workflow.
    Handles ProposeAction and ConfirmAction RPCs.
    """

    def ProposeAction(self, request, context):
        """
        Analyzes the user's query, runs guardrails, and proposes an action.
        Does NOT execute any sensitive tools directly.
        """
        user_id = request.user_id
        query_text = request.query_text.strip()
        action_id = str(
            random.randint(100000, 999999)
        )  # Generate a unique ID for this proposal

        print(
            f"\n--- ProposeAction for user '{user_id}' with query: '{query_text}' ---"
        )

        # --- Dummy Data for Demonstration ---
        # In a real scenario, these would come from the request or a dynamic agent plan
        dummy_portfolio = {"CASH_USD": 500, "GOOG": 9500}
        dummy_total_value = 10000
        dummy_trade_details = {"asset": "GOOG", "amount": 10, "action": "BUY"}
        # Assume the AI decided to call 'execute_trade' based on 'query_text'
        tool_to_propose = "execute_trade"
        proposed_tool_params = {
            "user_id": user_id,
            "trade_details": dummy_trade_details,
        }

        # 1. Check if the proposed tool is known
        if tool_to_propose not in TOOL_REGISTRY:
            bq_logger.log_tool_call(
                user_id,
                tool_to_propose,
                proposed_tool_params,
                {"status": "error", "message": "Tool not found during proposal."},
            )
            return agent_gateway_pb2.ProposeActionResponse(
                action_id="",
                explanation="I could not understand your request.",
                status_message="Failed to generate plan: Tool not found.",
            )

        # 2. Run Guardrails for Sensitive Tools
        if tool_to_propose in SENSITIVE_TOOLS:
            print(
                f"Sensitive tool '{tool_to_propose}' proposed. Initiating pre-checks..."
            )

            # Run Compliance Pre-Check
            compliance_params = {
                "portfolio_assets": dummy_portfolio,
                "total_value": dummy_total_value,
            }
            compliance_result = execute_tool(
                user_id, "check_portfolio_compliance", compliance_params
            )

            if not compliance_result.get("compliant"):
                violations = compliance_result.get(
                    "violations", ["Unknown compliance violation"]
                )
                explanation = f"Proposed action violates compliance rules: {', '.join(violations)}."
                print(f"❌ Guardrail Block: {explanation}")
                return agent_gateway_pb2.ProposeActionResponse(
                    action_id="",
                    explanation=explanation,
                    status_message="Failed to generate plan: Compliance violation.",
                )
            print("✅ Compliance pre-check PASSED.")

            # Run Risk Pre-Check
            risk_params = {
                "user_id": user_id,
                "portfolio_assets": list(dummy_portfolio.keys()),
            }
            risk_result = execute_tool(user_id, "analyze_portfolio_risk", risk_params)

            risk_score = risk_result.get("risk_score", 1.0)
            if risk_score > 0.75:
                explanation = f"Proposed action carries high risk (score: {risk_score}). Risk score exceeds threshold of 0.75."
                print(f"❌ Guardrail Block: {explanation}")
                return agent_gateway_pb2.ProposeActionResponse(
                    action_id="",
                    explanation=explanation,
                    status_message="Failed to generate plan: High risk.",
                )
            print(f"✅ Risk pre-check PASSED (score: {risk_score}).")

        print(f"All pre-checks passed for proposed action '{tool_to_propose}'.")

        # 3. Store the proposed action for later confirmation
        PROPOSED_ACTIONS_STORE[action_id] = {
            "user_id": user_id,
            "tool_name": tool_to_propose,
            "params": proposed_tool_params,
            "proposed_changes": [
                f"Buy {dummy_trade_details['amount']} shares of {dummy_trade_details['asset']}"
            ],
        }

        # 4. Return the proposed plan to the user
        explanation = f"I recommend to {PROPOSED_ACTIONS_STORE[action_id]['proposed_changes'][0]} to optimize your portfolio given current market conditions."
        print(f"✅ Action Proposed (ID: {action_id}). Awaiting user confirmation.")

        return agent_gateway_pb2.ProposeActionResponse(
            action_id=action_id,
            explanation=explanation,
            proposed_changes=PROPOSED_ACTIONS_STORE[action_id]["proposed_changes"],
            status_message="Plan generated successfully. Awaiting confirmation.",
        )

    def ConfirmAction(self, request, context):
        """
        Executes a previously proposed and approved action.
        """
        user_id = request.user_id
        action_id = request.action_id

        print(
            f"\n--- ConfirmAction for user '{user_id}' with action ID: '{action_id}' ---"
        )

        # 1. Retrieve the proposed action from the store
        proposed_action = PROPOSED_ACTIONS_STORE.pop(
            action_id, None
        )  # Remove after use

        if proposed_action is None:
            print(f"❌ Error: Action ID '{action_id}' not found or already confirmed.")
            return agent_gateway_pb2.ConfirmActionResponse(
                confirmation_id="",
                status_message="Action ID not found or already processed.",
            )
        if proposed_action["user_id"] != user_id:
            print(f"❌ Error: Mismatched user_id for action ID '{action_id}'.")
            return agent_gateway_pb2.ConfirmActionResponse(
                confirmation_id="", status_message="Unauthorized: User ID mismatch."
            )

        # 2. Execute the tool
        print(
            f"Executing tool '{proposed_action['tool_name']}' for user '{user_id}'..."
        )
        execution_result = execute_tool(
            user_id=user_id,
            tool_name=proposed_action["tool_name"],
            params=proposed_action["params"],
        )

        if execution_result.get("status") == "success":
            confirmation_id = execution_result.get(
                "confirmation_id", f"CONF_{random.randint(1000, 9999)}"
            )
            print(
                f"✅ Action Confirmed and Executed (Confirmation ID: {confirmation_id})."
            )
            return agent_gateway_pb2.ConfirmActionResponse(
                confirmation_id=confirmation_id,
                status_message="Action executed successfully.",
            )
        else:
            print(f"❌ Error during execution: {execution_result.get('message')}")
            return agent_gateway_pb2.ConfirmActionResponse(
                confirmation_id="",
                status_message=f"Failed to execute action: {execution_result.get('message', 'Unknown error.')}",
            )


def serve():
    """Starts the gRPC server with the auth interceptor."""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), interceptors=[JwtAuthInterceptor()]
    )
    agent_gateway_pb2_grpc.add_AgentGatewayServicer_to_server(
        AgentGatewayServicer(), server
    )
    port = "8080"
    server.add_insecure_port(f"[::]:{port}")
    print(f"🔐 Agent Server with HITL & Guardrails started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
