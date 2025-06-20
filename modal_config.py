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
MODAL_APP_NAME = "sandbox-environment"
# Path to the requirements file inside the agent_sandbox submodule
REQUIREMENTS_PATH = "agent_sandbox/user_files/requirements.txt"

app = modal.App(MODAL_APP_NAME)

base_image = (
    modal.Image.debian_slim()
    .pip_install_from_requirements(REQUIREMENTS_PATH)
    .run_commands(
        "mkdir -p /workspace /output",
    )
)

def create_custom_image_with_files(local_dir_path: str):
    """
    Creates a custom Modal image by mounting a local directory
    to the /workspace path in the container.
    """
    return base_image.add_local_dir(local_dir_path, "/workspace")

# Global app instance
_modal_app = None
_base_image = None

def initialize_modal():
    """Initialize Modal app and base image."""
    global _modal_app, _base_image
    
    if _modal_app is None:
        _modal_app = app
    
    if _base_image is None:
        _base_image = base_image
    
    return _modal_app, _base_image

def get_app():
    """Get the Modal app instance."""
    if _modal_app is None:
        initialize_modal()
    return _modal_app

def get_image():
    """Get the base Modal image."""
    if _base_image is None:
        initialize_modal()
    return _base_image 