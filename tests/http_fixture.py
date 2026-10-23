#!/usr/bin/env python3
"""Request-validating HTTP fixture; its parent Sky test owns its lifetime."""

import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

MESSAGES = [
    {"role": "system", "content": "Be precise."},
    {"role": "user", "content": "Weather in Berlin?"},
]
TOOLS = [
    {
        "type": "function",
        "name": "weather",
        "description": "Return current weather.",
        "parameters": {"type": "object"},
        "strict": False,
    }
]


class ResponsesFixture(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def reply(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_CONNECT(self):
        self.reply(502, "External network is disabled in tests.")

    def do_POST(self):
        route, _, outcome = self.path.removeprefix("/").partition("/")
        try:
            if route not in ("chat", "tools") or outcome not in (
                "",
                "loop",
                "http-error",
                "malformed",
                "disconnect",
            ):
                raise ValueError("unexpected endpoint")
            if self.headers.get("Authorization") != "Bearer sky-openai-test-key":
                raise ValueError("incorrect bearer authorization")
            if self.headers.get("Content-Type") != "application/json":
                raise ValueError("incorrect content type")
            payload = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
            )
            continued = (
                route == "tools"
                and outcome == "loop"
                and "previous_response_id" in payload
            )
            expected = {
                "model": "fixture-model",
                "input": MESSAGES,
                "reasoning": {"effort": "high"},
            }
            if route == "tools":
                expected["tools"] = TOOLS
            if continued:
                expected["previous_response_id"] = "resp_http_tool"
                expected["input"] = [
                    {
                        "type": "function_call_output",
                        "call_id": "call_weather",
                        "output": "18 C",
                    }
                ]
            if payload != expected:
                raise ValueError("incorrect request payload")
        except (ValueError, TypeError) as error:
            self.reply(422, str(error))
            return

        if outcome == "http-error":
            self.reply(429, '{"error":{"message":"fixture rate limit"}}')
        elif outcome == "malformed":
            self.reply(200, "{")
        elif outcome == "disconnect":
            self.close_connection = True
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
        else:
            text = "Hello there" if route == "chat" else "Checking weather."
            if continued:
                text = "It is 18 C."
            output = [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": text}],
                }
            ]
            if route == "tools" and not continued:
                output.append(
                    {
                        "type": "function_call",
                        "id": "fc_http",
                        "call_id": "call_weather",
                        "name": "weather",
                        "arguments": '{"city":"Berlin"}',
                    }
                )
            self.reply(
                201 if route == "chat" else 200,
                json.dumps(
                    {
                        "id": "resp_http_tool",
                        "output": output,
                        "usage": {
                            "input_tokens": 12,
                            "output_tokens": 3,
                            "total_tokens": 15,
                        },
                    }
                ),
            )


def main():
    with ThreadingHTTPServer(("127.0.0.1", 0), ResponsesFixture) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        try:
            # Exit on parent EOF as well as on Process.close's termination signal.
            sys.stdin.read()
        finally:
            server.shutdown()
            worker.join()


if __name__ == "__main__":
    main()
