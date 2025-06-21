# Automated Dataset Processing System

## The Problem

Experimental datasets, especially from electrochemical instruments like CHI potentiostats, often come as scattered raw files with inconsistent naming and formats. Converting these into machine learning-ready datasets requires:

- **Manual file parsing** of `.txt` and `.bin` files
- **Metadata extraction** from complex filenames (concentrations, sample IDs, experimenters, etc.)
- **Data standardization** into consistent formats
- **Hugging Face dataset creation** with proper column naming and structure

This process is time-consuming, error-prone, and requires domain expertise for each new dataset.

## The Solution

This system automates the entire dataset processing pipeline using AI agents:

1. **Upload raw files** through a simple web interface
2. **AI agent automatically**:
   - Parses CHI potentiostat `.txt` files
   - Extracts metadata from filenames (concentrations, sample IDs, etc.)
   - Organizes data into structured Hugging Face format
   - Creates standardized datasets ready for ML workflows
3. **Download processed dataset** as a complete, organized package

The system runs in the cloud using Modal, providing scalable processing without local computational requirements.

## 🚀 Quick Start

### Deploy the Web Endpoint
```bash
modal deploy modal_webendpoint/modal_webendpoint.py
```

This deploys the FastAPI web application that provides:
- File upload interface
- Real-time processing logs via Server-Sent Events
- Download functionality for processed datasets

## 📋 How It Works

### For Researchers
1. **Upload**: Drag and drop your experimental files (`.txt` files from CHI potentiostats)
2. **Add Context**: Optionally provide experiment notes or context
3. **Monitor**: Watch real-time logs as the AI processes your data
4. **Download**: Get your organized Hugging Face dataset as a ZIP file

### Expected Input Format
The system processes CHI potentiostat files with descriptive names like:
```
250616_Pprot382int_2007B_1uM_AI1_S10_EricMM_GCE_DPV.txt
```

Where:
- `250616` = Date (June 25, 2024)
- `Pprot382int_2007B` = Protein/molecule identifier
- `1uM` = Concentration
- `AI1` = Molecule name
- `S10` = Sample number
- `EricMM` = Experimenter
- `GCE_DPV` = Electrode type and technique

### Output Format
The system generates Hugging Face datasets with:
- **`potential`** - Voltage/potential values
- **`current`** - Current values  
- **Concentration columns** - Molecule concentrations (e.g., `ai1` for AI-1 concentration)
- **Metadata** - Extracted from filenames and user context

## 🛠️ Setup & Dependencies

### Prerequisites
- Modal CLI installed and authenticated
- OpenAI API key configured in Modal secrets (`openai-secret`)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up Modal secrets (if not already done)
modal secret create openai-secret OPENAI_API_KEY=your_api_key_here
```

## 📁 Project Structure

```
├── modal_webendpoint/           # Web application
│   ├── modal_webendpoint.py    # Main FastAPI app
│   ├── templates/              # HTML templates
│   └── requirements.txt        # Web app dependencies
├── agent_sandbox/              # AI agent environment
│   ├── coding_agent.py         # Main agent logic
│   ├── tools/                  # Agent tools
│   └── user_files/             # Agent dependencies
├── modal_agent.py              # Modal function orchestrator
├── modal_shared_app.py         # Shared Modal configuration
├── my_files/                   # Processing instructions & utilities
│   ├── AGENTS.md               # Dataset processing guidelines
│   └── chi_txt_parser.py       # CHI potentiostat file parser
├── test_files/                 # Sample data for testing
└── requirements.txt            # Main project dependencies
```

## 🏗️ Architecture

### Core Components

- **`modal_webendpoint/`** - FastAPI web application for file uploads and real-time monitoring
- **`modal_agent.py`** - Modal function that orchestrates the AI agent execution
- **`agent_sandbox/`** - Isolated development environment for the AI agent
- **`modal_shared_app.py`** - Shared Modal app configuration
- **`my_files/`** - Contains `AGENTS.md` with processing instructions and `chi_txt_parser.py` for data parsing

### Data Flow

1. **Upload**: Users upload experimental files via web interface
2. **Volume Creation**: Files are stored in Modal volumes with session-specific naming
3. **Agent Execution**: AI agent runs in isolated Modal sandbox with access to uploaded files
4. **Processing**: Agent parses files, extracts metadata, and organizes into HF dataset format
5. **Output**: Processed dataset saved as `dataset_hf/` directory in the volume
6. **Download**: Users can download the processed dataset as a ZIP file

## 🔍 Testing

### Test Agent Compatibility
```bash
python test_agent_compatibility.py
```

### Test Modal Logging
```bash
python test_modal_logging.py
```

### Local Development
```bash
# Run the web endpoint locally
cd frontend
python app.py
```

## 📝 Configuration

### Modal Secrets
- `openai-secret` - OpenAI API key for AI agent functionality

### Environment Variables
- Processing timeouts and retry settings in `modal_agent.py`
- Volume naming conventions and session management

## 🚨 Troubleshooting

### Common Issues
1. **Timeout errors**: Increase timeout values in `modal_agent.py` for large datasets
2. **Volume not found**: Ensure proper session ID generation and volume naming
3. **Agent failures**: Check OpenAI API key and quota limits
4. **File parsing errors**: Verify file format matches CHI potentiostat `.txt` format

### Debug Mode
Enable detailed logging by modifying the logging configuration in `modal_agent.py`:
```python
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
```

## 🔄 Development Workflow

1. **Local Testing**: Use `test_files/` for development and testing
2. **Agent Development**: Modify `agent_sandbox/coding_agent.py` for new processing logic
3. **Web Interface**: Update `modal_webendpoint/templates/` for UI changes
4. **Deployment**: Use `modal deploy` for production updates

## 📊 Monitoring

The system provides real-time monitoring through:
- **Server-Sent Events** for live log streaming
- **Modal Queue** for cross-function communication
- **Session-based processing** with unique identifiers
- **Volume persistence** for data storage across function calls

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with sample data in `test_files/`
4. Submit a pull request with detailed description

---

**Note**: This system is designed for processing voltammetry data from CHI potentiostats. For other data types, add parsing logic to `my_files` and update the agent instructions in `my_files/AGENTS.md`. 