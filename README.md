# Strands Live 🎤

A live speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming with Strands Agents SDK integration.

## Features

- **Real-time Audio Streaming**: Bidirectional audio communication with Amazon Nova Sonic
- **Tool Integration**: Powered by Strands Agents SDK with 50+ built-in tools
- **Extensible**: Easy to add custom tools and capabilities
- **Voice Activity Detection**: Smart audio processing with barge-in support
- **Cross-platform**: Works on macOS, Linux, and Windows

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/murmeral/strands-live.git
cd strands-live
make install

# Or install as CLI
make install-cli
```

### Usage

```bash
# Run directly
python strands_live_main.py

# Or use CLI after install-cli
strands-live --help
```

### Configuration

Set up your AWS credentials and configure the region:

```bash
export AWS_REGION=us-west-2  # or your preferred region
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

## Project Structure

```
strands-live/
├── src/strands_live/           # Main package source
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Command-line interface
│   ├── speech_agent.py        # Main SpeechAgent orchestrator
│   ├── audio_streamer.py      # Audio input/output management
│   ├── bedrock_streamer.py    # Nova Sonic streaming handler
│   ├── tool_handler_base.py   # Base tool handler interface
│   ├── tool_handler.py        # Basic tool handler implementation
│   └── strands_tool_handler.py # Strands SDK integration
├── tests/                     # Test suite
│   ├── test_speech_agent.py
│   ├── test_audio_streamer.py
│   ├── test_bedrock_streamer.py
│   └── test_tool_handlers.py
├── pyproject.toml             # Project configuration
├── Makefile                   # Build automation
├── README.md                  # This file
└── requirements.txt           # Dependencies
```

## Architecture

### Core Components

#### 1. SpeechAgent (`speech_agent.py`)
- **Role**: High-level orchestrator for the entire speech processing pipeline
- **Responsibilities**:
  - Coordinates audio streaming and Bedrock communication
  - Manages component lifecycle (initialize, start, stop)
  - Handles error recovery and cleanup
- **Key Methods**:
  - `initialize()`: Sets up streaming connections
  - `start_conversation()`: Begins real-time audio processing
  - `stop_conversation()`: Cleanly shuts down resources

#### 2. BedrockStreamManager (`bedrock_streamer.py`)
- **Role**: Manages bidirectional streaming with Amazon Nova Sonic
- **Responsibilities**:
  - Establishes WebSocket-like streaming connections
  - Handles audio encoding/decoding (PCM 16kHz)
  - Processes tool use requests from the model
  - Manages conversation state and context
- **Key Features**:
  - Asynchronous streaming with proper backpressure handling
  - Tool integration with response streaming
  - Error recovery and reconnection logic
  - Performance timing and metrics

#### 3. AudioStreamer (`audio_streamer.py`)
- **Role**: Real-time audio capture and playback
- **Responsibilities**:
  - Captures microphone input using PyAudio
  - Plays back synthesized speech
  - Handles audio format conversion
  - Manages audio device configuration
- **Technical Details**:
  - 16kHz PCM mono audio processing
  - Configurable buffer sizes for latency optimization
  - Cross-platform audio device detection
  - Real-time audio processing with minimal latency

#### 4. Tool Handler System
Three-tier tool handling architecture:

##### ToolHandlerBase (`tool_handler_base.py`)
- Abstract base class defining the tool handler interface
- Standardized method signatures for tool processing
- Error handling patterns and response formatting

##### ToolHandler (`tool_handler.py`)
- Basic implementation with essential tools
- Mathematical calculations, time utilities
- Lightweight and minimal dependencies

##### StrandsToolHandler (`strands_tool_handler.py`)
- Full Strands SDK integration
- Access to 50+ powerful tools (file operations, web requests, AWS services, etc.)
- Extensible plugin architecture
- Hot-reloadable custom tools

### Data Flow

```
Microphone → AudioStreamer → BedrockStreamManager → Nova Sonic Model
     ↑                                                      ↓
Speaker ← AudioStreamer ← BedrockStreamManager ← Tool Responses
                                ↓
                         ToolHandler System
                              ↓
                    External APIs/Services
```

### Technical Implementation Details

#### Audio Processing Pipeline
1. **Capture**: PyAudio captures 16kHz PCM audio from microphone
2. **Buffering**: Audio chunks are buffered for streaming efficiency
3. **Encoding**: Raw PCM data is sent to Nova Sonic via streaming API
4. **Response**: Model generates both audio and potential tool calls
5. **Playback**: Synthesized audio is played through speakers
6. **Tool Execution**: Tool calls are processed asynchronously

#### Streaming Architecture
- **Bidirectional Streaming**: Uses Amazon Bedrock's real-time streaming API
- **Backpressure Handling**: Prevents buffer overflow during high-throughput scenarios
- **Error Recovery**: Automatic reconnection and state restoration
- **Performance Monitoring**: Built-in timing and metrics collection

#### Tool Integration
- **Modular Design**: Tools are loaded dynamically based on configuration
- **Async Processing**: Tool execution doesn't block audio streaming
- **Error Isolation**: Tool failures don't crash the main conversation flow
- **Response Streaming**: Tool results are streamed back to the user in real-time

## Configuration Options

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-west-2                    # AWS region for Bedrock
AWS_ACCESS_KEY_ID=your_access_key       # AWS access key
AWS_SECRET_ACCESS_KEY=your_secret_key   # AWS secret key

# Model Configuration
BEDROCK_MODEL_ID=amazon.nova-sonic-v1:0 # Nova Sonic model version
BEDROCK_REGION=us-west-2                # Bedrock service region

# Audio Configuration
AUDIO_SAMPLE_RATE=16000                 # Audio sample rate (Hz)
AUDIO_CHANNELS=1                        # Audio channels (mono)
AUDIO_CHUNK_SIZE=1024                   # Audio buffer size
```

### Runtime Configuration

```python
# Initialize with custom configuration
speech_agent = SpeechAgent(
    model_id="amazon.nova-sonic-v1:0",
    region="us-west-2",
    tool_handler=StrandsToolHandler()  # or ToolHandler() for basic tools
)
```

## Performance Characteristics

### Latency Metrics
- **Audio Latency**: ~100-200ms round-trip (microphone to speaker)
- **Tool Processing**: Variable based on tool complexity (50ms-5s)
- **Model Response**: ~200-500ms for speech generation
- **Total Conversation Latency**: ~300-700ms typical

### Resource Usage
- **Memory**: ~100-300MB depending on tool configuration
- **CPU**: ~10-30% on modern systems during active conversation
- **Network**: ~50-200 KB/s during streaming
- **Audio**: Real-time processing with minimal buffering

## Development

### Setup Development Environment

```bash
# Clone and install development dependencies
git clone https://github.com/murmeral/strands-live.git
cd strands-live
make install

# Install additional development tools
pip install pytest black ruff mypy
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_speech_agent.py -v

# Run with coverage
pytest --cov=strands_live tests/
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
mypy src/strands_live/
```

### Building and Distribution

```bash
# Build package
make build

# Install locally
make install-cli

# Clean build artifacts
make clean
```

## Extending the System

### Adding Custom Tools

1. **Create Tool Handler**:
```python
from strands_live.tool_handler_base import ToolHandlerBase

class CustomToolHandler(ToolHandlerBase):
    async def process_tool_use(self, tool_name, tool_use_content):
        if tool_name == "my_custom_tool":
            # Your tool implementation
            return {"result": "custom response"}
        return await super().process_tool_use(tool_name, tool_use_content)
```

2. **Register with SpeechAgent**:
```python
speech_agent = SpeechAgent(tool_handler=CustomToolHandler())
```

### Integrating External Services

The tool handler system makes it easy to integrate external APIs and services:

```python
async def process_tool_use(self, tool_name, tool_use_content):
    if tool_name == "weather_api":
        # Call external weather service
        weather_data = await fetch_weather_data(tool_use_content["location"])
        return {"weather": weather_data}
```

## Troubleshooting

### Common Issues

1. **Audio Device Issues**:
   - Check microphone permissions
   - Verify audio device availability
   - Test with `python -c "import pyaudio; print('PyAudio working')"`

2. **AWS Credentials**:
   - Ensure AWS credentials are properly configured
   - Check IAM permissions for Bedrock access
   - Verify region availability for Nova Sonic

3. **Streaming Issues**:
   - Check network connectivity
   - Monitor for firewall blocking
   - Verify Bedrock service availability

### Debug Mode

```bash
# Run with debug logging
strands-live --debug

# Check logs
tail -f /tmp/strands-live.log
```

## Requirements

### System Requirements
- **Python**: 3.10+ (3.11+ recommended)
- **Memory**: 1GB+ available RAM
- **Network**: Stable internet connection for streaming
- **Audio**: Microphone and speakers/headphones

### Dependencies
- **Core**: `strands-agents>=0.1.0`, `strands-agents-tools>=0.1.0`
- **Audio**: `pyaudio>=0.2.11`
- **AWS**: `boto3>=1.26.0`, `botocore>=1.29.0`
- **Utilities**: `pytz>=2023.3`

## API Reference

### SpeechAgent

```python
class SpeechAgent:
    def __init__(self, model_id: str, region: str, tool_handler: Optional[ToolHandlerBase] = None)
    async def initialize(self) -> None
    async def start_conversation(self) -> None
    async def stop_conversation(self) -> None
```

### ToolHandlerBase

```python
class ToolHandlerBase:
    async def process_tool_use(self, tool_name: str, tool_use_content: dict) -> dict
    def get_available_tools(self) -> List[str]
```

## License

Apache License 2.0

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and formatting (`make test format`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for API changes
- Use type hints for better code clarity
- Keep functions focused and modular

## Roadmap

- [ ] Support for additional language models
- [ ] Multi-language conversation support
- [ ] Voice customization options
- [ ] Advanced audio processing features
- [ ] Mobile platform support
- [ ] Cloud deployment configurations