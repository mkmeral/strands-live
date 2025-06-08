import asyncio
import time

import pyaudio

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024  # Number of frames per buffer


def time_it(label, methodToRun):
    start_time = time.perf_counter()
    result = methodToRun()
    end_time = time.perf_counter()
    # Import debug_print to avoid circular imports
    from .bedrock_streamer import debug_print

    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


class AudioStreamer:
    """Handles continuous microphone input and audio output using separate streams."""

    def __init__(self, bedrock_stream_manager, agent=None):
        self.bedrock_stream_manager = bedrock_stream_manager
        self.agent = agent  # Reference to speech agent
        self.is_streaming = False
        self.loop = asyncio.get_event_loop()

        # Import debug_print to avoid circular imports
        from .bedrock_streamer import debug_print

        # Initialize PyAudio
        debug_print("AudioStreamer Initializing PyAudio...")
        self.p = time_it("AudioStreamerInitPyAudio", pyaudio.PyAudio)
        debug_print("AudioStreamer PyAudio initialized")

        # Initialize separate streams for input and output
        # Input stream with callback for microphone
        debug_print("Opening input audio stream...")
        self.input_stream = time_it(
            "AudioStreamerOpenAudio",
            lambda: self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=INPUT_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.input_callback,
            ),
        )
        debug_print("input audio stream opened")

        # Output stream for direct writing (no callback)
        debug_print("Opening output audio stream...")
        self.output_stream = time_it(
            "AudioStreamerOpenAudio",
            lambda: self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=OUTPUT_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
            ),
        )

        debug_print("output audio stream opened")

    def input_callback(self, in_data, frame_count, time_info, status):
        """Callback function that schedules audio processing in the asyncio event loop"""
        if self.is_streaming and in_data:
            # Schedule the task in the event loop
            asyncio.run_coroutine_threadsafe(
                self.process_input_audio(in_data), self.loop
            )
        return (None, pyaudio.paContinue)

    async def process_input_audio(self, audio_data):
        """Process a single audio chunk directly"""
        try:
            # Send audio to Bedrock immediately with agent identifiers
            if self.agent:
                self.bedrock_stream_manager.add_audio_chunk(
                    audio_data, self.agent.prompt_name, self.agent.audio_content_name
                )
            else:
                # Fallback for backward compatibility
                self.bedrock_stream_manager.add_audio_chunk(
                    audio_data, "default", "default"
                )
        except Exception as e:
            if self.is_streaming:
                print(f"Error processing input audio: {e}")

    async def play_output_audio(self):
        """Play audio responses from Nova Sonic"""
        while self.is_streaming:
            try:
                # Check for barge-in flag from agent
                if self.agent and self.agent.barge_in:
                    # Clear the audio queue
                    while not self.bedrock_stream_manager.audio_output_queue.empty():
                        try:
                            self.bedrock_stream_manager.audio_output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    self.agent.barge_in = False
                    # Small sleep after clearing
                    await asyncio.sleep(0.05)
                    continue

                # Get audio data from the stream manager's queue
                audio_data = await asyncio.wait_for(
                    self.bedrock_stream_manager.audio_output_queue.get(), timeout=0.1
                )

                if audio_data and self.is_streaming:
                    # Write directly to the output stream in smaller chunks
                    chunk_size = CHUNK_SIZE  # Use the same chunk size as the stream

                    # Write the audio data in chunks to avoid blocking too long
                    for i in range(0, len(audio_data), chunk_size):
                        if not self.is_streaming:
                            break

                        end = min(i + chunk_size, len(audio_data))
                        chunk = audio_data[i:end]

                        # Create a new function that captures the chunk by value
                        def write_chunk(data):
                            return self.output_stream.write(data)

                        # Pass the chunk to the function
                        await asyncio.get_event_loop().run_in_executor(
                            None, write_chunk, chunk
                        )

                        # Brief yield to allow other tasks to run
                        await asyncio.sleep(0.001)

            except asyncio.TimeoutError:
                # No data available within timeout, just continue
                continue
            except Exception as e:
                if self.is_streaming:
                    print(f"Error playing output audio: {str(e)}")
                    import traceback

                    traceback.print_exc()
                await asyncio.sleep(0.05)

    async def start_streaming(self):
        """Start streaming audio."""
        if self.is_streaming:
            return

        # Import time_it_async and debug_print to avoid circular imports
        from .bedrock_streamer import time_it_async

        print("Starting audio streaming. Speak into your microphone...")
        print("Press Enter to stop streaming...")

        # Send audio content start event
        if self.agent:
            await time_it_async(
                "send_audio_content_start_event",
                lambda: self.bedrock_stream_manager.send_audio_content_start_event(
                    self.agent.prompt_name, self.agent.audio_content_name
                ),
            )
        else:
            # Fallback for backward compatibility
            await time_it_async(
                "send_audio_content_start_event",
                lambda: self.bedrock_stream_manager.send_audio_content_start_event(
                    "default", "default"
                ),
            )

        self.is_streaming = True

        # Start the input stream if not already started
        if not self.input_stream.is_active():
            self.input_stream.start_stream()

        # Start processing tasks
        # self.input_task = asyncio.create_task(self.process_input_audio())
        self.output_task = asyncio.create_task(self.play_output_audio())

        # Wait for user to press Enter to stop
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Once input() returns, stop streaming
        await self.stop_streaming()

    async def stop_streaming(self):
        """Stop streaming audio."""
        if not self.is_streaming:
            return

        self.is_streaming = False

        # Cancel the tasks
        tasks = []
        if hasattr(self, "input_task") and not self.input_task.done():
            tasks.append(self.input_task)
        if hasattr(self, "output_task") and not self.output_task.done():
            tasks.append(self.output_task)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        # Stop and close the streams
        if self.input_stream:
            if self.input_stream.is_active():
                self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            if self.output_stream.is_active():
                self.output_stream.stop_stream()
            self.output_stream.close()
        if self.p:
            self.p.terminate()

        if self.agent:
            await self.bedrock_stream_manager.close(
                self.agent.prompt_name, self.agent.audio_content_name
            )
        else:
            await self.bedrock_stream_manager.close()
