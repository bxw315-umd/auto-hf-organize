# Product Requirements Document: User Context Field for Experiment Processing

## Introduction/Overview

Currently, the experiment dataset processing app uses generic prompts and AGENTS.md files that don't account for user-specific context about their experiments. This can lead to incorrect assumptions by the coding agent (e.g., interpreting "eric_mm" as a person's name rather than "Eric minimal media"). 

This feature adds a textarea field where users can provide experiment-specific context that will be appended to the AGENTS.md file before processing, allowing the coding agent to make more accurate interpretations of the data.

## Goals

1. **Improve Agent Accuracy**: Provide the coding agent with user-specific context to reduce misinterpretations of file names and data
2. **Enhanced User Control**: Give users the ability to specify important details about their experiment that aren't obvious from file names alone
3. **Seamless Integration**: Integrate user context into the existing workflow without disrupting the current upload and processing flow
4. **Optional Feature**: Maintain the current functionality for users who don't need to provide additional context

## User Stories

1. **As a researcher**, I want to provide context about my experiment so that the coding agent correctly interprets file names and data structures
2. **As a user**, I want to optionally add experiment details without being forced to provide context if I don't need it
3. **As a user**, I want to see a clear text area where I can describe my experiment before uploading my dataset
4. **As a user**, I want my context to be automatically included in the agent's instructions so I don't have to manually modify files

## Functional Requirements

1. **Context Input Field**: The system must display a textarea field between the file selection and upload button
2. **Textarea Specifications**: The textarea must be static-sized with vertical scrolling for overflow content
3. **Placeholder Text**: The textarea must display helpful placeholder text prompting users to describe their experiment
4. **Optional Field**: The context field must be optional - users can submit empty content
5. **Context Capture**: The system must capture the textarea content when the upload button is clicked
6. **AGENTS.md Integration**: The system must append the user context as a new section at the end of AGENTS.md before running the agent
7. **Empty Context Handling**: The system must handle empty context gracefully by appending an empty string. But this, in theory, should not require any special handling.
8. **No Post-Upload Editing**: Users must not be able to modify context after upload begins

## Non-Goals (Out of Scope)

1. **Character Limits**: No validation or limits on context length
2. **Context Persistence**: No saving or displaying context after processing
3. **Context Editing**: No ability to edit context after upload
4. **Rich Text Formatting**: No formatting options beyond plain text
5. **Context Examples**: No built-in examples or help text beyond placeholder
6. **Context Validation**: No validation of context content or quality
7. **Context in Dataset**: No inclusion of context in final dataset metadata
8. **Collapsible UI**: No expandable/collapsible context field

## Design Considerations

### UI Layout
- Add textarea between file selection input and upload button
- Use consistent styling with existing form elements
- Maintain current form layout and spacing
- Textarea should be visually distinct but not overwhelming

### Placeholder Text
- Clear, concise prompt explaining what context to provide
- Example: "Describe your experiment, including any important details about file naming conventions, experimental conditions, or data structure that might not be obvious from file names alone."

### Textarea Specifications
- Fixed height with vertical scroll for overflow
- Consistent width with other form elements
- Standard textarea styling matching the app's design system

## Technical Considerations

### Frontend Changes
- Modify `frontend/templates/index.html` to add textarea element
- Update JavaScript to capture textarea content in form submission
- Include context in FormData sent to backend

### Backend Changes
- Modify `frontend/app.py` to receive context from frontend
- Update `run_agent.py` to accept and process context parameter
- Implement AGENTS.md modification logic to append user context

### File Modification
- Read existing AGENTS.md content
- Append user context as new section
- Preserve original AGENTS.md structure
- Handle cases where AGENTS.md doesn't exist (should raise error)

## Success Metrics

1. **User Adoption**: At least 50% of users provide context when the feature is available
2. **Agent Accuracy**: Reduction in misinterpretations of file names and data structures
3. **User Satisfaction**: Positive feedback about the ability to provide experiment context
4. **System Stability**: No degradation in processing speed or reliability
5. **Error Reduction**: Fewer cases where users need to manually correct agent interpretations

## Open Questions

1. **Context Section Title**: What should the new section in AGENTS.md be called? (e.g., "User Context", "Experiment Details", "Additional Information") | Answer: Experiment Details
2. **Context Formatting**: Should the context be formatted in any specific way when appended to AGENTS.md? (e.g., markdown formatting, plain text) | answer: markdown
3. **Context Length Guidelines**: Should we provide any guidance on recommended context length in the placeholder text? | Answer: no
4. **Error Handling**: What should happen if AGENTS.md modification fails? Should processing continue without context or fail gracefully? | Answer: fail

## Implementation Priority

**High Priority**: Core textarea and context capture functionality
**Medium Priority**: AGENTS.md integration and backend processing
**Low Priority**: UI polish and placeholder text refinement 