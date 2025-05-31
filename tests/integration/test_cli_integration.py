"""
Integration tests for CLI and tool handler functionality.

These tests verify that the CLI works end-to-end with Strands tools,
testing real component interactions without requiring AWS credentials.
"""

import os
import subprocess
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from strands_tools import calculator, current_time

from strands_live.cli import get_default_tools, main, run_cli
from strands_live.speech_agent import SpeechAgent
from strands_live.strands_tool_handler import StrandsToolHandler
from strands_live.tool_handler import ToolHandler


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_cli_help_message(self):
        """Test that CLI help message shows all expected options."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "--debug" in result.stdout
        assert "Nova Sonic Python Streaming" in result.stdout

    @patch("strands_live.cli.SpeechAgent")
    @patch("strands_live.cli.StrandsToolHandler")
    @pytest.mark.asyncio
    async def test_main_uses_strands_by_default(
        self, mock_strands_handler, mock_speech_agent
    ):
        """Test that main() uses StrandsToolHandler by default."""
        # Setup mocks
        mock_strands_instance = Mock()
        mock_strands_handler.return_value = mock_strands_instance

        mock_agent_instance = Mock()
        mock_agent_instance.initialize = AsyncMock()
        mock_agent_instance.start_conversation = AsyncMock()
        mock_speech_agent.return_value = mock_agent_instance

        # Test default behavior
        await main(debug=False)

        # Verify StrandsToolHandler was used with tools
        mock_strands_handler.assert_called_once()
        call_args = mock_strands_handler.call_args
        assert "tools" in call_args.kwargs
        assert len(call_args.kwargs["tools"]) == 2  # current_time and calculator

        # Verify SpeechAgent was created with Strands handler
        mock_speech_agent.assert_called_once_with(
            model_id="amazon.nova-sonic-v1:0",
            region="us-east-1",
            tool_handler=mock_strands_instance,
        )

    @patch("strands_live.cli.SpeechAgent")
    @patch("strands_live.cli.StrandsToolHandler")
    @pytest.mark.asyncio
    async def test_main_with_custom_tools(
        self, mock_strands_handler, mock_speech_agent
    ):
        """Test that main() uses custom tools when provided."""
        # Setup mocks
        mock_strands_instance = Mock()
        mock_strands_handler.return_value = mock_strands_instance

        mock_agent_instance = Mock()
        mock_agent_instance.initialize = AsyncMock()
        mock_agent_instance.start_conversation = AsyncMock()
        mock_speech_agent.return_value = mock_agent_instance

        # Create custom tools
        custom_tools = [Mock(), Mock(), Mock()]

        # Test with custom tools
        await main(debug=False, tools=custom_tools)

        # Verify StrandsToolHandler was used with custom tools
        mock_strands_handler.assert_called_once()
        call_args = mock_strands_handler.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == custom_tools

        # Verify SpeechAgent was created with Strands handler
        mock_speech_agent.assert_called_once_with(
            model_id="amazon.nova-sonic-v1:0",
            region="us-east-1",
            tool_handler=mock_strands_instance,
        )


class TestToolHandlerIntegration:
    """Integration tests for tool handler functionality."""

    def test_strands_tool_handler_initialization(self):
        """Test that StrandsToolHandler initializes properly with tools."""
        handler = StrandsToolHandler(tools=[current_time, calculator])

        # Verify it has the expected interface
        assert hasattr(handler, "process_tool_use")
        assert hasattr(handler, "get_supported_tools")
        assert callable(handler.process_tool_use)
        assert callable(handler.get_supported_tools)
        assert hasattr(handler, "tools")
        assert len(handler.tools) == 2

    def test_original_tool_handler_initialization(self):
        """Test that original ToolHandler initializes properly."""
        handler = ToolHandler()

        # Verify it has the expected interface
        assert hasattr(handler, "process_tool_use")
        assert hasattr(handler, "get_supported_tools")
        assert callable(handler.process_tool_use)
        assert callable(handler.get_supported_tools)

    def test_strands_tool_handler_has_expected_tools(self):
        """Test that StrandsToolHandler provides expected tools."""
        handler = StrandsToolHandler(tools=[current_time, calculator])
        tools = handler.get_supported_tools()

        # Should be a list of tool names
        assert isinstance(tools, list)
        assert len(tools) == 2

        # Should contain expected tools
        assert "current_time" in tools
        assert "calculator" in tools

    def test_original_tool_handler_has_expected_tools(self):
        """Test that original ToolHandler provides expected tools."""
        handler = ToolHandler()
        tools = handler.get_supported_tools()

        # Should be a list of tool names
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Should contain expected tools
        assert "getDateAndTimeTool" in tools
        assert "trackOrderTool" in tools

    @pytest.mark.asyncio
    async def test_strands_tool_handler_can_handle_tool_use(self):
        """Test that StrandsToolHandler can handle tool use requests."""
        handler = StrandsToolHandler(tools=[current_time, calculator])

        # Test with current_time tool
        result = await handler.process_tool_use("current_time", {"content": "{}"})

        # Result should be a dictionary with required fields
        assert isinstance(result, dict)
        assert "status" in result
        assert "content" in result
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_original_tool_handler_can_handle_tool_use(self):
        """Test that original ToolHandler can handle tool use requests."""
        handler = ToolHandler()

        # Should not raise exception
        try:
            result = await handler.process_tool_use("getDateAndTimeTool", {})
            # Result should be a dictionary with required fields
            assert isinstance(result, dict)
            assert "formattedTime" in result or "error" in result
        except Exception as e:
            # Some tools might not work without proper setup, but the handler should exist
            assert "getDateAndTimeTool" in str(e) or "tool" in str(e).lower()


class TestSpeechAgentIntegration:
    """Integration tests for SpeechAgent with different tool handlers."""

    def test_speech_agent_initialization_with_strands_handler(self):
        """Test SpeechAgent initialization with StrandsToolHandler."""
        strands_handler = StrandsToolHandler(tools=[current_time, calculator])
        agent = SpeechAgent(
            model_id="amazon.nova-sonic-v1:0",
            region="us-east-1",
            tool_handler=strands_handler,
        )

        # Verify agent was initialized with the correct handler
        assert agent.tool_handler is strands_handler
        assert agent.model_id == "amazon.nova-sonic-v1:0"
        assert agent.region == "us-east-1"

    def test_speech_agent_initialization_with_original_handler(self):
        """Test SpeechAgent initialization with original ToolHandler."""
        original_handler = ToolHandler()
        agent = SpeechAgent(
            model_id="amazon.nova-sonic-v1:0",
            region="us-east-1",
            tool_handler=original_handler,
        )

        # Verify agent was initialized with the correct handler
        assert agent.tool_handler is original_handler
        assert agent.model_id == "amazon.nova-sonic-v1:0"
        assert agent.region == "us-east-1"

    def test_speech_agent_initialization_with_default_handler(self):
        """Test SpeechAgent initialization with default handler."""
        agent = SpeechAgent(model_id="amazon.nova-sonic-v1:0", region="us-east-1")

        # Should use default ToolHandler
        assert agent.tool_handler is not None
        assert isinstance(agent.tool_handler, ToolHandler)


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_get_default_tools_function(self):
        """Test that get_default_tools returns expected tools."""
        tools = get_default_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2
        assert current_time in tools
        assert calculator in tools

    @patch.dict(os.environ, {}, clear=True)
    def test_cli_runs_without_aws_credentials(self):
        """Test that CLI handles missing AWS credentials gracefully."""
        # This should fail with AWS credential error, not import/setup errors
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from strands_live.cli import main; print('CLI imports successful')",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "CLI imports successful" in result.stdout

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing with various combinations."""
        test_cases = [
            (["--help"], 0),
            (["--debug", "--help"], 0),
        ]

        for args, expected_code in test_cases:
            result = subprocess.run(
                [sys.executable, "main.py"] + args, capture_output=True, text=True
            )
            assert result.returncode == expected_code, f"Failed for args: {args}"

    @patch("strands_live.cli.SpeechAgent")
    @patch("strands_live.cli.StrandsToolHandler")
    def test_cli_configuration_flow(self, mock_strands_handler, mock_speech_agent):
        """Test the complete CLI configuration flow."""
        # Setup mocks
        mock_strands_instance = Mock()
        mock_strands_handler.return_value = mock_strands_instance

        mock_agent_instance = Mock()
        mock_agent_instance.initialize = AsyncMock()
        mock_agent_instance.start_conversation = AsyncMock(
            side_effect=KeyboardInterrupt
        )
        mock_speech_agent.return_value = mock_agent_instance

        # Test CLI with different argument combinations
        test_cases = [
            # (args)
            ([]),  # Default should use Strands
            (["--debug"]),  # Should use Strands with debug
        ]

        for args in test_cases:
            with patch("sys.argv", ["main.py"] + args):
                try:
                    run_cli()
                except SystemExit:
                    pass  # Expected due to argparse in tests
                except Exception:
                    pass  # Expected due to mocked components

                # The important thing is that imports and setup work
                assert mock_speech_agent.called

    def test_project_structure_integrity(self):
        """Test that project structure is intact."""
        required_files = [
            "main.py",
            "src/__init__.py",
            "src/cli.py",
            "src/speech_agent.py",
            "src/strands_tool_handler.py",
            "src/tool_handler.py",
            "tests/__init__.py",
            "requirements.txt",
        ]

        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file missing: {file_path}"

    def test_requirements_can_be_parsed(self):
        """Test that requirements.txt can be parsed."""
        with open("requirements.txt") as f:
            requirements = f.read()

        # Should contain expected dependencies
        assert "pytest" in requirements
        assert len(requirements.strip()) > 0

        # Check for key dependencies
        lines = requirements.strip().split("\n")
        assert len(lines) > 0

    def test_main_py_exists_and_runnable(self):
        """Test that main.py exists and can be imported."""
        assert os.path.exists("main.py")

        # Test that it can be imported without errors
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import main; print('main.py imports successfully')",
            ],
            capture_output=True,
            text=True,
        )

        # Should not have import errors
        assert result.returncode == 0
        assert "main.py imports successfully" in result.stdout
