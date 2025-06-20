import modal
import uuid
from datetime import datetime
import io

# Create Modal app with FastAPI image
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "python-multipart")
    .add_local_dir("templates", "/templates")
)

app = modal.App("dataset-processor", image=image)

@app.function()
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, File, UploadFile, Form
    from fastapi.responses import HTMLResponse
    import os

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
        
        # Store files in the volume
        with volume.batch_upload() as batch:
            for file in files:
                batch.put_file(io.BytesIO(file.file.read()), file.filename)
        
        print(f"Experiment context: {experiment_context}")

        return {
            "status": "uploaded",
            "session_id": session_id,
            "volume_name": volume_name,
            "file_count": len(files),
            "experiment_context": experiment_context
        }

    return web_app