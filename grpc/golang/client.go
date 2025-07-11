package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	pb "github.com/shrivatsas/exp-codegen/grpc/protos"
)

func main() {
	// Set up a connection to the server
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	// Create a client
	client := pb.NewGreeterClient(conn)

	// Contact the server and print out its response
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	// Call SayHello RPC
	resp, err := client.SayHello(ctx, &pb.HelloRequest{Name: "World from Go"})
	if err != nil {
		log.Fatalf("Could not greet: %v", err)
	}
	fmt.Printf("Greeter client received: %s (Count: %d)\n", resp.Message, resp.GreetingCount)

	// Call SayHelloStream RPC
	fmt.Println("\nStreaming responses:")
	streamCtx, streamCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer streamCancel()
	
	stream, err := client.SayHelloStream(streamCtx, &pb.HelloRequest{Name: "Streaming World from Go"})
	if err != nil {
		log.Fatalf("Could not greet with stream: %v", err)
	}
	
	for {
		streamResp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("Failed to receive stream: %v", err)
		}
		fmt.Printf("Greeter client received stream: %s (Count: %d)\n", 
			streamResp.Message, streamResp.GreetingCount)
	}
}