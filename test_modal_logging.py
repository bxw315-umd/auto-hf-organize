#!/usr/bin/env python3
"""
Test Modal logging functionality with real Modal sandbox and OpenAI-style commands.
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
import modal
from pathlib import Path
from unittest.mock import patch

# Add agent_sandbox to path
sys.path.append(str(Path("agent_sandbox")))
from agent_sandbox.coding_agent import modal_exec, is_modal_environment
from agent_sandbox.shell_logger import FileLogger


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="modal_test_")
    workspace = Path(temp_dir) / "workspace"
    workspace.mkdir(exist_ok=True)
    
    # Create some test files
    (workspace / "test_file.txt").write_text("This is a test file")
    (workspace / "AGENTS.md").write_text("# Agent Instructions\n\nProcess the data files.")
    
    yield workspace
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_real_modal_sandbox_with_file_logger(temp_workspace):
    """Test real Modal sandbox with FileLogger using OpenAI-style commands."""
    
    # Create output directory for logs
    output_dir = temp_workspace / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Create FileLogger
    log_file_path = output_dir / "shell_log.jsonl"
    logger = FileLogger(str(log_file_path))
    
    # Create/lookup Modal App
    app = modal.App.lookup("sandbox-environment", create_if_missing=True)
    
    # Create custom image with our test workspace
    image = (
        modal.Image.debian_slim()
        .pip_install_from_requirements("agent_sandbox/user_files/requirements.txt")
    )
    
    # Mount the test workspace
    image = image.add_local_dir(temp_workspace, "/workspace")
    
    # Create ephemeral volume
    with modal.Volume.ephemeral() as vol:
        # Create Modal Sandbox
        sb = modal.Sandbox.create(
            app=app,
            image=image,
            volumes={"/output": vol},
            workdir="/workspace"
        )
        
        # OpenAI-style commands (from the shell log format)
        test_commands = [
            ["bash", "-lc", "ls -la"],
            ["bash", "-lc", "cat test_file.txt"],
            ["bash", "-lc", "head -n 5 AGENTS.md"],
            ["bash", "-lc", "pwd"],
            ["bash", "-lc", "echo 'Hello from Modal sandbox'"]
        ]
        
        # Execute each command and log the results
        for i, cmd in enumerate(test_commands):
            print(f"Executing command {i+1}: {cmd}")
            
            # Execute command in sandbox
            result = modal_exec(sb, cmd)
            
            # Log the command and output (OpenAI format)
            log_entry = {
                "command": cmd,
                "output": result.stdout + result.stderr
            }
            logger.log(log_entry)
            
            print(f"Command output: {result.stdout[:100]}...")
        
        # Terminate sandbox
        sb.terminate()
    
    # Verify log file was created and contains expected data
    assert log_file_path.exists(), f"Log file should be created at {log_file_path}"
    
    # Read and verify log entries
    with open(log_file_path, 'r') as f:
        log_lines = f.readlines()
    
    assert len(log_lines) == len(test_commands), f"Expected {len(test_commands)} log entries, got {len(log_lines)}"
    
    # Parse and verify log entries
    log_entries = [json.loads(line.strip()) for line in log_lines]
    
    # Verify commands match
    for i, entry in enumerate(log_entries):
        assert entry["command"] == test_commands[i], f"Command mismatch at index {i}"
        assert "output" in entry, f"Missing output in entry {i}"
        assert len(entry["output"]) > 0, f"Empty output in entry {i}"
    
    # Verify specific outputs
    outputs = [entry["output"] for entry in log_entries]
    
    # Check that ls command found our files
    assert any("test_file.txt" in output for output in outputs), "ls command should find test_file.txt"
    assert any("AGENTS.md" in output for output in outputs), "ls command should find AGENTS.md"
    
    # Check that cat command showed file content
    assert any("This is a test file" in output for output in outputs), "cat command should show file content"
    
    # Check that head command showed AGENTS.md content
    assert any("Agent Instructions" in output for output in outputs), "head command should show AGENTS.md content"
    
    # Check that pwd shows workspace
    assert any("/workspace" in output for output in outputs), "pwd should show /workspace"
    
    # Check that echo command worked
    assert any("Hello from Modal sandbox" in output for output in outputs), "echo command should work"
    
    print(f"✅ Real Modal sandbox test passed! Created log file with {len(log_entries)} entries")
    print(f"Log file: {log_file_path}")
    
    # Show a sample log entry
    print(f"Sample log entry: {json.dumps(log_entries[0], indent=2)}")


def test_modal_environment_detection():
    """Test that Modal environment detection works correctly."""
    
    # Test without Modal environment
    with patch.dict(os.environ, {}, clear=True):
        assert not is_modal_environment(), "Should not detect Modal environment when MODAL_SANDBOX_ID is not set"
    
    # Test with Modal environment
    with patch.dict(os.environ, {"MODAL_SANDBOX_ID": "test-sandbox-123"}, clear=True):
        assert is_modal_environment(), "Should detect Modal environment when MODAL_SANDBOX_ID is set"


def test_conditional_logger_selection():
    """Test that the right logger is selected based on environment."""
    
    from agent_sandbox.coding_agent import run_coding_agent
    
    # Test Docker environment (no Modal env var)
    with patch.dict(os.environ, {}, clear=True):
        # Mock the logger creation to just return the logger type
        with patch('agent_sandbox.coding_agent.StdoutLogger') as mock_stdout:
            with patch('agent_sandbox.coding_agent.FileLogger') as mock_file:
                # This will fail because we're not providing a real container/sandbox,
                # but we can catch the error and verify the logger was selected correctly
                try:
                    run_coding_agent("test", None, logger=None, use_modal=False)
                except:
                    pass
                
                # Verify StdoutLogger was called (for Docker environment)
                mock_stdout.assert_called_once()
                mock_file.assert_not_called()
    
    # Test Modal environment
    with patch.dict(os.environ, {"MODAL_SANDBOX_ID": "test-sandbox-123"}, clear=True):
        with patch('agent_sandbox.coding_agent.StdoutLogger') as mock_stdout:
            with patch('agent_sandbox.coding_agent.FileLogger') as mock_file:
                try:
                    run_coding_agent("test", None, logger=None, use_modal=True)
                except:
                    pass
                
                # Verify FileLogger was called (for Modal environment)
                mock_file.assert_called_once()
                mock_stdout.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 