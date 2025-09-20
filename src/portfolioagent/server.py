# src/portfolioagent/server.py

import grpc
from concurrent import futures
import json
import importlib

import agent_gateway_pb2
import agent_gateway_pb2_grpc
import jwt
import bq_logger

# --- Authentication Middleware ---
# In a real application, this should be loaded from a secure configuration (e.g., Secret Manager)
SECRET_KEY = "your-super-secret-key-that-is-not-in-code"


class JwtAuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        """Intercepts incoming RPCs to enforce JWT authentication."""
        auth_metadata = None
        for key, value in handler_call_details.invocation_metadata:
            if key == "authorization":
                auth_metadata = value
                break

        if auth_metadata is None:
            print("❌ Auth Error: Missing authorization metadata.")
            context = grpc.ServicerContext()
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED, "Missing authorization token."
            )
            return None

        token = auth_metadata.replace("Bearer ", "")
        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Add user_id to the context so the servicer can access it
            # handler_call_details.context.user_id = decoded_token["user_id"]
            print(f"✅ Authenticated user: {decoded_token['user_id']}")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            print("❌ Auth Error: Invalid or expired token.")
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
    # ... (This function remains unchanged from our previous step) ...
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


# --- gRPC Service Implementation ---

# --- NEW: Define sensitive tools that require pre-checks ---
SENSITIVE_TOOLS = ["execute_trade"]


class AgentGatewayServicer(agent_gateway_pb2_grpc.AgentGatewayServicer):
    """
    Implements the AgentGateway service with pre-check guardrails.
    This class now acts as a workflow orchestrator.
    """

    def ProcessRequest(self, request, context):
        """Handles the ProcessRequest RPC, orchestrating pre-checks for sensitive tools."""
        user_id = request.user_id
        tool_to_call = request.query_text.strip()
        print(f"Received request from user '{user_id}' for tool: '{tool_to_call}'")

        # --- MODIFIED: Pre-check Logic ---
        if tool_to_call in SENSITIVE_TOOLS:
            print(
                f"Sensitive tool '{tool_to_call}' requested. Initiating pre-checks..."
            )

            # 1. Define dummy data for checks. In a real scenario, this would be part of the request.
            dummy_portfolio = {"CASH_USD": 500, "GOOG": 9500}
            dummy_total_value = 10000

            # 2. Run Compliance Pre-Check
            compliance_params = {
                "portfolio_assets": dummy_portfolio,
                "total_value": dummy_total_value,
            }
            compliance_result = execute_tool(
                user_id, "check_portfolio_compliance", compliance_params
            )

            if not compliance_result.get("compliant"):
                error_msg = f"Guardrail Block: Action failed compliance checks. Violations: {compliance_result.get('violations')}"
                print(f"❌ {error_msg}")
                return agent_gateway_pb2.AgentResponse(
                    response_text=json.dumps({"status": "error", "message": error_msg})
                )

            print("✅ Compliance pre-check PASSED.")

            # 3. Run Risk Pre-Check
            risk_params = {
                "user_id": user_id,
                "portfolio_assets": list(dummy_portfolio.keys()),
            }
            risk_result = execute_tool(user_id, "analyze_portfolio_risk", risk_params)

            risk_score = risk_result.get(
                "risk_score", 1.0
            )  # Default to high risk on error
            if risk_score > 0.75:
                error_msg = f"Guardrail Block: Action failed risk check. Risk score {risk_score} exceeds threshold of 0.75."
                print(f"❌ {error_msg}")
                return agent_gateway_pb2.AgentResponse(
                    response_text=json.dumps({"status": "error", "message": error_msg})
                )

            print(f"✅ Risk pre-check PASSED (score: {risk_score}).")

        # --- End of Pre-check Logic ---

        # If it's a non-sensitive tool OR a sensitive tool that passed all checks, execute it.
        print(f"All checks passed for '{tool_to_call}'. Proceeding with execution...")

        available_data = {
            "user_id": user_id,
            "portfolio_assets": ["GOOG", "TSLA"],  # Dummy data
            "trade_details": {
                "asset": "GOOG",
                "amount": 10,
                "action": "BUY",
            },  # Dummy data
        }

        required_params = TOOL_REGISTRY[tool_to_call].get("parameters", [])
        final_params = {
            key: available_data[key] for key in required_params if key in available_data
        }

        result = execute_tool(
            user_id=user_id, tool_name=tool_to_call, params=final_params
        )

        return agent_gateway_pb2.AgentResponse(response_text=json.dumps(result))


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
    print(f"🔐 Agent Server with Guardrails started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
