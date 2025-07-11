import time
import grpc
from concurrent import futures
import generated.service_pb2 as service_pb2
import generated.service_pb2_grpc as service_pb2_grpc

class GreeterServicer(service_pb2_grpc.GreeterServicer):
    """Provides methods that implement functionality of greeter server."""

    def __init__(self):
        self.counter = 0

    def SayHello(self, request, context):
        """Implementation of the SayHello RPC method."""
        self.counter += 1
        return service_pb2.HelloReply(
            message=f"Hello, {request.name}!", 
            greeting_count=self.counter
        )
    
    def SayHelloStream(self, request, context):
        """Implementation of the SayHelloStream RPC method."""
        for i in range(5):
            self.counter += 1
            yield service_pb2.HelloReply(
                message=f"Hello {i+1}, {request.name}!", 
                greeting_count=self.counter
            )
            time.sleep(1)  # Simulate processing time


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("Server stopped")


if __name__ == '__main__':
    serve()