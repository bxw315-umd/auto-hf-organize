import modal
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
import os
import zipfile
import io
from pathlib import Path

# Create Modal app with FastAPI image
image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "python-multipart")
)

volume = modal.Volume.from_name("dataset-volume-20250621_011346_cc9ea6a4")

app = modal.App("prototype-download-endpoint", image=image, volumes={"/workspace": volume})

@app.function()
@modal.asgi_app()
def fastapi_app():
    web_app = FastAPI()

    @web_app.get("/")
    async def index():
        # Simple HTML page with download button
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download Prototype</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .download-btn { 
                    background: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 16px;
                }
                .download-btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h1>Dataset Download Prototype</h1>
            <p>Click the button below to download the dataset:</p>
            <button class="download-btn" onclick="downloadDataset()">Download Dataset</button>
            <div id="status"></div>
            
            <script>
                function downloadDataset() {
                    const status = document.getElementById('status');
                    status.textContent = 'Starting download...';
                    
                    // Create a temporary link element to trigger download
                    const link = document.createElement('a');
                    link.href = '/download';
                    link.download = 'dataset_hf.zip';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    status.textContent = 'Download started!';
                }
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    @web_app.get("/download")
    async def download():
        """Download the dataset_hf directory as a zip file"""
        try:
            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Path to the dataset_hf directory within the volume
                volume_path = "/workspace"
                dataset_hf_path = os.path.join(volume_path, "dataset_hf")
                
                if not os.path.exists(dataset_hf_path):
                    raise HTTPException(status_code=404, detail="dataset_hf directory not found")
                
                # Walk through the dataset_hf directory and add all files
                for root, dirs, files in os.walk(dataset_hf_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Get relative path from dataset_hf directory
                        relative_path = os.path.relpath(file_path, dataset_hf_path)
                        # Add file to zip
                        zip_file.write(file_path, relative_path)
            
            # Reset buffer position
            zip_buffer.seek(0)
            
            # Return the zip file as a streaming response
            return StreamingResponse(
                io.BytesIO(zip_buffer.getvalue()),
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=dataset_hf.zip"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    @web_app.get("/list")
    async def list_files():
        """List all files in the dataset_hf directory for debugging"""
        try:
            volume_path = "/workspace"
            dataset_hf_path = os.path.join(volume_path, "dataset_hf")
            
            if not os.path.exists(dataset_hf_path):
                return {"error": "dataset_hf directory not found", "path": dataset_hf_path}
            
            files = []
            for root, dirs, filenames in os.walk(dataset_hf_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, dataset_hf_path)
                    files.append({
                        "path": relative_path,
                        "size": os.path.getsize(file_path)
                    })
            
            return {
                "dataset_hf_path": dataset_hf_path,
                "total_files": len(files),
                "files": files
            }
            
        except Exception as e:
            return {"error": str(e)}

    return web_app 