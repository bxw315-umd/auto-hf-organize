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
OUTPUT_DIR = ROOT / "outputs" / "user_files"
CONTAINER_SCRIPT = ROOT / "agent_sandbox" / "run_container.py"

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
            encoding="utf-8",
            check=True
        )
        container_name = result.stdout.strip().split('\n')[-1].strip()
        logger.info(f"    Container started: {container_name}")
        return container_name
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting container: {e.stderr.strip()}")
        raise

def run_agent_step(command: str, container: str, logger_type: str = "stdout"):
    """Invoke the coding agent with provided command and container."""
    logger.info(">>> [2] Running summarizer agent...")
    response = run_coding_agent(command, container, logger_type)
    logger.info(f"    Agent response: {response}")
    return response

def stop_container(name: str):
    """Stop the Docker container via docker-py."""
    logger.info(">>> [3] Stopping container...")
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

def main(logger_type: str = "stdout"):
    # Step 0: (Optional) Copy any needed files to OUTPUT_DIR here if needed

    # Step 1: start container
    container = start_container(CONTAINER_SCRIPT)

    # Step 2: run summarizer agent
    summarizer_command = (
        "Could you look through the huggingface dataset at `dataset_hf` and, given the context in AGENTS.md, write a blurb about\n"
        "* what the dataset describes\n"
        "* how variables are formatted semantically\n"
        "* the variables that differ between samples\n"
        "* the variables that are all the same between samples\n"
        "* if a variable only has a few unique values, what they are\n"
        "* any other interesting details\n\n"
        "This blurb will be passed as context into an automated plotting agent which does not have access to the data, so\n"
        "your response should be complete but concise. It should include information about the dataset in isolation, not in the context of other files that were scanned (such as AGENTS.md)."
    )
    response = run_agent_step(summarizer_command, container, logger_type)

    with open(OUTPUT_DIR / "dataset_description.txt", "w", encoding="utf-8") as f:
        f.write(response)

    # Step 3: stop container
    stop_container(container)

    logger.info("\n✅ Summarizer agent execution completed successfully!")
    return response

if __name__ == "__main__":
    main()