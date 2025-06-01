import asyncio
import base64
import datetime
import inspect
import json
import time
import uuid

from aws_sdk_bedrock_runtime.client import (
    BedrockRuntimeClient,
    InvokeModelWithBidirectionalStreamOperationInput,
)
from aws_sdk_bedrock_runtime.config import (
    Config,
    HTTPAuthSchemeResolver,
    SigV4AuthScheme,
)
from aws_sdk_bedrock_runtime.models import (
    BidirectionalInputPayloadPart,
    InvokeModelWithBidirectionalStreamInputChunk,
)
from smithy_aws_core.credentials_resolvers.environment import (
    EnvironmentCredentialsResolver,
)

# Tool handling will be injected from outside


def debug_print(message):
    """Print only if debug mode is enabled"""
    # Import DEBUG from cli module to avoid circular imports
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


class BedrockStreamManager:
    """Manages bidirectional streaming with AWS Bedrock using asyncio"""

    # Event templates - simplified to keep only what's needed for transport
    AUDIO_EVENT_TEMPLATE = """{
        "event": {
            "audioInput": {
            "promptName": "%s",
            "contentName": "%s",
            "content": "%s"
            }
        }
    }"""

    TOOL_CONTENT_START_EVENT = """{
        "event": {
            "contentStart": {
                "promptName": "%s",
                "contentName": "%s",
                "interactive": false,
                "type": "TOOL",
                "role": "TOOL",
                "toolResultInputConfiguration": {
                    "toolUseId": "%s",
                    "type": "TEXT",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        }
    }"""

    CONTENT_END_EVENT = """{
        "event": {
            "contentEnd": {
            "promptName": "%s",
            "contentName": "%s"
            }
        }
    }"""

    PROMPT_END_EVENT = """{
        "event": {
            "promptEnd": {
            "promptName": "%s"
            }
        }
    }"""

    SESSION_END_EVENT = """{
        "event": {
            "sessionEnd": {}
        }
    }"""

    def tool_result_event(self, content_name, content, role, prompt_name):
        """Create a tool result event"""

        if isinstance(content, dict):
            content_json_string = json.dumps(content)
        else:
            content_json_string = content

        tool_result_event = {
            "event": {
                "toolResult": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "content": content_json_string,
                }
            }
        }
        return json.dumps(tool_result_event)

    def __init__(
        self, model_id="amazon.nova-sonic-v1:0", region="us-east-1", tool_handler=None, agent=None
    ):
        """Initialize the stream manager."""
        self.model_id = model_id
        self.region = region
        self.tool_handler = tool_handler  # Inject tool handler from outside
        self.agent = agent  # Reference to speech agent for callbacks

        # Replace RxPy subjects with asyncio queues
        self.audio_input_queue = asyncio.Queue()
        self.audio_output_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        self.response_task = None
        self.stream_response = None
        self.is_active = False
        self.bedrock_client = None

        # Audio playback components
        self.audio_player = None

    def _initialize_client(self):
        """Initialize the Bedrock client."""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
            http_auth_scheme_resolver=HTTPAuthSchemeResolver(),
            http_auth_schemes={"aws.auth#sigv4": SigV4AuthScheme()},
        )
        self.bedrock_client = BedrockRuntimeClient(config=config)

    async def initialize_stream(self):
        """Initialize the bidirectional stream with Bedrock."""
        if not self.bedrock_client:
            self._initialize_client()

        try:
            self.stream_response = await time_it_async(
                "invoke_model_with_bidirectional_stream",
                lambda: self.bedrock_client.invoke_model_with_bidirectional_stream(
                    InvokeModelWithBidirectionalStreamOperationInput(
                        model_id=self.model_id
                    )
                ),
            )
            self.is_active = True

            # Start listening for responses
            self.response_task = asyncio.create_task(self._process_responses())

            # Start processing audio input
            asyncio.create_task(self._process_audio_input())

            # Wait a bit to ensure everything is set up
            await asyncio.sleep(0.1)

            debug_print("Stream initialized successfully")
            return self
        except Exception as e:
            self.is_active = False
            print(f"Failed to initialize stream: {str(e)}")
            raise

    async def send_raw_event(self, event_json):
        """Send a raw event JSON to the Bedrock stream."""
        if not self.stream_response or not self.is_active:
            debug_print("Stream not initialized or closed")
            return

        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode("utf-8"))
        )

        try:
            await self.stream_response.input_stream.send(event)
            # For debugging large events, you might want to log just the type
            from .cli import DEBUG

            if DEBUG:
                if len(event_json) > 200:
                    event_type = json.loads(event_json).get("event", {}).keys()
                    debug_print(f"Sent event type: {list(event_type)}")
                else:
                    debug_print(f"Sent event: {event_json}")
        except Exception as e:
            debug_print(f"Error sending event: {str(e)}")
            from .cli import DEBUG

            if DEBUG:
                import traceback

                traceback.print_exc()

    async def send_audio_content_start_event(self, prompt_name, audio_content_name):
        """Send a content start event to the Bedrock stream."""
        content_start_event = f"""{{
            "event": {{
                "contentStart": {{
                "promptName": "{prompt_name}",
                "contentName": "{audio_content_name}",
                "type": "AUDIO",
                "interactive": true,
                "role": "USER",
                "audioInputConfiguration": {{
                    "mediaType": "audio/lpcm",
                    "sampleRateHertz": 16000,
                    "sampleSizeBits": 16,
                    "channelCount": 1,
                    "audioType": "SPEECH",
                    "encoding": "base64"
                    }}
                }}
            }}
        }}"""
        await self.send_raw_event(content_start_event)

    async def _process_audio_input(self):
        """Process audio input from the queue and send to Bedrock."""
        while self.is_active:
            try:
                # Get audio data from the queue
                data = await self.audio_input_queue.get()

                audio_bytes = data.get("audio_bytes")
                prompt_name = data.get("prompt_name")
                content_name = data.get("content_name")
                
                if not audio_bytes:
                    debug_print("No audio bytes received")
                    continue

                # Base64 encode the audio data
                blob = base64.b64encode(audio_bytes)
                audio_event = self.AUDIO_EVENT_TEMPLATE % (
                    prompt_name,
                    content_name,
                    blob.decode("utf-8"),
                )

                # Send the event
                await self.send_raw_event(audio_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                debug_print(f"Error processing audio: {e}")
                from .cli import DEBUG

                if DEBUG:
                    import traceback

                    traceback.print_exc()

    def add_audio_chunk(self, audio_bytes, prompt_name, content_name):
        """Add an audio chunk to the queue."""
        self.audio_input_queue.put_nowait(
            {
                "audio_bytes": audio_bytes,
                "prompt_name": prompt_name,
                "content_name": content_name,
            }
        )

    async def send_audio_content_end_event(self, prompt_name, audio_content_name):
        """Send a content end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        content_end_event = self.CONTENT_END_EVENT % (
            prompt_name,
            audio_content_name,
        )
        await self.send_raw_event(content_end_event)
        debug_print("Audio ended")

    async def send_tool_start_event(self, content_name, tool_use_id, prompt_name):
        """Send a tool content start event to the Bedrock stream."""
        content_start_event = self.TOOL_CONTENT_START_EVENT % (
            prompt_name,
            content_name,
            tool_use_id,
        )
        debug_print(f"Sending tool start event: {content_start_event}")
        await self.send_raw_event(content_start_event)

    async def send_tool_result_event(self, content_name, tool_result, prompt_name):
        """Send a tool content event to the Bedrock stream."""
        # Use the actual tool result from processToolUse
        tool_result_event = self.tool_result_event(
            content_name=content_name, content=tool_result, role="TOOL", prompt_name=prompt_name
        )
        debug_print(f"Sending tool result event: {tool_result_event}")
        await self.send_raw_event(tool_result_event)

    async def send_tool_content_end_event(self, content_name, prompt_name):
        """Send a tool content end event to the Bedrock stream."""
        tool_content_end_event = self.CONTENT_END_EVENT % (
            prompt_name,
            content_name,
        )
        debug_print(f"Sending tool content event: {tool_content_end_event}")
        await self.send_raw_event(tool_content_end_event)

    async def send_prompt_end_event(self, prompt_name):
        """Close the stream and clean up resources."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        prompt_end_event = self.PROMPT_END_EVENT % (prompt_name)
        await self.send_raw_event(prompt_end_event)
        debug_print("Prompt ended")

    async def send_session_end_event(self):
        """Send a session end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        await self.send_raw_event(self.SESSION_END_EVENT)
        self.is_active = False
        debug_print("Session ended")

    async def _process_responses(self):
        """Process incoming responses from Bedrock."""
        try:
            while self.is_active:
                try:
                    output = await self.stream_response.await_output()
                    result = await output[1].receive()
                    if result.value and result.value.bytes_:
                        try:
                            response_data = result.value.bytes_.decode("utf-8")
                            json_data = json.loads(response_data)

                            # Delegate event handling to the agent
                            if self.agent:
                                await self.agent.handle_response_event(json_data)

                            # Put the response in the output queue for other components
                            await self.output_queue.put(json_data)
                        except json.JSONDecodeError:
                            await self.output_queue.put({"raw_data": response_data})
                except StopAsyncIteration:
                    # Stream has ended
                    break
                except Exception as e:
                    # Handle ValidationException properly
                    if "ValidationException" in str(e):
                        error_message = str(e)
                        print(f"Validation error: {error_message}")
                    else:
                        print(f"Error receiving response: {e}")
                    break

        except Exception as e:
            print(f"Response processing error: {e}")
        finally:
            self.is_active = False

    async def close(self, prompt_name=None, audio_content_name=None):
        """Close the stream properly."""
        if not self.is_active:
            return

        self.is_active = False
        if self.response_task and not self.response_task.done():
            self.response_task.cancel()

        if prompt_name and audio_content_name:
            await self.send_audio_content_end_event(prompt_name, audio_content_name)
            await self.send_prompt_end_event(prompt_name)
        
        await self.send_session_end_event()

        if self.stream_response:
            await self.stream_response.input_stream.close()
