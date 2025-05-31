import asyncio
import base64
import datetime
import inspect
import json
import os
import time
import uuid

import websockets


def debug_print(message):
    """Print only if debug mode is enabled"""
    try:
        from .cli import DEBUG

        if DEBUG:
            functionName = inspect.stack()[1].function
            if functionName == "time_it" or functionName == "time_it_async":
                functionName = inspect.stack()[2].function
            print(
                f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S.%f}"[:-3]
                + " "
                + functionName
                + " "
                + message
            )
    except ImportError:
        functionName = inspect.stack()[1].function
        print(
            f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S.%f}"[:-3]
            + " "
            + functionName
            + " "
            + message
        )


def time_it(label, methodToRun):
    start_time = time.perf_counter()
    result = methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


async def time_it_async(label, methodToRun):
    start_time = time.perf_counter()
    result = await methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


class GeminiLiveStreamManager:
    """Manages bidirectional streaming with Gemini Live API using WebSockets"""

    def __init__(
        self, api_key=None, model_id="gemini-2.0-flash-live-001", tool_handler=None
    ):
        """Initialize the stream manager."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_id = model_id
        self.tool_handler = tool_handler

        # WebSocket connection
        self.websocket = None
        self.host = "generativelanguage.googleapis.com"
        self.ws_url = f"wss://{self.host}/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={self.api_key}"

        # Async queues for audio processing
        self.audio_input_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        # Task management
        self.response_task = None
        self.audio_input_task = None
        self.is_active = False
        self.barge_in = False

        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.turn_id = str(uuid.uuid4())
        self.toolUseContent = ""
        self.toolUseId = ""
        self.toolName = ""

        # Audio and text response settings
        self.audio_player = None
        self.display_assistant_text = False
        self.role = None

    def _get_tool_config(self):
        """Get tool configuration from tool handler"""
        if self.tool_handler:
            return self.tool_handler.get_gemini_tool_config()
        return []

    async def initialize_stream(self):
        """Initialize the bidirectional stream with Gemini Live API."""
        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.ws_url, additional_headers={"Content-Type": "application/json"}
            )
            self.is_active = True

            # Send initial setup message
            setup_message = {
                "setup": {
                    "model": f"models/{self.model_id}",
                    "generation_config": {
                        "response_modalities": ["AUDIO", "TEXT"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {"voice_name": "Aoede"}
                            }
                        },
                    },
                    "system_instruction": {
                        "parts": [
                            {
                                "text": "You are a helpful assistant. When reading order numbers, please read each digit individually, separated by pauses. For example, order #1234 should be read as 'order number one-two-three-four' rather than 'order number one thousand two hundred thirty-four'."
                            }
                        ]
                    },
                    "tools": self._get_tool_config(),
                }
            }

            await self.websocket.send(json.dumps(setup_message))

            # Wait for setup confirmation
            setup_response = await self.websocket.recv()
            setup_data = json.loads(setup_response)
            debug_print(f"Setup response: {setup_data}")

            # Start response processing task
            self.response_task = asyncio.create_task(self._process_responses())

            # Start audio input processing task
            self.audio_input_task = asyncio.create_task(self._process_audio_input())

            # Wait for setup completion
            await asyncio.sleep(0.1)

            debug_print("Gemini Live stream initialized successfully")
            return self

        except Exception as e:
            self.is_active = False
            print(f"Failed to initialize Gemini Live stream: {str(e)}")
            raise

    async def send_raw_message(self, message_dict):
        """Send a raw message dict to the Gemini Live API."""
        if not self.websocket or not self.is_active:
            debug_print("WebSocket not connected or stream closed")
            return

        try:
            message_json = json.dumps(message_dict)
            await self.websocket.send(message_json)
            debug_print(f"Sent message: {message_json}")
        except Exception as e:
            debug_print(f"Error sending message: {str(e)}")

    async def send_audio_content_start_event(self):
        """Send audio content start - handled automatically by Gemini Live"""
        debug_print("Audio content started (handled automatically by Gemini Live)")

    async def _process_audio_input(self):
        """Process audio input from the queue and send to Gemini Live."""
        while self.is_active:
            try:
                data = await self.audio_input_queue.get()

                audio_bytes = data.get("audio_bytes")
                if not audio_bytes:
                    debug_print("No audio bytes received")
                    continue

                # Base64 encode the audio data
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

                # Send audio message to Gemini Live with proper format
                message = {
                    "realtime_input": {
                        "media_chunks": [
                            {
                                "data": audio_b64,
                                "mime_type": "audio/pcm;rate=16000;channels=1",
                            }
                        ]
                    }
                }

                await self.send_raw_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                debug_print(f"Error processing audio: {e}")

    def add_audio_chunk(self, audio_bytes):
        """Add an audio chunk to the queue."""
        self.audio_input_queue.put_nowait(
            {"audio_bytes": audio_bytes, "session_id": self.session_id}
        )

    async def send_audio_content_end_event(self):
        """Send audio content end - handled automatically by Gemini Live"""
        debug_print("Audio content ended (handled automatically by Gemini Live)")

    async def send_text_message(self, text):
        """Send a text message to Gemini Live."""
        message = {
            "client_content": {
                "turn_complete": True,
                "turns": [{"role": "user", "parts": [{"text": text}]}],
            }
        }
        await self.send_raw_message(message)

    async def send_tool_result(self, tool_call_id, result):
        """Send tool result back to Gemini Live."""
        if isinstance(result, dict):
            result_json = json.dumps(result)
        else:
            result_json = str(result)

        message = {
            "client_content": {
                "turn_complete": True,
                "turns": [
                    {
                        "role": "function",
                        "parts": [
                            {
                                "function_response": {
                                    "name": self.toolName,
                                    "id": tool_call_id,
                                    "response": {"result": result_json},
                                }
                            }
                        ],
                    }
                ],
            }
        }
        await self.send_raw_message(message)

    async def _process_responses(self):
        """Process incoming responses from Gemini Live API."""
        try:
            while self.is_active:
                try:
                    raw_response = await self.websocket.recv()
                    response_data = json.loads(raw_response)

                    # Handle setup completion
                    if "setupComplete" in response_data:
                        debug_print("Setup completed successfully")
                        continue

                    # Handle server content
                    if "serverContent" in response_data:
                        server_content = response_data["serverContent"]

                        # Check for interruptions
                        if server_content.get("interrupted"):
                            debug_print("Response interrupted by user")
                            self.barge_in = True
                            # Clear audio output queue on interruption
                            while not self.audio_output_queue.empty():
                                try:
                                    self.audio_output_queue.get_nowait()
                                except asyncio.QueueEmpty:
                                    break

                        # Handle model turn responses
                        if "modelTurn" in server_content:
                            await self._handle_model_turn(server_content["modelTurn"])

                        # Handle turn completion
                        if server_content.get("turnComplete"):
                            debug_print("Turn completed")
                            self.barge_in = False

                    # Put response in output queue
                    await self.output_queue.put(response_data)

                except websockets.exceptions.ConnectionClosed:
                    debug_print("WebSocket connection closed")
                    break
                except Exception as e:
                    debug_print(f"Error receiving response: {e}")
                    break

        except Exception as e:
            print(f"Response processing error: {e}")
        finally:
            self.is_active = False

    async def _handle_model_turn(self, model_turn):
        """Handle model turn responses."""
        for part in model_turn.get("parts", []):
            # Handle text output
            if "text" in part:
                text_content = part["text"]
                if text_content.strip():
                    print(f"Assistant: {text_content}")

                    # Check for interruption
                    if "interrupted" in text_content.lower():
                        debug_print("Barge-in detected. Stopping audio output.")
                        self.barge_in = True

            # Handle audio output
            if "inlineData" in part:
                inline_data = part["inlineData"]
                if inline_data.get("mimeType") == "audio/pcm":
                    audio_content = inline_data["data"]
                    audio_bytes = base64.b64decode(audio_content)
                    await self.audio_output_queue.put(audio_bytes)

            # Handle function calls
            if "functionCall" in part:
                await self._handle_function_call(part["functionCall"])

    async def _handle_function_call(self, function_call):
        """Handle function calls."""
        self.toolName = function_call.get("name")
        self.toolUseId = function_call.get("id", str(uuid.uuid4()))
        args = function_call.get("args", {})

        debug_print(f"Tool use detected: {self.toolName}, ID: {self.toolUseId}")

        if self.tool_handler:
            try:
                tool_result = await self.tool_handler.process_tool_use(
                    self.toolName, {"name": self.toolName, "args": args}
                )
                await self.send_tool_result(self.toolUseId, tool_result)
            except Exception as e:
                debug_print(f"Error processing tool use: {e}")
                await self.send_tool_result(
                    self.toolUseId, {"error": f"Tool execution failed: {str(e)}"}
                )
        else:
            debug_print("No tool handler available")

    async def send_prompt_end_event(self):
        """End the current prompt/conversation."""
        debug_print("Prompt ended (handled automatically by Gemini Live)")

    async def send_session_end_event(self):
        """End the session."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        self.is_active = False
        debug_print("Session ended")

    async def close(self):
        """Close the stream properly."""
        if not self.is_active:
            return

        self.is_active = False

        # Cancel tasks
        if self.response_task and not self.response_task.done():
            self.response_task.cancel()

        if self.audio_input_task and not self.audio_input_task.done():
            self.audio_input_task.cancel()

        # Close WebSocket
        if self.websocket:
            await self.websocket.close()

        debug_print("Gemini Live stream closed")


class GeminiStreamManager(GeminiLiveStreamManager):
    """Compatibility wrapper to match BedrockStreamManager interface exactly"""

    def __init__(
        self, model_id="gemini-2.0-flash-live-001", region=None, tool_handler=None
    ):
        # Ignore region parameter for Gemini (kept for compatibility)
        api_key = os.getenv("GOOGLE_API_KEY")
        super().__init__(api_key=api_key, model_id=model_id, tool_handler=tool_handler)

        # Match BedrockStreamManager attributes
        self.prompt_name = self.session_id
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())

    # Compatibility methods to match BedrockStreamManager interface
    async def send_tool_start_event(self, content_name):
        """Compatibility method - Gemini handles this automatically"""
        debug_print(f"Tool start event (auto-handled): {content_name}")

    async def send_tool_result_event(self, content_name, tool_result):
        """Send tool result - compatibility wrapper"""
        await self.send_tool_result(self.toolUseId, tool_result)

    async def send_tool_content_end_event(self, content_name):
        """Compatibility method - Gemini handles this automatically"""
        debug_print(f"Tool content end event (auto-handled): {content_name}")
