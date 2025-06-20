# PRD: Modal Web Endpoint Migration

## Introduction/Overview

This feature migrates the existing Flask-based file upload and processing application to a Modal web endpoint. The goal is to serve the application from the cloud rather than locally while maintaining all existing functionality including real-time streaming logs, file uploads, and dataset processing with Modal agents.

## Goals

1. **Cloud Deployment**: Replace local Flask server with Modal web endpoint for cloud-based access
2. **Feature Parity**: Maintain all existing functionality including real-time streaming, file uploads, and experiment context processing
3. **Volume Management**: Implement unique volume naming for uploaded files using session IDs
4. **Remote Agent Execution**: Integrate with `run_agent_remotely` function using web server logging
5. **Zero Downtime**: Ensure seamless transition from Flask app to Modal endpoint

## User Stories

1. **As a researcher**, I want to upload my dataset files through a web interface so that I can process them remotely without running local servers.

2. **As a user**, I want to see real-time processing logs so that I can monitor the progress of my dataset analysis.

3. **As a user**, I want to provide experiment context with my uploads so that the processing agent has the necessary information to analyze my data.

4. **As a user**, I want my uploaded files to be stored in a unique, isolated volume so that my data remains separate from other users' data.

5. **As a user**, I want the processing to fail gracefully if something goes wrong so that I understand what happened and can retry if needed.

## Functional Requirements

1. **Web Interface**: The system must provide a web interface identical to the current Flask app's `/` route.

2. **File Upload**: The system must accept file uploads via POST to `/upload` endpoint with the same functionality as the current Flask app.

3. **Experiment Context**: The system must accept and validate experiment context from form data, maintaining the same validation logic as the current implementation.

4. **Volume Creation**: The system must create a unique Modal volume for each upload session using the format `dataset-volume-{session_id}`.

5. **File Storage**: The system must store uploaded files in the unique volume while preserving directory structure.

6. **Agent Execution**: The system must call `run_agent_remotely` with the volume path and experiment context.

7. **Real-time Logging**: The system must stream logs in real-time via Server-Sent Events (SSE) to `/stream` endpoint.

8. **HTTP Logging**: The system must configure the agent to use HTTP logging with the Modal endpoint URL instead of hardcoded localhost.

9. **Background Processing**: The system must process uploads in background threads to avoid blocking the web interface.

10. **Error Handling**: The system must handle processing failures gracefully and communicate errors to the user interface.

11. **Volume Persistence**: The system must not automatically clean up volumes after processing completion.

## Non-Goals (Out of Scope)

1. **Authentication/Authorization**: No user authentication or authorization mechanisms
2. **Rate Limiting**: No usage quotas or rate limiting
3. **File Size Limits**: No additional file size restrictions beyond Modal's inherent limits
4. **Log Persistence**: Logs are not saved permanently, only transmitted during processing
5. **Volume Management UI**: No interface for managing, listing, or deleting volumes
6. **Monitoring/Alerts**: No additional monitoring or alerting capabilities
7. **Multi-tenancy**: No user isolation beyond volume separation
8. **Retry Mechanisms**: No automatic retry functionality for failed uploads

## Design Considerations

- **UI Consistency**: Maintain exact same HTML templates and JavaScript functionality as current Flask app
- **Real-time Updates**: Preserve Server-Sent Events implementation for live log streaming
- **Responsive Design**: Ensure the web interface works across different devices and screen sizes
- **Error Display**: Provide clear error messages in the web interface when processing fails

## Technical Considerations

1. **Modal Integration**: Must integrate with Modal's web endpoint framework and volume management
2. **HTTP Logging**: Replace hardcoded `http://localhost:8000/log` with dynamic Modal endpoint URL
3. **File Handling**: Adapt file upload handling to work with Modal's file system and volume mounting
4. **Background Processing**: Implement proper background task handling within Modal's execution environment
5. **Session Management**: Generate and manage unique session IDs for volume naming
6. **Error Propagation**: Ensure errors from `run_agent_remotely` are properly communicated to the web interface

## Success Metrics

1. **Functional Parity**: 100% feature compatibility with existing Flask app
2. **Uptime**: 99%+ availability for the web endpoint
3. **Processing Success**: 95%+ successful processing of uploaded datasets
4. **User Experience**: No degradation in real-time log streaming performance
5. **Volume Isolation**: Zero data leakage between different user sessions

## Open Questions

1. **Endpoint URL Configuration**: How should the Modal endpoint URL be dynamically determined for HTTP logging?
2. **Volume Cleanup Strategy**: While not automatic, should there be a manual cleanup process for old volumes?
3. **Error Recovery**: What specific error conditions should trigger graceful failure handling?
4. **Session ID Generation**: Should session IDs be UUID-based or follow a different naming convention?
5. **Deployment Environment**: Are there specific Modal deployment settings or configurations needed?

## Implementation Notes

- The Modal endpoint should replace the current `app.run()` with Modal's web endpoint decorator
- File upload handling needs to be adapted to work with Modal's volume mounting system
- The `run_agent_remotely` function should be called with the volume path and proper logging configuration
- Real-time streaming should be implemented using Modal's web endpoint streaming capabilities
- Error handling should be consistent with the current Flask implementation patterns 