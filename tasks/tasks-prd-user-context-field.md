# Task List: User Context Field for Experiment Processing

## Relevant Files

- `frontend/templates/index.html` - Contains the main upload form where the textarea will be added
- `frontend/app.py` - Backend Flask app that handles file uploads and needs to receive context
- `run_agent.py` - Main agent execution script that needs to process and integrate user context
- `my_files/AGENTS.md` - Template file that will be modified with user context. This file is read-only.
- `outputs/user_files/AGENTS.md` - Target file where user context will be appended

### Notes

- The implementation follows the existing Flask + HTML/JavaScript architecture
- User context will be appended as a new "Experiment Details" section in markdown format
- Error handling should fail gracefully if AGENTS.md modification fails
- No special handling needed for empty context strings

## Tasks

- [x] 1.0 Frontend UI Implementation
  - [x] 1.1 Add textarea element to the upload form in index.html
  - [x] 1.2 Style the textarea to match existing form elements
  - [x] 1.3 Add placeholder text prompting users to describe their experiment
  - [x] 1.4 Update JavaScript to capture textarea content in form submission
  - [x] 1.5 Include context in FormData sent to backend
  - [x] 1.6 Ensure textarea is positioned between file selection and upload button
- [ ] 2.0 Backend Context Handling
  - [ ] 2.1 Modify upload endpoint in app.py to receive context parameter
  - [ ] 2.2 Update process_dataset function to accept and pass context
  - [ ] 2.3 Ensure context is properly extracted from request data
  - [ ] 2.4 Handle cases where context is empty or not provided (ideally no code changes)
- [ ] 3.0 AGENTS.md Integration
  - [ ] 3.1 Modify run_agent.py to accept optional context parameter
  - [ ] 3.2 Implement logic to append user context as "Experiment Details" section within the sandbox (outputs/user_files)
  - [ ] 3.3 Ensure AGENTS.md modification happens before agent execution
  - [ ] 3.4 Preserve original AGENTS.md structure and content
- [ ] 4.0 Error Handling and Validation
  - [ ] 4.1 Add error handling for AGENTS.md file operations
  - [ ] 4.2 Implement graceful failure if AGENTS.md modification fails
  - [ ] 4.3 Add validation to ensure context is properly received
  - [ ] 4.4 Handle edge cases where AGENTS.md doesn't exist in outputs/user_files
- [ ] 5.0 Testing and Integration
  - [ ] 5.1 Test textarea functionality with various input lengths
  - [ ] 5.2 Verify context is properly captured and sent to backend
  - [ ] 5.3 Test AGENTS.md modification with different context content
  - [ ] 5.4 Verify agent execution works correctly with modified AGENTS.md
  - [ ] 5.5 Test error scenarios and edge cases
  - [ ] 5.6 Ensure existing functionality remains unchanged 