import modal
import uuid
from datetime import datetime
import io

# Create Modal app with FastAPI image
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "python-multipart", "openai")
    .add_local_dir("templates", "/templates")
    .add_local_dir("../my_files", "/my_files")
)

app = modal.App("dataset-processor-web-app", image=image)

@app.function()
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, File, UploadFile, Form
    from fastapi.responses import HTMLResponse

    web_app = FastAPI()

    @web_app.get("/")
    async def index():
        with open("/templates/index.html", "r") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    @web_app.post("/upload")
    async def upload(
        files: list[UploadFile] = File(...),
        experiment_context: str = Form("")
    ):
        # Generate unique session ID for volume naming
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(uuid.uuid4())[:8]
        volume_name = f"dataset-volume-{session_id}"
        
        print(f"Uploading {len(files)} files for session {session_id}")
        print(f"Creating volume: {volume_name}")
        
        # Create Modal volume
        volume = modal.Volume.from_name(volume_name, create_if_missing=True)
        
        with volume.batch_upload() as batch:
            # Store files in the volume
            for file in files:
                batch.put_file(io.BytesIO(file.file.read()), file.filename)
        
            # Additionally, copy over the files from my_files
            batch.put_directory("/my_files", "/")

        
        print(f"Experiment context: {experiment_context}")

        # Call run_coding_agent with the uploaded files and experiment context
        request = f"Process the uploaded dataset files. Experiment context: {experiment_context}"
        
        # Get the current endpoint URL for logging
        # This will be the Modal endpoint URL + /log
        endpoint_url = "https://mariotu4--dataset-processor-web-app-fastapi-app-dev.modal.run/log"  # This will be replaced with actual Modal URL
        
        print(f"Starting coding agent with endpoint_url: {endpoint_url}")

        try:
            run_agent_func = modal.Function.from_name("dataset-processor-agent", "run_agent_remotely")
            result = run_agent_func.remote(
                session_id=session_id,
                context=experiment_context,
                logger_str="http",
                endpoint_url=endpoint_url
            )
            print(f"Coding agent completed successfully: {result}")
        except Exception as e:
            print(f"Error running coding agent: {e}")
            result = f"Error: {str(e)}"

        return {
            "status": "uploaded",
            "session_id": session_id,
            "volume_name": volume_name,
            "file_count": len(files),
            "experiment_context": experiment_context,
            "agent_result": result
        }
    
    @web_app.post("/log")
    async def log(log_entry: dict):
        print(f"Log entry: {log_entry}")
        return {"message": "Log endpoint called"}

    return web_app