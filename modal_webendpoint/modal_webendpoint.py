import modal
import uuid
from datetime import datetime
import io
import json
import asyncio
import os
import zipfile
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import run_in_threadpool
from queue import Empty
import modal_shared_app
from modal_agent import run_agent_remotely

# Create Modal app with FastAPI image
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "python-multipart", "openai", "sse-starlette")
    .add_local_dir("modal_webendpoint/templates", "/templates")
    .add_local_dir("my_files", "/my_files")
    .add_local_python_source("modal_shared_app", "modal_agent")
)

app = modal_shared_app.app

# Use a Modal Queue for logs, accessible across functions.
log_queue = modal.Queue.from_name("dataset-processor-log-queue", create_if_missing=True)

@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
    from fastapi.responses import HTMLResponse, StreamingResponse

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
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + str(uuid.uuid4())[:8]
        volume_name = f"dataset-volume-{session_id}"
        
        print(f"Uploading {len(files)} files for session {session_id}")
        print(f"Creating volume: {volume_name}")
        
        volume = modal.Volume.from_name(volume_name, create_if_missing=True)
        
        with volume.batch_upload() as batch:
            for file in files:
                batch.put_file(io.BytesIO(file.file.read()), file.filename)
            batch.put_directory("/my_files", "/")
        
        print(f"Experiment context: {experiment_context}")

        base_url = "https://mariotu4--dataset-processor-agent-fastapi-app.modal.run/"
        endpoint_url = f"{base_url}/log"
        print(f"Starting coding agent with endpoint_url: {endpoint_url}")

        # Run the agent in the background
        run_agent_func = run_agent_remotely
        run_agent_func.spawn(
            session_id=session_id,
            context=experiment_context,
            logger_str="http",
            endpoint_url=endpoint_url
        )

        # The agent now runs in the background. The logs will be sent to /log
        # and streamed to the client via /stream. The upload endpoint can return immediately.
        return {
            "status": "processing_started",
            "session_id": session_id,
            "volume_name": volume_name,
            "file_count": len(files)
        }
    
    @web_app.post("/log")
    async def log(log_entry: dict):
        # The agent sends logs here
        log_queue.put(log_entry)
        return {"message": "Log received"}

    @web_app.get("/stream")
    async def stream(request: Request):
        def get_log():
            try:
                return log_queue.get(timeout=10)
            except Empty:
                return {"type": "keepalive"}
            except Exception as e:
                print(f"Error getting log: {e}")
                # don't keep alive if there's an error
                return None

        async def generator():
            while True:
                if await request.is_disconnected():
                    break
                entry = await run_in_threadpool(get_log)
                yield {"data": json.dumps(entry)}
        return EventSourceResponse(generator())

    @web_app.get("/download/{volume_name}")
    async def download(volume_name: str):
        """Download the dataset_hf directory from a specific volume as a zip file"""
        try:
            zip_buffer = io.BytesIO()
            volume = modal.Volume.from_name(volume_name)

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                try:
                    # Iterate recursively through the dataset_hf directory
                    for entry in volume.iterdir("dataset_hf", recursive=True):
                        # Add only files to the zip archive
                        if entry.type == modal.volume.FileEntryType.FILE:
                            # entry.path is the full path from the volume root, e.g., "dataset_hf/data/file.txt"
                            # We want the path inside the zip to be relative to "dataset_hf", e.g., "data/file.txt"
                            relative_path = os.path.relpath(entry.path, "dataset_hf")
                            
                            # Read the file content and write it to the zip file
                            content = b"".join(volume.read_file(entry.path))
                            zip_file.writestr(relative_path, content)

                except FileNotFoundError:
                    raise HTTPException(
                        status_code=404, detail="dataset_hf directory not found in volume"
                    )

            zip_buffer.seek(0)
            return StreamingResponse(
                io.BytesIO(zip_buffer.getvalue()),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=dataset_hf.zip"
                },
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    return web_app