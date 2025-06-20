#!/usr/bin/env python3
"""
Modal configuration and initialization for the experiment processing system.
"""

import modal
import os
import logging

# Configure logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Modal App configuration
stub = modal.Stub("huggingface-dataset-organizer")

# Mount the agent sandbox directory
agent_sandbox_mount = modal.Mount.from_local_dir(
    "agent_sandbox", remote_path="/root/agent_sandbox"
)

# Define the Modal image
sandbox_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install_from_requirements("agent_sandbox/user_files/requirements.txt")
) 