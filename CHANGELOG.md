# Changelog

## [Unreleased] - 2024-01-XX

### Added
- **Tasks Tool Integration**: Added comprehensive background task management system
  - Create, list, pause, resume, and delete long-running tasks
  - Persistent state management with JSON-based storage
  - Thread-based execution with proper lifecycle management
  - Error handling and task status tracking
  - Integration with Strands Agents for task execution

### Fixed
- **Model Configuration**: Fixed model loading in tasks tool to use correct Bedrock model configuration
  - Proper `pathlib.Path` handling for model file loading
  - Correct usage of `model_utils.load_path()` and `model_utils.load_config()`
  - Fixed `'str' object has no attribute 'stem'` error

- **Stream Reliability**: Major improvements to Bedrock streaming robustness
  - Fixed "Invalid event bytes" errors with proper error detection and recovery
  - Fixed "Stream is completed and doesn't support further writes" errors
  - Added stream closure detection and prevention mechanisms
  - Implemented proper resource cleanup and task management
  - Enhanced error handling with exponential backoff and retry logic
  - Added audio data validation to prevent corrupted data transmission

- **JSON Error Handling**: Enhanced task state loading with corrupted file recovery
  - Graceful handling of malformed JSON files
  - Detailed error logging for debugging
  - Continued operation even with some corrupted task files
  - User warnings about corrupted files

### Changed
- **Default Voice**: Changed default voice from "matthew" to "tiffany"
- **Order Number Reading**: Added special instruction for reading order numbers digit-by-digit
- **Tool Configuration**: Enabled tasks tool by default (replaced use_llm in default tools)
- **Dependencies**: Added `aws_sdk_bedrock_runtime>=0.0.2` dependency

### Improved
- **Error Recovery**: Comprehensive error handling and recovery mechanisms
  - Stream auto-reinitialization on failures
  - Proper task cancellation and cleanup
  - Better error categorization and handling
  - Reduced system crashes and improved stability

- **Code Quality**: Enhanced code organization and documentation
  - Better error messages and debugging information
  - Improved type safety and parameter validation
  - Enhanced resource management and cleanup

### Technical Details
- **Stream Management**: Complete rewrite of stream lifecycle management
  - Added `is_stream_closed` flag for proper closure tracking
  - Implemented `_cleanup_stream()` for resource management
  - Enhanced `ensure_stream_active()` with proper recovery logic
  - Better task tracking with `audio_input_task` and `response_task`

- **Audio Processing**: Improved audio input validation and processing
  - Size validation for audio chunks
  - Type checking for audio data
  - Error counting and circuit breaker patterns
  - Timeout handling for queue operations

- **Task System**: Robust background task management
  - Thread-based execution with proper isolation
  - Persistent state with automatic recovery
  - Comprehensive error handling and logging
  - Clean shutdown and resource cleanup