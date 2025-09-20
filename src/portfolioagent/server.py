# src/portfolioagent/server.py

import grpc
from concurrent import futures
import time
import json
import importlib

import agent_gateway_pb2
import agent_gateway_pb2_grpc

# --- Tool-Calling Infrastructure ---


def load_tool_registry():
    """Loads the tool registry from the JSON file."""
    with open("tools.json", "r") as f:
        return json.load(f)


TOOL_REGISTRY = load_tool_registry()


def execute_tool(tool_name: str, params: dict):
    """
    Executes a tool with retries and a timeout.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"Tool '{tool_name}' not found."}

    tool_info = TOOL_REGISTRY[tool_name]
    max_retries = 2
    timeout_seconds = 5  # Timeout for a single attempt

    for attempt in range(max_retries):
        try:
            module = importlib.import_module(tool_info["module"])
            tool_callable = getattr(module, tool_info["callable"])

            # Here we can use a more robust way to handle timeouts in production
            # For simplicity, we are assuming tools are well-behaved.
            result = tool_callable(**params)

            if result.get("status") == "error":
                raise Exception(result.get("message", "Tool execution failed"))

            return result

        except Exception as e:
            print(f"Attempt {attempt + 1} for tool '{tool_name}' failed: {e}")
            if attempt + 1 == max_retries:
                return {
                    "status": "error",
                    "message": f"Tool '{tool_name}' failed after {max_retries} attempts.",
                }
            time.sleep(1)  # Wait before retrying


# --- gRPC Service Implementation ---


class AgentGatewayServicer(agent_gateway_pb2_grpc.AgentGatewayServicer):
    """Implements the AgentGateway service."""

    def ProcessRequest(self, request, context):
        """Handles the ProcessRequest RPC with tool-calling logic."""
        print(
            f"Received request from user '{request.user_id}' with query: '{request.query_text}'"
        )

        tool_to_call = request.query_text.strip()

        # --- START OF FIX ---

        if tool_to_call not in TOOL_REGISTRY:
            error_result = {
                "status": "error",
                "message": f"Tool '{tool_to_call}' not found.",
            }
            return agent_gateway_pb2.AgentResponse(
                response_text=json.dumps(error_result)
            )

        # 1. Define all available data the agent has access to.
        available_data = {
            "user_id": request.user_id,
            "portfolio_assets": ["GOOG", "TSLA"],  # Dummy data for now
        }

        # 2. Get the list of required parameters for the specific tool from the registry.
        required_params = TOOL_REGISTRY[tool_to_call].get("parameters", [])

        # 3. Build the final parameters dictionary, only including the required keys.
        final_params = {
            key: available_data[key] for key in required_params if key in available_data
        }

        # --- END OF FIX ---

        result = execute_tool(tool_name=tool_to_call, params=final_params)

        return agent_gateway_pb2.AgentResponse(response_text=json.dumps(result))


def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_gateway_pb2_grpc.add_AgentGatewayServicer_to_server(
        AgentGatewayServicer(), server
    )

    port = "8080"
    server.add_insecure_port(f"[::]:{port}")

    print(f"🚀 Agent Server with Tool-Calling capabilities started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
