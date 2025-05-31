# 🎙️ Speech-Based AI Agents with Strands Integration

A **high-performance, real-time speech-based AI agent system** that seamlessly integrates with **Amazon Bedrock**, **Nova Sonic**, and the **Strands Agents SDK**. This system enables natural voice conversations with AI agents that can execute tools, manage state, and provide intelligent responses through advanced speech processing.

## 🚀 Key Features

### **🔊 Advanced Speech Processing**
- **Real-time audio streaming** with AWS Nova Sonic
- **High-quality voice synthesis** and recognition
- **Low-latency conversation flow** for natural interactions
- **Configurable audio parameters** (sample rate, channels, etc.)

### **🤖 Intelligent Agent System**
- **Dual tool handler architecture** (Strands SDK + Original)
- **Extensible tool ecosystem** with hot-reloading capabilities
- **Advanced conversation management** with context preservation
- **Error handling and recovery** for robust operation

### **🛠️ Strands Agents SDK Integration**
- **Default Strands tools** for enhanced functionality
- **Seamless tool proxy** between systems
- **Dynamic tool loading** and management
- **Backward compatibility** with original tools

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
│   ├── cli.py                 # Command-line interface
│   ├── speech_agent.py        # Main agent orchestrator
│   ├── audio_streamer.py      # Audio processing
│   ├── bedrock_streamer.py    # AWS Bedrock integration
│   ├── strands_tool_handler.py # Strands SDK integration
│   ├── tool_handler.py        # Original tool handler
│   └── tool_handler_base.py   # Base tool handler class
└── tests/                     # Test suite
    ├── unit/                  # Unit tests (128 tests)
    └── integration/           # Integration tests (18 tests)
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                            │
│                     (main.py, cli.py)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Speech Agent                                  │
│              (High-level orchestrator)                         │
└─┬─────────────────────────────────────────────────────────────┬─┘
  │                                                             │
┌─▼────────────────┐  ┌──────────────────┐  ┌─────────────────▼─┐
│  Audio Streamer  │  │ Bedrock Stream   │  │   Tool Handlers   │
│   (PyAudio)      │  │    Manager       │  │                   │
│                  │  │  (AWS Bedrock)   │  │ ┌───────────────┐ │
│ • Microphone     │  │                  │  │ │ Strands Tools │ │
│ • Speakers       │  │ • Nova Sonic     │  │ │   (Default)   │ │
│ • Voice Activity │  │ • Streaming      │  │ └───────────────┘ │
│   Detection      │  │ • Tool Events    │  │ ┌───────────────┐ │
└──────────────────┘  └──────────────────┘  │ │Original Tools │ │
                                            │ │(Compatibility)│ │
                                            │ └───────────────┘ │
                                            └───────────────────┘
```

### **Component Responsibilities**

#### **🎛️ CLI Interface** (`main.py`, `cli.py`)
- **Entry point** with argument parsing
- **Tool handler selection** (Strands vs Original)
- **Configuration management** and environment setup
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

#### **🛠️ Tool Handlers**
- **Strands Tool Handler** (`strands_tool_handler.py`)
  - **Default handler** using Strands Agents SDK
  - **Dynamic tool loading** and hot-reloading
  - **Tool registry management** and proxy functions
  - **Advanced tool ecosystem** integration

- **Original Tool Handler** (`tool_handler.py`)
  - **Backward compatibility** handler
  - **Built-in tools** (date/time, order tracking)
  - **Simple tool interface** for basic functionality
  - **Legacy support** and migration path  

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

### **Basic Usage (Strands Tools - Default)**
```bash
# Start with Strands Agents SDK tools (recommended)
python main.py

# With debug logging
python main.py --debug
```

### **Original Tools (Backward Compatibility)**
```bash
# Use original tool handler
python main.py --original-tools

# Debug mode with original tools
python main.py --debug --original-tools
```

### **CLI Options**
```bash
usage: main.py [-h] [--debug] [--original-tools]

Nova Sonic Python Streaming

options:
  -h, --help        show this help message and exit
  --debug           Enable debug mode
  --original-tools  Use original tool handler instead of Strands tools
```

### **Conversation Flow**
1. **Start the application**: `python main.py`
2. **Wait for initialization**: System loads models and tools
3. **Begin speaking**: Voice activity detection starts conversation
4. **Natural interaction**: AI responds with voice and executes tools
5. **End conversation**: Ctrl+C or natural conversation end

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

#### **Unit Tests** (128 tests)
```bash
# Core component tests
python -m pytest tests/test_*.py -v

# Specific component
python -m pytest tests/test_strands_tool_handler.py -v
```

#### **Integration Tests** (18 tests)
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
├── test_tool_handler.py           # Original tool tests
└── integration/                   # Integration tests
    ├── __init__.py
    └── test_cli_integration.py    # End-to-end tests
```

### **Test Results Summary**
- **Total Tests**: 146
- **Passing**: 143 ✅
- **Coverage**: Core functionality fully tested
- **Integration**: CLI, tools, and AWS integration verified

## 🔧 Development

### **Development Workflow**

#### **1. Add New Tools (Strands Method - Recommended)**
```python
# Create tools/my_tool.py
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

#### **2. Add New Tools (Original Method)**
```python
# Extend ToolHandler in src/tool_handler.py
async def process_tool_use(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "my_new_tool":
        return await self._my_new_tool(parameters)
    # ... existing tools
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

### **🆕 Latest Changes (v2.0.0)**

#### **🚀 Strands Agents SDK Integration**
- **Default tool handler** now uses Strands Agents SDK
- **Seamless tool proxy** between Strands and original systems
- **Hot-reloading tools** from `cwd()/tools/` directory
- **Backward compatibility** maintained with `--original-tools` flag

#### **🛠️ Enhanced CLI Interface**
- **New CLI options**: `--original-tools` flag for compatibility
- **Clear messaging**: Shows which tool system is active
- **Improved error handling** and user feedback
- **Extended help documentation**

#### **🧪 Comprehensive Testing**
- **146 total tests** (up from 128)
- **18 new integration tests** for end-to-end validation
- **Tool handler compatibility** testing
- **CLI functionality** verification

#### **📚 Documentation Updates**
- **Complete README rewrite** with usage examples
- **Architecture diagrams** and component breakdown
- **Detailed installation** and setup instructions
- **Development workflow** documentation

### **Migration Guide (v1.x → v2.0)**

#### **No Breaking Changes**
- **Existing functionality** preserved
- **Original tools** still available with `--original-tools`
- **Same command-line interface** with new options

#### **Recommended Updates**
```bash
# Old usage (still works)
python main.py

# New usage (enhanced with Strands)
python main.py  # Now uses Strands by default

# Access original tools
python main.py --original-tools
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
python -c "from strands import Agent; print('Strands OK')"
```

### **Debug Mode**
```bash
# Enable verbose logging
python main.py --debug

# Check specific components
python -c "
from src.strands_tool_handler import StrandsToolHandler
handler = StrandsToolHandler()
print('Available tools:', handler.get_supported_tools())
"
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