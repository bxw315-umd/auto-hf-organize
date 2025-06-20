# Task List: Modal Sandbox Migration for Experiment Processing

## Relevant Files

- `run_agent.py` - Main agent execution script to be replaced with Modal implementation
- `frontend/app.py` - Backend Flask app updated to use new Modal agent runner
- `agent_sandbox/coding_agent.py` - Agent module with Modal environment support
- `agent_sandbox/run_container.py` - Docker container script (for reference/compatibility)
- `my_files/` - Directory containing files to be copied to Modal sandbox
- `outputs/uploaded_files/` - Directory where unique user directories are created
- `modal_agent.py` - New Modal-based agent runner with copy_dir function
- `requirements.txt` - May need Modal dependency addition
- `modal_config.py` - Modal configuration (created in Task 1.0)
- `test_agent_compatibility.py` - Comprehensive tests for Docker/Modal compatibility
- `test_context_functionality.py` - Tests for context handling functionality
- `test_docker_compatibility.py` - Tests for our project's Docker compatibility

### Notes

- The implementation follows the existing Flask + Modal architecture
- Modal sandboxes will replace Docker containers for cloud-based execution
- Each user session gets its own ephemeral sandbox environment
- File management uses unique directories within outputs/uploaded_files
- Agent sandbox submodule must maintain compatibility with both Docker and Modal
- **CORRECTION**: Initially created `modal_run_agent.py` with incorrect mounting approach - should create `modal_agent.py` with proper sandbox structure

## Tasks

- [x] 1.0 Modal Infrastructure Setup
  - [x] 1.1 Add Modal dependency to requirements.txt
  - [x] 1.2 Create Modal app configuration and initialization
  - [x] 1.3 Set up Modal authentication and environment variables
  - [x] 1.4 Create base Modal image configuration
- [x] 2.0 File Management and Preparation
  - [x] 2.1 Modify file preparation logic to copy my_files to unique directory
  - [x] 2.2 Update directory structure to work with Modal mounting
  - [x] 2.3 Implement file copying from my_files to unique user directory
  - [x] 2.4 Ensure proper file permissions and structure for Modal sandbox
- [x] 3.0 Modal Agent Runner Implementation
  - [x] 3.1 Create modal_agent.py with basic Modal sandbox structure
  - [x] 3.2 Implement ephemeral volume creation and management
  - [x] 3.3 Add Modal image creation with local directory mounting
  - [x] 3.4 Implement sandbox creation and agent execution logic
  - [x] 3.5 Add output download from ephemeral volume
  - [x] 3.6 Implement error handling for sandbox failures and timeouts
  - [x] 3.7 Add file size validation (>5MB limit)
- [x] 4.0 Agent Sandbox Compatibility Layer
  - [x] 4.1 Add Modal environment detection to coding_agent.py
  - [x] 4.2 Implement conditional logging based on environment
  - [x] 4.3 Ensure agent works in both Docker and Modal environments
  - [x] 4.4 Test agent compatibility with existing Docker setup
- [ ] 5.0 Frontend Integration and Testing
  - [x] 5.1 Update frontend/app.py to use new modal_agent.py
  - [ ] 5.2 Ensure real-time logging continues to work with Modal
  - [ ] 5.3 Test complete user workflow from upload to download
  - [ ] 5.4 Verify concurrent user processing works correctly
  - [ ] 5.5 Test error scenarios and edge cases
  - [ ] 5.6 Remove or deprecate old run_agent.py 