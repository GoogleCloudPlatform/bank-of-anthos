import grpc
from concurrent import futures
import time

# Import the generated classes
import agent_gateway_pb2
import agent_gateway_pb2_grpc


class AgentGatewayServicer(agent_gateway_pb2_grpc.AgentGatewayServicer):
    """Implements the AgentGateway service."""

    def ProcessRequest(self, request, context):
        """Handles the ProcessRequest RPC."""
        print(
            f"Received request from user '{request.user_id}' with query: '{request.query_text}'"
        )

        # Simple placeholder logic for now
        response_message = f"Hello, {request.user_id}! The agent is processing your query: '{request.query_text}'"

        return agent_gateway_pb2.AgentResponse(response_text=response_message)


def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_gateway_pb2_grpc.add_AgentGatewayServicer_to_server(
        AgentGatewayServicer(), server
    )

    port = "8080"
    server.add_insecure_port(f"[::]:{port}")

    print(f"🚀 Server started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
