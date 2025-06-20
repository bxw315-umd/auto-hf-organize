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
import sys
import shutil

# Configure logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Modal App
app = modal.App("dataset-processor-agent")

# Base image for the remote environment
image = (
    modal.Image.debian_slim()
    .apt_install("ripgrep", "ed")  # Install ripgrep and ed
    .pip_install_from_requirements("agent_sandbox/user_files/requirements.txt")
    .add_local_file("agent_sandbox/tools/apply_patch", "/usr/local/bin/apply_patch", copy=True)
    .run_commands("chmod +x /usr/local/bin/apply_patch")
    .add_local_python_source("agent_sandbox")
)

def get_agent_command(workspace: str):
    """Generates the agent command with the dynamic output directory."""
    return (
        f"I've provided you with the raw data files for an experiment in the '{workspace}' directory. "
        "Please take the dataset and organize it into a huggingface dataset, complete "
        "with metadata columns inferred from the file names. Refer to AGENTS.md for more details. "
        f"All files you generate should be saved in the '{workspace}' directory."
        f"Save the dataset to disk as '{workspace}/dataset_hf'."
    )
    

@app.function(image=image, timeout=900, secrets=[modal.Secret.from_name("openai-secret")])
def run_agent_remotely(session_id: str, context: str = "", logger_str: str = "stdout", endpoint_url: str = None):
    """
    Runs the coding agent inside a Modal environment.
    This function creates a session-specific volume, waits for data, and then executes the agent.
    """
    logger_module = logging.getLogger(__name__)
    
    volume_name = f"dataset-volume-{session_id}"
    logger_module.info(f"Using persistent volume: '{volume_name}'")
    volume = modal.Volume.from_name(volume_name, create_if_missing=False)
    
    logger_module.info("Creating sandbox with persistent volume...")
    sb = None
    try:
        sb = modal.Sandbox.create(
            volumes={"/workspace": volume},
            workdir="/workspace",
            timeout=850
        )
        logger_module.info("Sandbox created successfully!")

        logger_module.info(f"Waiting for session data in volume '{volume_name}'...")
        timeout_seconds = 300
        start_time = time.time()
        is_ready = False
        while not is_ready:
            if time.time() - start_time > timeout_seconds:
                error_msg = f"Timeout: Session data not found in volume '{volume_name}' after {timeout_seconds}s."
                logger_module.error(error_msg)
                raise TimeoutError(error_msg)
            
            
            proc = sb.exec("test", "-f", "/workspace/AGENTS.md")
            try:
                proc.wait()
                if proc.returncode == 0:
                    is_ready = True
                    logger_module.info(f"Session data found in volume '{volume_name}'.")
                else:
                    logger_module.info("Session data not found. Retrying in 5s...")
                    time.sleep(5)
            except Exception as e:
                logger_module.warning(f"Error checking volume, will retry: {e}")
                time.sleep(5)

        if context:
            logger_module.info(">>> [1] Adding user context to AGENTS.md...")
            
            script_to_run = (
                "from pathlib import Path;"
                "import sys;"
                f"context = '''{context}''';"
                "agents_md_path = Path('/workspace/AGENTS.md');"
                "if not agents_md_path.exists(): sys.exit(1);"
                "content = agents_md_path.read_text();"
                "context_section = f'\\n\\n## Experiment Details\\n\\n{context}\\n';"
                "updated_content = content + context_section;"
                "agents_md_path.write_text(updated_content);"
            )
            
            safe_script = script_to_run.replace("'", "'\\''")
            
            proc = sb.exec("python", "-c", safe_script)
            proc.wait()
            if proc.returncode == 0:
                logger_module.info(f"    Added user context to AGENTS.md in volume '{volume_name}'")
            else:
                logger_module.error(f"Failed to modify AGENTS.md in volume '{volume_name}'")
                logger_module.info("    Continuing without user context...")

        logger_module.info(">>> [2] Running coding agent with sandbox...")
        try:
            sys.path.append(str(Path("agent_sandbox")))
            from agent_sandbox.coding_agent import run_coding_agent
            
            agent_command = get_agent_command("/workspace")
            
            result = run_coding_agent(
                request=agent_command,
                container_or_sandbox=sb,
                logger=logger_str,
                use_modal=True,
                endpoint_url=endpoint_url
            )
            logger_module.info("Agent execution completed successfully.")
            return result
        except ImportError as e:
            logger_module.error(f"Failed to import coding_agent: {e}")
            raise
        except Exception as e:
            logger_module.error(f"Agent execution failed: {e}")
            raise
            
    except Exception as e:
        logger_module.error(f"Unexpected error creating sandbox: {e}")
        raise
    finally:
        if sb:
            try:
                sb.terminate()
                logger_module.info("Sandbox terminated in cleanup.")
            except Exception as cleanup_error:
                logger_module.warning(f"Error during sandbox cleanup: {cleanup_error}")

@app.local_entrypoint()
def main(session_id: str, context: str = "", logger: str = "stdout", endpoint_url: str = None):
    """
    Local entrypoint to run the agent.
    - Triggers the remote Modal function with a session_id.
    """
    logger_module = logging.getLogger(__name__)
    logger_module.info(f"Starting Modal agent execution for session_id: {session_id}")

    logger_module.info("Calling remote function `run_agent_remotely`...")
    run_agent_remotely.remote(session_id=session_id, context=context, logger_str=logger, endpoint_url=endpoint_url)

if __name__ == "__main__":
    logger.info("Modal agent runner - use `modal run modal_agent.py --session-id <ID>` to execute.") 