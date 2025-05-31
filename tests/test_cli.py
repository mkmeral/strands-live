import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.cli import main, run_cli, get_default_tools


class TestCLI:
    """Test cases for the CLI module."""

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @pytest.mark.asyncio
    async def test_main_success(self, mock_speech_agent_class, mock_strands_handler_class):
        """Test the main function runs successfully with Strands handler."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock()
        mock_speech_agent.start_conversation = AsyncMock()
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Run main function
        await main(debug=False)
        
        # Verify StrandsToolHandler was created with tools
        mock_strands_handler_class.assert_called_once()
        call_args = mock_strands_handler_class.call_args
        assert 'tools' in call_args.kwargs
        assert len(call_args.kwargs['tools']) == 2  # current_time and calculator
        
        # Verify SpeechAgent was created with Strands handler
        mock_speech_agent_class.assert_called_once_with(
            model_id='amazon.nova-sonic-v1:0', 
            region='us-east-1',
            tool_handler=mock_strands_handler
        )
        
        # Verify methods were called
        mock_speech_agent.initialize.assert_called_once()
        mock_speech_agent.start_conversation.assert_called_once()

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @pytest.mark.asyncio
    async def test_main_with_custom_tools(self, mock_speech_agent_class, mock_strands_handler_class):
        """Test the main function with custom tools."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock()
        mock_speech_agent.start_conversation = AsyncMock()
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Create custom tools list
        custom_tools = [Mock(), Mock()]
        
        # Run main function with custom tools
        await main(debug=False, tools=custom_tools)
        
        # Verify StrandsToolHandler was created with custom tools
        mock_strands_handler_class.assert_called_once()
        call_args = mock_strands_handler_class.call_args
        assert 'tools' in call_args.kwargs
        assert call_args.kwargs['tools'] == custom_tools
        
        # Verify methods were called
        mock_speech_agent.initialize.assert_called_once()
        mock_speech_agent.start_conversation.assert_called_once()

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @pytest.mark.asyncio
    async def test_main_with_debug(self, mock_speech_agent_class, mock_strands_handler_class):
        """Test the main function with debug mode enabled."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock()
        mock_speech_agent.start_conversation = AsyncMock()
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Run main function with debug
        await main(debug=True)
        
        # Verify StrandsToolHandler was created
        mock_strands_handler_class.assert_called_once()
        mock_speech_agent_class.assert_called_once()
        mock_speech_agent.initialize.assert_called_once()
        mock_speech_agent.start_conversation.assert_called_once()

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self, mock_speech_agent_class, mock_strands_handler_class):
        """Test that main handles KeyboardInterrupt gracefully."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock()
        mock_speech_agent.start_conversation = AsyncMock(side_effect=KeyboardInterrupt())
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Should not raise exception
        await main(debug=False)
        
        # Verify methods were called up to the interruption
        mock_speech_agent.initialize.assert_called_once()
        mock_speech_agent.start_conversation.assert_called_once()

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @patch('builtins.print')
    @pytest.mark.asyncio
    async def test_main_general_exception(self, mock_print, mock_speech_agent_class, mock_strands_handler_class):
        """Test that main handles general exceptions gracefully."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock(side_effect=Exception("Test error"))
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Should not raise exception
        await main(debug=False)
        
        # Verify error was printed
        mock_print.assert_called_with("Application error: Test error")

    @patch('src.cli.StrandsToolHandler')
    @patch('src.cli.SpeechAgent')
    @patch('builtins.print')
    @patch('traceback.print_exc')
    @pytest.mark.asyncio
    async def test_main_exception_with_debug(self, mock_traceback, mock_print, mock_speech_agent_class, mock_strands_handler_class):
        """Test that main prints traceback in debug mode."""
        # Mock the handler and SpeechAgent
        mock_strands_handler = Mock()
        mock_strands_handler_class.return_value = mock_strands_handler
        
        mock_speech_agent = Mock()
        mock_speech_agent.initialize = AsyncMock(side_effect=Exception("Test error"))
        mock_speech_agent_class.return_value = mock_speech_agent
        
        # Should not raise exception
        await main(debug=True)
        
        # Verify error was printed and traceback was shown
        mock_print.assert_called_with("Application error: Test error")
        mock_traceback.assert_called_once()

    def test_get_default_tools(self):
        """Test that get_default_tools returns the expected tools."""
        tools = get_default_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2  # current_time and calculator
        
        # Import the expected tools to compare
        from strands_tools import current_time, calculator
        assert current_time in tools
        assert calculator in tools

    @patch('argparse.ArgumentParser.parse_args')
    @patch('asyncio.run')
    def test_run_cli_without_debug(self, mock_asyncio_run, mock_parse_args):
        """Test run_cli without debug flag."""
        # Mock argument parsing to return default flags
        mock_args = Mock()
        mock_args.debug = False
        mock_parse_args.return_value = mock_args
        
        # Run CLI
        run_cli()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('asyncio.run')
    def test_run_cli_with_debug(self, mock_asyncio_run, mock_parse_args):
        """Test run_cli with debug flag."""
        # Mock argument parsing to return debug flag
        mock_args = Mock()
        mock_args.debug = True
        mock_parse_args.return_value = mock_args
        
        # Run CLI
        run_cli()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('asyncio.run')
    @patch('builtins.print')
    def test_run_cli_exception_handling(self, mock_print, mock_asyncio_run, mock_parse_args):
        """Test that run_cli handles exceptions gracefully."""
        # Mock argument parsing
        mock_args = Mock()
        mock_args.debug = False
        mock_parse_args.return_value = mock_args
        
        # Mock asyncio.run to raise exception
        mock_asyncio_run.side_effect = Exception("CLI error")
        
        # Should not raise exception
        run_cli()
        
        # Verify error was printed
        mock_print.assert_called_with("Application error: CLI error")