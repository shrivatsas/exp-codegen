// File: src/main/kotlin/com/example/grpc/GreeterClient.kt
package com.example.grpc

import com.example.grpc.proto.GreeterGrpcKt
import com.example.grpc.proto.HelloRequest
import io.grpc.ManagedChannelBuilder
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.runBlocking
import java.io.Closeable
import java.util.concurrent.TimeUnit
import kotlin.system.exitProcess

class GreeterClient(private val channel: io.grpc.ManagedChannel) : Closeable {
    private val stub = GreeterGrpcKt.GreeterCoroutineStub(channel)

    suspend fun greet(name: String) {
        // Unary call
        val request = HelloRequest.newBuilder().setName(name).build()
        val response = stub.sayHello(request)
        println("Greeter client received: ${response.message} (Count: ${response.greetingCount})")
    }

    suspend fun greetStream(name: String) {
        println("\nStreaming responses:")
        val request = HelloRequest.newBuilder().setName(name).build()
        
        // Server streaming call
        stub.sayHelloStream(request).collect { response ->
            println("Greeter client received stream: ${response.message} (Count: ${response.greetingCount})")
        }
    }

    override fun close() {
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS)
    }
}

fun main() = runBlocking {
    val port = 50051
    val channel = ManagedChannelBuilder.forAddress("localhost", port)
        .usePlaintext()
        .build()
    
    val client = GreeterClient(channel)
    
    try {
        client.greet("World from Kotlin")
        client.greetStream("Streaming World from Kotlin")
    } catch (e: Exception) {
        println("Error: ${e.message}")
        e.printStackTrace()
        exitProcess(1)
    } finally {
        client.close()
    }
}