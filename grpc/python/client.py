import grpc
import generated.service_pb2 as service_pb2
import generated.service_pb2_grpc as service_pb2_grpc


def run():
    """Run the gRPC client."""
    # Create a channel to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = service_pb2_grpc.GreeterStub(channel)
        
        # Call the SayHello RPC
        response = stub.SayHello(service_pb2.HelloRequest(name='World'))
        print(f"Greeter client received: {response.message} (Count: {response.greeting_count})")
        
        # Call the SayHelloStream RPC
        print("\nStreaming responses:")
        for response in stub.SayHelloStream(service_pb2.HelloRequest(name='Streaming World')):
            print(f"Greeter client received stream: {response.message} (Count: {response.greeting_count})")


if __name__ == '__main__':
    run()
