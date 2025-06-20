#!/usr/bin/env python3
"""
Test script to verify agent compatibility with both Docker and Modal environments.
Task 4.3: Ensure agent works in both Docker and Modal environments
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add agent_sandbox to path
sys.path.append(str(Path("agent_sandbox")))
from agent_sandbox.coding_agent import (
    is_modal_environment, 
    docker_exec, 
    modal_exec
)

def test_modal_environment_detection():
    """Test that Modal environment detection works correctly."""
    
    # Test without Modal environment
    with patch.dict(os.environ, {}, clear=True):
        assert not is_modal_environment(), "Should not detect Modal environment when MODAL_SANDBOX_ID is not set"
    
    # Test with Modal environment
    with patch.dict(os.environ, {"MODAL_SANDBOX_ID": "test-sandbox-123"}, clear=True):
        assert is_modal_environment(), "Should detect Modal environment when MODAL_SANDBOX_ID is set"


def test_docker_exec_compatibility():
    """Test that docker_exec function works with Docker containers."""
    
    # Mock subprocess.run to avoid actual Docker calls
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.txt\nfile2.txt\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test docker_exec with a simple command
        result = docker_exec(
            container="test-container",
            cmd=["ls", "-l"],
            cwd="/workspace",
            env={"TEST_VAR": "test_value"}
        )
        
        # Verify subprocess.run was called with correct Docker command
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        
        # Check that the command starts with docker exec
        assert call_args[0] == "docker"
        assert call_args[1] == "exec"
        assert call_args[2] == "-w"
        assert call_args[3] == "/workspace"
        assert "-e" in call_args
        assert "TEST_VAR=test_value" in call_args
        assert "test-container" in call_args
        assert "ls" in call_args
        assert "-l" in call_args
        
        # Verify return value
        assert result.returncode == 0
        assert result.stdout == "file1.txt\nfile2.txt\n"


def test_modal_exec_compatibility():
    """Test that modal_exec function works with Modal sandboxes."""
    
    # Mock Modal sandbox
    mock_sandbox = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout = MagicMock()
    mock_result.stdout.read.return_value = "file1.txt\nfile2.txt\n"
    mock_result.stderr = MagicMock()
    mock_result.stderr.read.return_value = ""
    mock_sandbox.exec.return_value = mock_result
    
    # Test modal_exec with a simple command
    result = modal_exec(
        sandbox=mock_sandbox,
        cmd=["ls", "-l"],
        cwd="/workspace"
    )
    
    # Verify sandbox.exec was called
    mock_sandbox.exec.assert_called_once()
    
    # Verify return value structure (CompletedProcess-like)
    assert hasattr(result, 'returncode')
    assert hasattr(result, 'stdout')
    assert hasattr(result, 'stderr')
    assert result.stdout == "file1.txt\nfile2.txt\n"


def test_logger_selection_logic():
    """Test that logger selection works correctly for both environments."""
    
    # Test Docker environment (should default to stdout)
    with patch('agent_sandbox.coding_agent.is_modal_environment', return_value=False):
        with patch('agent_sandbox.coding_agent.StdoutLogger') as mock_stdout_logger:
            mock_stdout_logger.return_value = MagicMock()
            
            # Test with no logger specified (should default to stdout)
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_response = MagicMock()
                mock_response.id = "test-response-id"
                mock_response.output = []
                mock_client.responses.create.return_value = mock_response
                
                from agent_sandbox.coding_agent import run_coding_agent
                run_coding_agent(
                    request="Test request",
                    container_or_sandbox="test-container",
                    logger=None,  # Should default to stdout
                    use_modal=False
                )
                
                # Verify StdoutLogger was created
                mock_stdout_logger.assert_called_once()
    
    # Test Modal environment (should default to file)
    with patch('agent_sandbox.coding_agent.is_modal_environment', return_value=True):
        with patch('agent_sandbox.coding_agent.FileLogger') as mock_file_logger:
            mock_file_logger.return_value = MagicMock()
            
            # Test with no logger specified (should default to file)
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_response = MagicMock()
                mock_response.id = "test-response-id"
                mock_response.output = []
                mock_client.responses.create.return_value = mock_response
                
                from agent_sandbox.coding_agent import run_coding_agent
                run_coding_agent(
                    request="Test request",
                    container_or_sandbox=MagicMock(),
                    logger=None,  # Should default to file
                    use_modal=True
                )
                
                # Verify FileLogger was created
                mock_file_logger.assert_called_once_with(file_path="outputs/shell_log.jsonl")


def test_import_compatibility():
    """Test that all required modules can be imported in both environments."""
    
    # Test core agent imports
    from agent_sandbox.coding_agent import (
        run_coding_agent, 
        docker_exec, 
        modal_exec, 
        is_modal_environment
    )
    
    # Test logger imports
    from agent_sandbox.shell_logger import (
        ShellLogger, 
        NullLogger, 
        HTTPEndpointLogger, 
        StdoutLogger, 
        FileLogger
    )
    
    # Test Modal imports (should work even if Modal is not installed)
    try:
        import modal
    except ImportError:
        pytest.skip("Modal not installed - this is expected in Docker environment")
    
    # Test Docker imports
    try:
        import docker
    except ImportError:
        pytest.skip("Docker not installed - this is expected in Modal environment")


def test_function_signatures():
    """Test that function signatures are compatible between environments."""
    
    from agent_sandbox.coding_agent import run_coding_agent, docker_exec, modal_exec
    
    # Test that run_coding_agent has the expected signature
    import inspect
    sig = inspect.signature(run_coding_agent)
    expected_params = ['request', 'container_or_sandbox', 'logger', 'use_modal']
    
    for param in expected_params:
        assert param in sig.parameters, f"Missing parameter: {param}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 