#!/usr/bin/env python3
"""
Modal-based agent runner for experiment processing.
Replaces Docker containers with Modal sandboxes for cloud-based execution.
"""

import modal
import logging
from pathlib import Path
import os
import time
import subprocess
import sys
import shutil

# Configure logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
AGENT_COMMAND = (
    "I've provided you with the raw data files for an experiment. "
    "Please take the dataset and organize it into a huggingface dataset, complete "
    "with metadata columns inferred from the file names. Refer to AGENTS.md for more details. "
    "All files you generate should be saved in the `/output` directory."
    "Save the dataset to disk as `/output/dataset_hf`."
)

def copy_dir(src: Path, dst: Path):
    """Recursively copy contents from src into dst."""
    if not src.exists():
        logger.warning(f"Source directory not found: {src}")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        target = dst / entry.name
        try:
            if entry.is_dir():
                shutil.copytree(entry, target, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, target)
            logger.info(f"Copied {entry} to {target}")
        except Exception as e:
            logger.error(f"Failed to copy {entry}: {e}")
            raise

def modify_agents_md(context: str, session_dir: Path):
    """Append user context to AGENTS.md in the session directory."""
    agents_md_path = session_dir / "AGENTS.md"
    
    if not isinstance(context, str):
        logger.error(f"Invalid context type: {type(context)}, expected string")
        raise ValueError(f"Context must be a string, got {type(context)}")
    
    if not agents_md_path.exists():
        logger.error(f"AGENTS.md not found at {agents_md_path}")
        raise FileNotFoundError(f"AGENTS.md not found at {agents_md_path}")
    
    try:
        with open(agents_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        context_section = f"\n\n## Experiment Details\n\n{context}\n"
        updated_content = content + context_section
        
        with open(agents_md_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"    Added user context to AGENTS.md in {session_dir}")
    except Exception as e:
        logger.error(f"Failed to modify AGENTS.md in {session_dir}: {e}")
        raise

def get_directory_size(directory: Path) -> int:
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        logger.warning(f"Error calculating directory size: {e}")
    return total_size

def validate_file_size(session_dir: Path, max_size_mb: int = 5) -> bool:
    """Validate that the session directory doesn't exceed the maximum size limit.
    
    Args:
        session_dir: Path to the session directory
        max_size_mb: Maximum size in megabytes (default: 5MB)
    
    Returns:
        True if validation passes, False otherwise
    """
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    
    try:
        total_size = get_directory_size(session_dir)
        size_mb = total_size / (1024 * 1024)
        
        logger.info(f"Session directory size: {size_mb:.2f} MB")
        
        if total_size > max_size_bytes:
            logger.error(f"Session directory size ({size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)")
            return False
        
        logger.info(f"File size validation passed ({size_mb:.2f} MB <= {max_size_mb} MB)")
        return True
        
    except Exception as e:
        logger.error(f"Error during file size validation: {e}")
        return False

def run_agent_in_sandbox(session_dir_str: str, context: str = "", logger: str = "stdout"):
    """
    Runs the coding agent with a Modal sandbox.
    Args:
        session_dir_str: Path to the session directory containing user files
        context: Optional user context to append to AGENTS.md
        logger: Logger type to use ('stdout', 'file', 'http', etc.)
    """
    session_dir = Path(session_dir_str)
    
    logger_module = logging.getLogger(__name__)
    logger_module.info("Starting Modal sandbox agent execution...")
    
    # Validate file size before proceeding
    logger_module.info(">>> [0] Validating file size...")
    if not validate_file_size(session_dir):
        raise ValueError(f"Session directory size exceeds the 5MB limit")
    
    # Create/lookup Modal App
    logger_module.info("Creating/looking up Modal App...")
    app = modal.App.lookup("sandbox-environment", create_if_missing=True)
    
    # Create custom image
    logger_module.info("Creating custom image...")
    image = (
        modal.Image.debian_slim()
        .apt_install("ripgrep", "ed")  # Install ripgrep and ed
        .pip_install_from_requirements("agent_sandbox/user_files/requirements.txt")
        .add_local_file("agent_sandbox/tools/apply_patch", "/usr/local/bin/apply_patch")  # Add apply_patch tool
        .run_commands("chmod +x /usr/local/bin/apply_patch")  # Make apply_patch executable
    )
    
    # Modify AGENTS.md with user context if provided
    if context:
        logger_module.info(">>> [1] Adding user context to AGENTS.md...")
        try:
            modify_agents_md(context, session_dir)
        except Exception as e:
            logger_module.error(f"Failed to modify AGENTS.md: {e}")
            logger_module.info("    Continuing without user context...")

    # Mount the session directory to the sandbox
    logger_module.info("Mounting session directory to sandbox...")
    image = image.add_local_dir(session_dir, "/workspace")

    # Create ephemeral volume using context manager
    logger_module.info("Creating ephemeral volume...")
    with modal.Volume.ephemeral() as vol:
        # Create Modal Sandbox using the App, image, and ephemeral volume
        logger_module.info("Creating sandbox with ephemeral volume...")
        sb = None
        try:
            sb = modal.Sandbox.create(
                app=app,
                image=image,
                volumes={"/output": vol},
                workdir="/workspace"
            )
            
            logger_module.info("Sandbox created successfully!")
            
            # Run the coding agent with the sandbox
            logger_module.info(">>> [2] Running coding agent with sandbox...")
            try:
                sys.path.append(str(Path("agent_sandbox")))
                from agent_sandbox.coding_agent import run_coding_agent
                result = run_coding_agent(
                    request=AGENT_COMMAND,
                    container_or_sandbox=sb,
                    logger=logger,
                    use_modal=True
                )
                logger_module.info("Agent execution completed successfully.")
            except ImportError as e:
                logger_module.error(f"Failed to import coding_agent: {e}")
                raise
            except Exception as e:
                logger_module.error(f"Agent execution failed: {e}")
                raise
            
            # Terminate sandbox (this syncs the volume)
            logger_module.info("Terminating sandbox...")
            if sb:
                sb.terminate()
                logger_module.info("Sandbox terminated successfully!")
            
            # Download results from ephemeral volume
            logger_module.info(">>> [3] Downloading results from ephemeral volume...")
            
            # Create output directory if it doesn't exist
            output_dir = session_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Wait for volume to be ready (similar to minimal example)
            logger_module.info("Waiting for volume to be ready...")
            time.sleep(5)  # Initial wait to ensure the volume is synced
            
            # List files in the volume to see what was created
            logger_module.info("Files in ephemeral volume:")
            try:
                for file_info in vol.listdir("/"):
                    logger_module.info(f"  - {file_info}")
                    # Try to get more details about each entry
                    if file_info.type == modal.volume.FileEntryType.DIRECTORY:
                        try:
                            sub_items = list(vol.listdir(f"/{file_info.path}"))
                            logger_module.info(f"    Contents of {file_info.path}: {len(sub_items)} items")
                            for sub_item in sub_items:
                                logger_module.info(f"      - {sub_item}")
                        except Exception as sub_error:
                            logger_module.warning(f"    Could not list contents of {file_info.path}: {sub_error}")
            except Exception as e:
                logger_module.warning(f"Could not list volume files: {e}")
                logger_module.info("Volume may not be ready yet, will retry...")
            
            # Download all files from the volume recursively
            logger_module.info("Downloading all files from volume...")
            
            def download_all(start_path, local_dest):
                """Iterates through the volume and downloads all files recursively."""
                logger_module.info("Listing all files for download...")
                try:
                    for entry in vol.iterdir(start_path, recursive=True):
                        # The full path inside the volume, including the leading slash
                        full_volume_path = f"/{entry.path}"
                        # The corresponding destination path on the local filesystem
                        local_file_path = local_dest / entry.path
                        
                        if entry.type == modal.volume.FileEntryType.FILE:
                            try:
                                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(local_file_path, "wb") as f:
                                    for chunk in vol.read_file(full_volume_path):
                                        f.write(chunk)
                                logger_module.info(f"  Downloaded: {local_file_path}")
                            except Exception as e:
                                logger_module.error(f"  Error downloading {full_volume_path}: {e}")
                except Exception as e:
                    logger_module.error(f"Could not list files in volume: {e}")

            # Start the download from the root of the volume
            download_all("/", output_dir)
            logger_module.info("\nDownload complete.")
            
            return result
            
        except modal.error.SandboxError as e:
            logger_module.error(f"Modal sandbox error: {e}")
            raise
        except modal.error.TimeoutError as e:
            logger_module.error(f"Modal operation timed out: {e}")
            raise
        except modal.error.VolumeError as e:
            logger_module.error(f"Modal volume error: {e}")
            raise
        except Exception as e:
            logger_module.error(f"Unexpected error creating sandbox: {e}")
            raise
        finally:
            # Ensure sandbox is terminated even if there's an error
            if sb:
                try:
                    sb.terminate()
                    logger_module.info("Sandbox terminated in cleanup.")
                except Exception as cleanup_error:
                    logger_module.warning(f"Error during sandbox cleanup: {cleanup_error}")

if __name__ == "__main__":
    # For local testing and development
    logger.info("Modal agent runner - use with modal.run() or modal.serve()")
    logger.info("Example: modal run modal_agent.py --function-name run_agent_in_sandbox") 