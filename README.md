# Nova Sonic Speech Agent

A refactored speech agent using Amazon Nova Sonic for real-time bidirectional audio streaming with tool integration.

## Project Structure

```
├── src/
│   ├── __init__.py           # Package initialization
│   ├── speech_agent.py       # SpeechAgent - High-level orchestrator
│   ├── tool_handler.py       # ToolHandler - Tool processing logic
│   ├── bedrock_streamer.py   # BedrockStreamManager - AWS Bedrock streaming
│   ├── audio_streamer.py     # AudioStreamer - Audio I/O management
│   └── cli.py                # CLI interface and application entry
├── tests/
│   ├── __init__.py
│   ├── test_speech_agent.py  # Unit tests for SpeechAgent
│   ├── test_tool_handler.py  # Unit tests for ToolHandler
│   ├── test_bedrock_streamer.py # Unit tests for BedrockStreamManager
│   ├── test_audio_streamer.py   # Unit tests for AudioStreamer
│   └── test_cli.py           # Unit tests for CLI
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Architecture

The application follows a layered architecture with clear separation of concerns:

### SpeechAgent (`src/speech_agent.py`) - **High-Level Orchestrator**
- **Primary interface** for the speech agent functionality
- Coordinates between audio streaming and Bedrock communication
- Manages conversation lifecycle (start, stop, error handling)
- Encapsulates AudioStreamer and BedrockStreamManager
- Provides unified API for external usage

### ToolHandler (`src/tool_handler.py`) - **Tool Processing**
- Isolated business logic for tool execution
- Implements date/time and order tracking tools
- Provides deterministic fake data for demonstration
- Easy to extend with new tools
- Clean async interface for tool processing

### BedrockStreamManager (`src/bedrock_streamer.py`) - **AWS Bedrock Integration**
- Manages bidirectional streaming with AWS Bedrock Nova Sonic
- Handles event serialization and stream lifecycle
- Processes responses and coordinates with injected tool handler
- Dependency injection for tool handling (loose coupling)

### AudioStreamer (`src/audio_streamer.py`) - **Audio I/O Management**
- Handles continuous microphone input and audio output
- Uses PyAudio for real-time audio streaming
- Manages barge-in detection and audio playback
- Separate from business logic concerns

### CLI (`src/cli.py`) - **Application Interface**
- Command-line interface with debug mode support
- Application bootstrapping and configuration
- Argument parsing and environment setup

## Key Design Principles

✅ **Single Responsibility**: Each class has one clear purpose  
✅ **Dependency Injection**: Components are loosely coupled  
✅ **High-Level Orchestration**: SpeechAgent coordinates everything  
✅ **Testability**: Each component is independently testable  
✅ **Extensibility**: Easy to add new tools or modify components  

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up AWS credentials (environment variables or AWS CLI):
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Usage

### Run the application:
```bash
python main.py
```

### Enable debug mode:
```bash
python main.py --debug
```

### Run tests:
```bash
pytest tests/ -v
```

### Programmatic Usage:
```python
from src import SpeechAgent

# Create and initialize speech agent
agent = SpeechAgent(model_id='amazon.nova-sonic-v1:0', region='us-east-1')
await agent.initialize()

# Start conversation
await agent.start_conversation()
```

## Features

- **Real-time Audio**: Bidirectional streaming with Nova Sonic
- **Tool Integration**: Built-in date/time and order tracking tools
- **Barge-in Support**: Interrupt assistant speech with user input
- **Debug Mode**: Detailed logging for troubleshooting
- **Clean Architecture**: High-level orchestration with modular components
- **Async/Await**: Modern Python asynchronous programming
- **Comprehensive Testing**: Unit tests for all components

## Available Tools

1. **getDateAndTimeTool**: Returns current date and time in PST
2. **trackOrderTool**: Simulates order tracking with deterministic fake data

## Requirements

- Python 3.8+
- AWS account with Bedrock access
- Microphone and speakers for audio interaction
- PyAudio system dependencies (may require additional setup on some systems)

## Development

The code is structured for easy extension:

- **Add new tools**: Extend `ToolHandler.process_tool_use()`
- **Modify audio settings**: Update constants in `audio_streamer.py`
- **Extend Bedrock events**: Modify `BedrockStreamManager` event handling
- **Add CLI options**: Update argument parser in `cli.py`
- **Replace components**: Thanks to dependency injection, components are swappable

## Testing

Run the comprehensive test suite:
```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_speech_agent.py -v
pytest tests/test_tool_handler.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Architecture Benefits

1. **Maintainability**: Changes to one component don't affect others
2. **Testability**: Each component can be tested in isolation
3. **Extensibility**: Easy to add new features or replace components
4. **Readability**: Clear separation makes code easier to understand
5. **Reusability**: Components can be used independently or in other projects