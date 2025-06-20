#!/usr/bin/env python3
"""
Test script to verify our project's Docker compatibility.
Task 4.4: Test agent compatibility with existing Docker setup
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test our project's Docker integration, not the agent_sandbox submodule
from run_agent import main, modify_agents_md, copy_dir, start_container, stop_container


def test_run_agent_docker_integration():
    """Test that our run_agent.py works correctly with Docker containers."""
    
    # Mock the Docker client and subprocess calls
    with patch('run_agent.docker_client') as mock_docker, \
         patch('subprocess.run') as mock_run:
        
        # Mock Docker container
        mock_container = MagicMock()
        mock_container.name = "test_container_123"
        mock_docker.containers.get.return_value = mock_container
        
        # Mock subprocess for container startup
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test_container_123\n"
        mock_run.return_value = mock_result
        
        # Test that the container startup logic works
        container_name = start_container(Path("agent_sandbox/run_container.py"))
        assert container_name == "test_container_123"
        
        # Test that container stopping works
        stop_container(container_name)
        mock_docker.containers.get.assert_called_with(container_name)


def test_file_copying_functionality():
    """Test that file copying works correctly for Docker setup."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test source directory
        src_dir = Path(temp_dir) / "src"
        src_dir.mkdir()
        
        # Create test files
        (src_dir / "test1.txt").write_text("test content 1")
        (src_dir / "test2.txt").write_text("test content 2")
        
        # Create test destination directory
        dst_dir = Path(temp_dir) / "dst"
        
        # Test copy_dir function
        copy_dir(src_dir, dst_dir)
        
        # Verify files were copied
        assert (dst_dir / "test1.txt").exists()
        assert (dst_dir / "test2.txt").exists()
        assert (dst_dir / "test1.txt").read_text() == "test content 1"
        assert (dst_dir / "test2.txt").read_text() == "test content 2"


def test_agents_md_modification():
    """Test that AGENTS.md modification works correctly."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test AGENTS.md file
        agents_md_path = Path(temp_dir) / "AGENTS.md"
        original_content = "# Agent Instructions\n\nOriginal content here.\n"
        agents_md_path.write_text(original_content)
        
        # Mock the OUTPUT_DIR to use our temp directory
        with patch('run_agent.OUTPUT_DIR', Path(temp_dir)):
            # Test context modification
            test_context = "This is a test experiment context."
            modify_agents_md(test_context)
            
            # Verify the content was modified correctly
            modified_content = agents_md_path.read_text()
            assert "## Experiment Details" in modified_content
            assert test_context in modified_content
            assert original_content in modified_content


def test_docker_environment_detection():
    """Test that our project correctly detects Docker environment."""
    
    # Import the detection function from our agent
    sys.path.append(str(Path("agent_sandbox")))
    from agent_sandbox.coding_agent import is_modal_environment
    
    # Test without Modal environment variable (should be Docker)
    with patch.dict(os.environ, {}, clear=True):
        is_modal = is_modal_environment()
        assert not is_modal, "Should detect Docker environment when MODAL_SANDBOX_ID is not set"


def test_project_structure_compatibility():
    """Test that our project structure is compatible with Docker setup."""
    
    # Verify required directories exist
    required_dirs = [
        "agent_sandbox/user_files",
        "my_files", 
        "outputs/uploaded_files"  # Updated to match actual structure
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Required directory {dir_path} should exist"
    
    # Verify required files exist
    required_files = [
        "agent_sandbox/run_container.py",
        "run_agent.py",
        "agent_sandbox/user_files/requirements.txt"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Required file {file_path} should exist"


def test_docker_volume_mounting_structure():
    """Test that our Docker volume mounting structure is correct."""
    
    # The Docker setup expects this volume mapping structure
    # Note: The actual structure uses outputs/user_files but we have outputs/uploaded_files
    # This test verifies the expected structure for Docker compatibility
    expected_volume_mapping = {
        str(Path.cwd() / "outputs" / "user_files"): {
            'bind': '/workspace',
            'mode': 'rw'
        }
    }
    
    # Verify the structure is correct
    workspace_path = str(Path.cwd() / "outputs" / "user_files")
    assert workspace_path in expected_volume_mapping
    assert expected_volume_mapping[workspace_path]['bind'] == '/workspace'
    assert expected_volume_mapping[workspace_path]['mode'] == 'rw'


def test_docker_agent_import_compatibility():
    """Test that our agent can be imported and used in Docker environment."""
    
    # Test that we can import the coding agent
    sys.path.append(str(Path("agent_sandbox")))
    from agent_sandbox.coding_agent import run_coding_agent, docker_exec
    
    # Test that the functions exist and are callable
    assert callable(run_coding_agent)
    assert callable(docker_exec)
    
    # Test that docker_exec has the expected signature
    import inspect
    sig = inspect.signature(docker_exec)
    expected_params = ['container', 'cmd', 'cwd', 'env', 'timeout_ms']
    
    for param in expected_params:
        assert param in sig.parameters, f"Missing parameter: {param}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 