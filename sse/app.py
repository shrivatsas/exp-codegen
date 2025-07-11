import asyncio
from quart import Quart, Response, websocket
import time

app = Quart(__name__)

@app.websocket('/ws')
async def ws():
    count = 0
    while True:
        count += 1
        await websocket.send(f"WebSocket Event {count} at {time.time()}")
        await asyncio.sleep(1)

async def sse_stream():
    count = 0
    while True:
        count += 1
        yield f"data: Event {count} at {time.time()}\n\n"
        await asyncio.sleep(1)

@app.route('/events')
async def sse():
    return Response(sse_stream(), content_type='text/event-stream')

@app.route('/')
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SSE Test</title>
    </head>
    <body>
        <h1>Server-Sent Events and WebSocket Test</h1>
        <h2>Server-Sent Events</h1>
        <div id="events"></div>
        <h2>WebSocket Events</h2>
        <div id="ws-events"></div>
        <script>
            // SSE
            const eventSource = new EventSource('/events');
            eventSource.onmessage = function(event) {
                const eventsDiv = document.getElementById('events');
                eventsDiv.innerHTML += event.data + '<br>';
            };

            // WebSocket
            const socket = new WebSocket('ws://' + location.host + '/ws');
            socket.onmessage = function(event) {
                const eventsDiv = document.getElementById('ws-events');
                eventsDiv.innerHTML += event.data + '<br>';
            };
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run()
