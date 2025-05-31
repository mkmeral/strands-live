# 🎙️ Speech-Based AI Agents with Strands Integration

A **high-performance, real-time speech-based AI agent system** that seamlessly integrates with **Amazon Bedrock**, **Nova Sonic**, and the **Strands Agents SDK**. This system enables natural voice conversations with AI agents that can execute tools, manage state, and provide intelligent responses through advanced speech processing.

## 🚀 Key Features

### **🔊 Advanced Speech Processing**
- **Real-time audio streaming** with AWS Nova Sonic
- **High-quality voice synthesis** and recognition
- **Low-latency conversation flow** for natural interactions
- **Configurable audio parameters** (sample rate, channels, etc.)

### **🤖 Intelligent Agent System**
- **Strands Agents SDK integration** for advanced tool capabilities
- **Extensible tool ecosystem** with hot-reloading capabilities
- **Advanced conversation management** with context preservation
- **Error handling and recovery** for robust operation

### **🛠️ Enhanced Tool Management**
- **Centralized tool configuration** at application level
- **Dynamic tool loading** and management
- **Dependency injection** for better testability
- **Built-in tools**: `current_time` and `calculator` by default

### **☁️ AWS Integration**
- **Amazon Bedrock** for LLM interactions
- **Nova Sonic** for speech processing
- **IAM-based authentication** and security
- **Multi-region support** and configuration

## 📦 Project Structure

```
speech-based-agents/
├── main.py                    # CLI entry point
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── src/                       # Source code
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface & tool configuration
│   ├── speech_agent.py        # Main agent orchestrator
│   ├── audio_streamer.py      # Audio processing
│   ├── bedrock_streamer.py    # AWS Bedrock integration
│   ├── strands_tool_handler.py # Strands SDK integration
│   ├── tool_handler.py        # Original tool handler (legacy)
│   └── tool_handler_base.py   # Base tool handler class
└── tests/                     # Test suite
    ├── unit/                  # Unit tests (134 tests)
    └── integration/           # Integration tests (20 tests)
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLI Interface                                        │
│                     (main.py, cli.py)                                      │
│                  Tool Configuration Layer                                   │
└───────────────────────────┬─────────────────────────────────────────────────┘
                           │
┌───────────────────────────┼─────────────────────────────────────────────────┐
│                   Speech Agent                                              │
│              (High-level orchestrator)                                     │
├─┬─────────────────────────────────────────────────────────────────────────┬─┤
  │                                                                         │
┌─▼────────────────┐  ┌──────────────────┐  ┌─────────────────────────────▼─┐
│  Audio Streamer  │  │ Bedrock Stream   │  │     Strands Tool Handler       │
│   (PyAudio)      │  │    Manager       │  │                               │
│                  │  │  (AWS Bedrock)   │  │ ┌───────────────────────────┐ │
│ • Microphone     │  │                  │  │ │     Tool Registry         │ │
│ • Speakers       │  │ • Nova Sonic     │  │ │                           │ │
│ • Voice Activity │  │ • Streaming      │  │ │ • current_time            │ │
│   Detection      │  │ • Tool Events    │  │ │ • calculator              │ │
│                  │  │ • Response       │  │ │ • [configurable tools]    │ │
└──────────────────┘  └──────────────────┘  │ └───────────────────────────┘ │
                                            └─────────────────────────────────┘
```

### **Component Responsibilities**

#### **🎛️ CLI Interface** (`main.py`, `cli.py`)
- **Entry point** with argument parsing
- **Centralized tool configuration** via `get_default_tools()`
- **Tool injection** into StrandsToolHandler
- **Debug mode** and logging configuration

#### **🤖 Speech Agent** (`speech_agent.py`) 
- **High-level orchestrator** managing conversation flow
- **Component coordination** between audio, Bedrock, and tools
- **Conversation lifecycle** (start, stop, error handling)
- **State management** and session persistence

#### **🎵 Audio Streamer** (`audio_streamer.py`)
- **Real-time audio capture** and playback
- **Voice activity detection** and barge-in support
- **PyAudio integration** with configurable parameters
- **Audio quality optimization** and noise handling

#### **☁️ Bedrock Stream Manager** (`bedrock_streamer.py`)
- **AWS Bedrock integration** with Nova Sonic
- **Bidirectional streaming** management
- **Event processing** and response handling
- **Tool execution coordination**

#### **🛠️ Strands Tool Handler** (`strands_tool_handler.py`)
- **Primary tool system** using Strands Agents SDK
- **Dynamic tool loading** and hot-reloading
- **Tool registry management** and execution
- **Bedrock-compatible tool schemas**

## 📦 Installation & Setup

### **Prerequisites**
- **Python 3.8+** (recommended: 3.11+)
- **AWS Account** with Bedrock access
- **Audio system** (microphone and speakers)
- **pip** package manager

### **1. Clone Repository**
```bash
git clone <repository-url>
cd speech-based-agents
```

### **2. Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# For development (includes testing dependencies)
pip install -r requirements.txt pytest-cov
```

### **3. AWS Configuration**
```bash
# Configure AWS credentials (choose one method)

# Method 1: AWS CLI
aws configure

# Method 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Method 3: IAM roles (recommended for production)
# Configure IAM role with Bedrock permissions
```

### **4. Verify Installation**
```bash
# Test CLI help
python main.py --help

# Test imports
python -c "from src.speech_agent import SpeechAgent; print('✅ Installation successful')"
```

## 🎯 Usage

### **Basic Usage**
```bash
# Start with Strands Agents SDK tools (default configuration)
python main.py

# With debug logging
python main.py --debug
```

### **CLI Options**
```bash
usage: main.py [-h] [--debug]

Nova Sonic Python Streaming

options:
  -h, --help    show this help message and exit
  --debug       Enable debug mode
```

### **Conversation Flow**
1. **Start the application**: `python main.py`
2. **Wait for initialization**: System loads models and tools
3. **Begin speaking**: Voice activity detection starts conversation
4. **Natural interaction**: AI responds with voice and executes tools
5. **End conversation**: Ctrl+C or natural conversation end

### **Available Tools**
- **current_time**: Get current date and time in various timezones
- **calculator**: Perform mathematical calculations and expressions
- **[Custom tools]**: Add your own via the Strands SDK

## 🧪 Testing

### **Run All Tests**
```bash
# Quick test run
python -m pytest tests/ -q

# Verbose output
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### **Test Categories**

#### **Unit Tests** (134 tests)
```bash
# Core component tests
python -m pytest tests/test_*.py -v

# Specific component
python -m pytest tests/test_strands_tool_handler.py -v
```

#### **Integration Tests** (20 tests)
```bash
# End-to-end integration testing
python -m pytest tests/integration/ -v

# CLI integration tests
python -m pytest tests/integration/test_cli_integration.py -v
```

#### **Test Structure**
```
tests/
├── __init__.py
├── test_audio_streamer.py         # Audio system tests
├── test_bedrock_streamer.py       # AWS Bedrock tests  
├── test_cli.py                    # CLI functionality tests
├── test_speech_agent.py           # Main agent tests
├── test_strands_tool_handler.py   # Strands integration tests
├── test_tool_handler.py           # Original tool tests (compatibility)
└── integration/                   # Integration tests
    ├── __init__.py
    └── test_cli_integration.py    # End-to-end tests
```

### **Test Results Summary**
- **Total Tests**: 154 ✅
- **Passing**: 154 tests
- **Failing**: 0 tests
- **Coverage**: Core functionality fully tested
- **Integration**: CLI, tools, and AWS integration verified

## 🔧 Development

### **Development Workflow**

#### **1. Add New Tools (Recommended Method)**
```python
# Add to src/cli.py get_default_tools() function
from strands_tools import current_time, calculator, my_new_tool

def get_default_tools():
    return [
        current_time,
        calculator,
        my_new_tool,  # Add your new tool here
    ]
```

#### **2. Create Custom Tools**
```python
# Create your tool using Strands SDK
from strands import tool

@tool
def my_custom_tool(param: str) -> dict:
    """
    Description of your tool.
    
    Args:
        param: Parameter description
        
    Returns:
        Result dictionary
    """
    return {
        "status": "success",
        "content": [{"text": f"Result: {param}"}]
    }
```

#### **3. Run Development Tests**
```bash
# Test specific changes
python -m pytest tests/test_strands_tool_handler.py -v

# Test integration
python -m pytest tests/integration/ -v

# Full test suite
python -m pytest tests/ --tb=short
```

### **Configuration Options**

#### **Environment Variables**
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1

# Application Configuration
STRANDS_DEBUG=true
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
```

## 🔒 Security & Best Practices

### **AWS Security**
- **Use IAM roles** instead of access keys when possible
- **Limit Bedrock permissions** to required models only
- **Enable CloudTrail** for API call logging
- **Rotate credentials** regularly

### **Application Security**
- **Validate tool inputs** to prevent injection attacks
- **Sanitize audio data** before processing
- **Implement timeouts** for tool execution
- **Log security events** appropriately

## 📈 Recent Updates & Changelog

### **🆕 Latest Changes (v2.1.0)**

#### **🏗️ Architecture Simplification**
- **Unified tool system** using only Strands Agents SDK
- **Centralized tool configuration** at CLI level
- **Dependency injection** pattern for better testability
- **Simplified CLI interface** with streamlined options

#### **🛠️ Enhanced Tool Management**
- **Configurable tool list** via `get_default_tools()` function
- **Easy tool addition/removal** by modifying CLI configuration
- **Improved tool loading** with proper error handling
- **Better tool registry management**

#### **🧪 Comprehensive Testing**
- **154 total tests** all passing ✅
- **Updated test coverage** for new architecture
- **Integration test improvements** for CLI functionality
- **Audio streamer test fixes** with proper mocking

#### **📚 Documentation Updates**
- **Complete README rewrite** reflecting new architecture
- **Updated usage examples** and development workflows
- **Simplified installation** and setup instructions
- **Current test status** and coverage information

### **Migration Guide (v2.0 → v2.1)**

#### **Breaking Changes**
- **Removed `--original-tools` flag** from CLI (simplified interface)
- **Tool configuration moved** to CLI level (`get_default_tools()`)

#### **Migration Steps**
```bash
# Old usage (no longer supported)
python main.py --original-tools

# New usage (simplified)
python main.py

# For custom tools, modify src/cli.py instead of command flags
```

#### **Developer Changes**
```python
# Old: Tools were hardcoded in StrandsToolHandler
handler = StrandsToolHandler()  # Had built-in tools

# New: Tools are injected via constructor
handler = StrandsToolHandler(tools=[current_time, calculator])
```

## 🆘 Troubleshooting

### **Common Issues**

#### **AWS Credentials**
```bash
# Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Or configure AWS CLI
aws configure
```

#### **Audio Issues**
```bash
# Error: Audio device not found
# Install PyAudio dependencies (macOS)
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio
```

#### **Strands Tools Not Loading**
```bash
# Check Strands installation
pip install strands-agents

# Verify installation
python -c "from strands_tools import current_time; print('Strands OK')"
```

### **Debug Mode**
```bash
# Enable verbose logging
python main.py --debug

# Check tool configuration
python -c "
from src.cli import get_default_tools
tools = get_default_tools()
print(f'Configured tools: {[tool.__name__ for tool in tools]}')
"
```

### **Test Issues**
```bash
# Run specific test file
python -m pytest tests/test_cli.py -v

# Run with output capture disabled  
python -m pytest tests/test_strands_tool_handler.py -v -s

# Check test coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Amazon Bedrock Team** for LLM infrastructure
- **Strands Agents SDK** for tool management framework  
- **Python Audio Community** for PyAudio and audio processing libraries
- **Open Source Contributors** for testing and feedback

---

**🚀 Ready to build the future of voice-enabled AI? Start with `python main.py` and begin your conversation!**