#!/usr/bin/env python3
"""
Test script to verify the context functionality works correctly.
"""

import os
import shutil
import tempfile
from pathlib import Path
from run_agent import modify_agents_md, main, OUTPUT_DIR
import pytest
import run_agent

@pytest.fixture
def agents_md(tmp_path):
    agents_md_path = tmp_path / "AGENTS.md"
    original_content = (
        "# Agent Instructions\n\n"
        "This is the original AGENTS.md content.\n\n"
        "## Section 1\nSome instructions here.\n\n"
        "## Section 2\nMore instructions here.\n"
    )
    agents_md_path.write_text(original_content, encoding="utf-8")
    # Patch OUTPUT_DIR for the duration of the test
    old_output_dir = run_agent.OUTPUT_DIR
    run_agent.OUTPUT_DIR = tmp_path
    yield agents_md_path, original_content
    run_agent.OUTPUT_DIR = old_output_dir


def test_empty_context(agents_md):
    agents_md_path, original_content = agents_md
    modify_agents_md("")
    content = agents_md_path.read_text(encoding="utf-8")
    # Per PRD, empty context still appends the section
    assert content.endswith("\n\n## Experiment Details\n\n\n"), "Should append empty section for empty context"


def test_simple_context(agents_md):
    agents_md_path, _ = agents_md
    test_context = "This is a test experiment context."
    modify_agents_md(test_context)
    content = agents_md_path.read_text(encoding="utf-8")
    assert "## Experiment Details" in content
    assert test_context in content


def test_complex_context(agents_md):
    agents_md_path, _ = agents_md
    complex_context = (
        "This is a complex experiment context.\n\n"
        "It has multiple lines and special characters: émojis 🧪, quotes \"test\", and symbols & < >.\n\n"
        "The experiment involves:\n- File naming conventions\n- Experimental conditions\n- Data structure details"
    )
    modify_agents_md(complex_context)
    content = agents_md_path.read_text(encoding="utf-8")
    assert "## Experiment Details" in content
    assert "émojis 🧪" in content
    assert "- Experimental conditions" in content


def test_error_handling_missing_file(tmp_path):
    # Patch OUTPUT_DIR to a directory with no AGENTS.md
    old_output_dir = run_agent.OUTPUT_DIR
    run_agent.OUTPUT_DIR = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError):
        modify_agents_md("test context")
    run_agent.OUTPUT_DIR = old_output_dir


def test_type_validation(agents_md):
    # Non-string input should raise ValueError
    with pytest.raises(ValueError):
        modify_agents_md(123) 