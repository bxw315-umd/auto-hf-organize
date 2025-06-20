# Product Requirements Document: Modal Sandbox Migration for Experiment Processing

## Introduction/Overview

Currently, the experiment dataset processing app uses local Docker containers to run the coding agent in an isolated environment. This approach has limitations in a web server environment where multiple concurrent users need to process datasets simultaneously. The system needs to migrate to Modal sandboxes, which provide cloud-based, scalable, and isolated execution environments.

This migration will replace the Docker container approach with Modal sandboxes while maintaining compatibility with the existing `agent_sandbox` submodule, which must support both Docker and Modal environments for flexibility across different projects.

## Goals

1. **Scalability**: Enable concurrent processing of multiple user datasets without resource conflicts
2. **Cloud-Based Execution**: Move from local Docker containers to cloud-based Modal sandboxes
3. **Maintain Compatibility**: Ensure `agent_sandbox` submodule works with both Docker and Modal environments
4. **Simplified File Management**: Eliminate the need for shared `outputs/user_files` directory
5. **Improved Isolation**: Each user session gets its own ephemeral sandbox environment
6. **Real-Time Logging**: Maintain real-time streaming of agent execution logs to the frontend

## User Stories

1. **As a user**, I want to upload my dataset and have it processed in a cloud environment so that I don't have to wait for other users' processing to complete
2. **As a developer**, I want the system to handle multiple concurrent users without resource conflicts
3. **As a user**, I want to see real-time progress of my dataset processing in the web interface
4. **As a developer**, I want the `agent_sandbox` submodule to work with both Docker and Modal environments for maximum flexibility
5. **As a user**, I want my processing results to be reliably downloaded and available after completion

## Functional Requirements

1. **Modal Sandbox Integration**: Replace `run_agent.py` with Modal sandbox implementation
2. **File Preparation**: Copy uploaded files and `my_files` content to a unique directory within `outputs/uploaded_files`. The unique directory is already created during file upload from the frontend.
3. **Image Creation**: Create Modal image with the prepared directory mounted as `/workspace`
4. **Ephemeral Volume**: Use ephemeral volumes for output storage with automatic cleanup
5. **Agent Execution**: Execute the coding agent within the Modal sandbox environment
6. **Logging Integration**: Modify agent logging to work with Modal's streaming capabilities
7. **Output Download**: Download results from ephemeral volume to local `outputs` directory
8. **Error Handling**: Handle sandbox failures, timeouts, and large output files (>5MB)
9. **Compatibility Layer**: Ensure `agent_sandbox` supports both Docker and Modal environments

## Non-Goals (Out of Scope)

1. **Cost Optimization**: No implementation of sandbox pooling or cost optimization features
2. **Persistent Volumes**: No persistent volume storage for this implementation
3. **Backward Compatibility**: No maintenance of Docker container approach in this project
4. **Requirements.txt Copying**: No need to copy requirements.txt as it's handled during sandbox creation
5. **Multiple Environment Support**: No support for multiple Modal environments or configurations

## Design Considerations

### File Structure Changes
- Eliminate `outputs/user_files` directory
- Use unique subdirectories within `outputs/uploaded_files` for each session
- Mount the unique directory directly to Modal sandbox as `/workspace`

### Modal App Configuration
- Use "sandbox-environment" as the Modal App name (following minimal example)
- Create custom Modal image with local directory mounting
- Use ephemeral volumes for output storage

### Agent Integration
- Minimal changes to `agent_sandbox/coding_agent.py` to support Modal environment
- Add Modal-specific logging capabilities
- Maintain existing agent functionality and command structure

### Error Handling
- Implement proper error handling for sandbox creation failures
- Handle timeout scenarios gracefully
- Validate output file size before download
- Automatic cleanup through Modal context managers

## Technical Considerations

### Frontend Changes
- No changes required to the frontend upload interface
- Maintain existing SSE streaming for real-time updates
- Preserve current user experience and UI

### Backend Changes
- Replace `run_agent.py` with Modal-based implementation
- Update `frontend/app.py` to use new Modal agent runner
- Modify file preparation logic to work with unique directories

### Agent Sandbox Compatibility
- Add Modal environment detection in `agent_sandbox`
- Implement conditional logging based on environment
- Maintain Docker compatibility for other projects using the submodule

### File Management
- Prepare unique directory: `outputs/uploaded_files/{unique_id}/` (but this is already done by the flask app)
- Copy uploaded files to unique directory
- Copy `my_files` contents to unique directory
- Mount entire unique directory to Modal sandbox

## Success Metrics

1. **Concurrency**: System can handle multiple concurrent users without conflicts
2. **Performance**: Processing time remains comparable to Docker approach
3. **Reliability**: Successful processing rate >95% with proper error handling
4. **User Experience**: Real-time logging continues to work seamlessly
5. **Compatibility**: `agent_sandbox` submodule works in both Docker and Modal environments

## Open Questions

1. **Modal App Naming**: Should we use "sandbox-environment" or a more specific name like "experiment-processing"?
2. **Image Optimization**: Should we use a specific base image or stick with `debian_slim`?
3. **Timeout Configuration**: What should be the default timeout for sandbox execution?
4. **Error Recovery**: Should we implement retry logic for failed sandbox operations?
5. **Logging Format**: Should we maintain the exact same log format or adapt to Modal's logging style?

## Implementation Priority

**High Priority**: Core Modal sandbox integration and file management
**Medium Priority**: Agent compatibility layer and logging integration
**Low Priority**: Error handling improvements and optimization 