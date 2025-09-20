# src/portfolioagent/server.py

import grpc
from concurrent import futures
import time
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
            return None  # Must return None to abort the call

        token = auth_metadata.replace("Bearer ", "")
        try:
            # Decode and validate the token
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(f"✅ Authenticated user: {decoded_token['user_id']}")
        except jwt.ExpiredSignatureError:
            print("❌ Auth Error: Token has expired.")
            context = grpc.ServicerContext()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token has expired.")
            return None
        except jwt.InvalidTokenError:
            print("❌ Auth Error: Invalid token.")
            context = grpc.ServicerContext()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid token.")
            return None

        # If the token is valid, continue to the actual RPC method
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
            break  # Exit loop on success

        except Exception as e:
            print(f"Attempt {attempt + 1} for tool '{tool_name}' failed: {e}")
            final_result = {
                "status": "error",
                "message": f"Tool '{tool_name}' failed after {attempt + 1} attempts.",
            }

    # Log the final outcome of the tool call to BigQuery
    bq_logger.log_tool_call(user_id, tool_name, params, final_result)
    return final_result


# --- gRPC Service Implementation ---


class AgentGatewayServicer(agent_gateway_pb2_grpc.AgentGatewayServicer):
    """Implements the AgentGateway service."""

    def ProcessRequest(self, request, context):
        """Handles the ProcessRequest RPC with tool-calling and logging logic."""
        print(
            f"Received request from user '{request.user_id}' with query: '{request.query_text}'"
        )
        tool_to_call = request.query_text.strip()

        # This block now also handles logging for tools that aren't found
        if tool_to_call not in TOOL_REGISTRY:
            error_result = {
                "status": "error",
                "message": f"Tool '{tool_to_call}' not found.",
            }
            bq_logger.log_tool_call(request.user_id, tool_to_call, {}, error_result)
            return agent_gateway_pb2.AgentResponse(
                response_text=json.dumps(error_result)
            )

        available_data = {
            "user_id": request.user_id,
            "portfolio_assets": ["GOOG", "TSLA"],
        }

        required_params = TOOL_REGISTRY[tool_to_call].get("parameters", [])
        final_params = {
            key: available_data[key] for key in required_params if key in available_data
        }

        # We pass the user_id into execute_tool for logging purposes
        result = execute_tool(
            user_id=request.user_id, tool_name=tool_to_call, params=final_params
        )

        return agent_gateway_pb2.AgentResponse(response_text=json.dumps(result))


def serve():
    """Starts the gRPC server with the auth interceptor."""
    # Add the interceptor when creating the server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), interceptors=[JwtAuthInterceptor()]
    )

    agent_gateway_pb2_grpc.add_AgentGatewayServicer_to_server(
        AgentGatewayServicer(), server
    )

    port = "8080"
    server.add_insecure_port(f"[::]:{port}")

    print(f"🔐 Agent Server with JWT Auth started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
