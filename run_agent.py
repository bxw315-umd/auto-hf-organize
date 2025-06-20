#!/usr/bin/env python3
import shutil
import subprocess
import logging
from pathlib import Path

import docker
from agent_sandbox.coding_agent import run_coding_agent

# Configure logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
ROOT = Path.cwd()
SANDBOX_USER_DIR = ROOT / "agent_sandbox" / "user_files"
MY_FILES_DIR = ROOT / "my_files"
OUTPUT_DIR = ROOT / "outputs" / "user_files"
CONTAINER_SCRIPT = ROOT / "agent_sandbox" / "run_container.py"

AGENT_COMMAND = (
    "I've provided you with the raw data files for an experiment. "
    "Please take the dataset and organize it into a huggingface dataset, complete "
    "with metadata columns inferred from the file names. Refer to AGENTS.md for more details. "
    "Save the dataset to disk as `dataset_hf`."
)

# Initialize Docker client
docker_client = docker.from_env()


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


def start_container(script: Path) -> str:
    """Run the Python script to start container and return its name."""
    logger.info(">>> [0] Starting container...")
    try:
        result = subprocess.run(
            ["python", "-u", str(script)],
            capture_output=True,
            text=True,
            check=True
        )
        # The Python script outputs just the container name as the last line
        container_name = result.stdout.strip().split('\n')[-1].strip()
        logger.info(f"    Container started: {container_name}")
        return container_name
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting container: {e.stderr.strip()}")
        raise


def run_agent_step(command: str, container: str, logger_type: str = "stdout"):
    """Invoke the coding agent with provided command and container."""
    logger.info(">>> [3] Running agent...")
    response = run_coding_agent(command, container, logger_type)
    logger.info(f"    Agent response: {response}")
    return response


def stop_container(name: str):
    """Stop the Docker container via docker-py."""
    logger.info(">>> [4] Stopping container...")
    try:
        container = docker_client.containers.get(name)
        container.stop()
        logger.info("    Container stopped successfully")
    except docker.errors.NotFound:
        logger.error(f"Container not found: {name}")
        raise
    except Exception as e:
        logger.error(f"Error stopping container: {e}")
        raise


def modify_agents_md(context: str):
    """Append user context to AGENTS.md as a new section."""
    agents_md_path = OUTPUT_DIR / "AGENTS.md"
    
    if not agents_md_path.exists():
        logger.error(f"AGENTS.md not found at {agents_md_path}")
        raise FileNotFoundError(f"AGENTS.md not found at {agents_md_path}")
    
    try:
        # Read existing content
        with open(agents_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Append user context as new section
        context_section = f"\n\n## Experiment Details\n\n{context}\n"
        updated_content = content + context_section
        
        # Write back to file
        with open(agents_md_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"    Added user context to AGENTS.md")
    except Exception as e:
        logger.error(f"Failed to modify AGENTS.md: {e}")
        raise


def main(logger_type: str = "stdout", context: str = ""):
    
    # Step 0: copy user files
    logger.info(">>> [0] Copying files from agent_sandbox/user_files to outputs/user_files...")
    copy_dir(SANDBOX_USER_DIR, OUTPUT_DIR)

    logger.info(">>> [0] Copying files from my_files to outputs/user_files...")
    copy_dir(MY_FILES_DIR, OUTPUT_DIR)

    # Step 1: Modify AGENTS.md with user context if provided
    if context:
        logger.info(">>> [0] Adding user context to AGENTS.md...")
        modify_agents_md(context)

    # Step 2: start container
    container = start_container(CONTAINER_SCRIPT)

    # Step 3: run agent
    response = run_agent_step(AGENT_COMMAND, container, logger_type)

    # Step 4: stop container
    stop_container(container)

    logger.info("\n✅ Agent execution completed successfully!")
    return response

if __name__ == "__main__":
    main()