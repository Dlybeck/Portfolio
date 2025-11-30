import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx
import time
import threading
import pytest
from services.code_server_proxy import CodeServerProxy

# Mock Upstream Server (simulates VS Code)
mock_app = FastAPI()

@mock_app.get("/{path:path}")
async def mock_upstream(path: str):
    async def slow_stream():
        yield b"start"
        for i in range(5):
            await asyncio.sleep(0.1) # Simulate network delay
            yield f"-chunk{i}".encode()
        yield b"-end"
    
    return StreamingResponse(slow_stream(), media_type="text/plain")

# Helper to run mock server
class MockServer(threading.Thread):
    def __init__(self, port=9999):
        super().__init__()
        self.port = port
        self.should_stop = False
        self.server = None

    def run(self):
        config = uvicorn.Config(mock_app, host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True
        self.join()

# The Test
@pytest.mark.asyncio
async def test_proxy_streaming_behavior():
    # 1. Start Mock Upstream
    upstream = MockServer(port=9999)
    upstream.start()
    # Wait for server to start
    await asyncio.sleep(1) 

    try:
        # 2. Initialize Proxy (pointing to mock upstream)
        # Force local mode to avoid SOCKS5 for this unit test
        import os
        os.environ["K_SERVICE"] = "test" # Trick it to think it's cloud run? No, we want local for test.
        # Actually, let's inject the URL directly.
        proxy = CodeServerProxy(code_server_url="http://127.0.0.1:9999")
        
        # Hack to force no proxy for localhost test even if IS_CLOUD_RUN logic triggers
        # We need to mock the `IS_CLOUD_RUN` behavior or just override the client
        # The current implementation of `get_session` uses global SOCKS5_PROXY if IS_CLOUD_RUN is true.
        # We need to make sure the test runs in a way that exercises the StreamingResponse logic.
        
        # Create a mock request
        # Starlette/FastAPI Request.client property expects (host, port) in the 'client' key of scope
        async def mock_receive():
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'headers': [[b'host', b'localhost']],
            'query_string': b'',
            'client': ('127.0.0.1', 12345) 
        }
        request = Request(scope, receive=mock_receive)

        print("\n--- Starting Proxy Request ---")
        start_time = time.time()
        
        # Execute Proxy Request
        response = await proxy.proxy_request(request, "test")
        
        # Check TTFB (Time To First Byte)
        # We iterate the response. The first chunk should come immediately ("start")
        # even though the rest takes 0.5s
        
        first_chunk = True
        async for chunk in response.body_iterator:
            if first_chunk:
                ttfb = time.time() - start_time
                print(f"Time to First Byte: {ttfb:.4f}s")
                first_chunk = False
                assert chunk == b"start", f"Unexpected first chunk: {chunk}"
                # If buffering, TTFB would be > 0.5s. If streaming, it should be < 0.1s
                assert ttfb < 0.2, "Proxy is BUFFERING! TTFB is too high."
            else:
                print(f"Received chunk: {chunk}")

        total_time = time.time() - start_time
        print(f"Total Time: {total_time:.4f}s")
        
        # Cleanup
        await proxy.close()

    finally:
        upstream.stop()

if __name__ == "__main__":
    # Simple run wrapper for manual execution
    asyncio.run(test_proxy_streaming_behavior())
