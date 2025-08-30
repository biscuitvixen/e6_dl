""" This file contains utility functions for the project """

import os
from pathlib import Path
from backend.logger_config import logger

def create_directory(pool_name, artist, base_dir="."):
    """Creates a directory for the downloaded pool and returns the
    sanitized name of the directory."""
    sanitized_name = sanitize_filename(f"{pool_name} by {artist}")
    logger.debug(f"Sanitized directory name: {sanitized_name}")
    
    # Create the full path using the base directory (current dir by default)
    base_path = Path(base_dir)
    full_path = base_path / sanitized_name
    
    if not full_path.exists():
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created: {full_path}")
    else:
        logger.info(f"Directory already exists: {full_path}")
    
    return str(full_path)

def create_internet_shortcut(url, directory, name):
    """Creates an internet shortcut file."""
    shortcut_path = f"{directory}/{name}.url"
    with open(shortcut_path, "w") as shortcut:
        shortcut.write("[InternetShortcut]\n")
        shortcut.write(f"URL={url}")
    logger.debug(f"Internet shortcut created: {shortcut_path}")

def sanitize_filename(filename):
    """Removes illegal characters from folder names."""
    forbidden_chars = ('<', '>', ':', '\"', '/', '\\', '?', '*', '|')
    name = filename
    for char in forbidden_chars:
        name = name.replace(char, "")
    logger.debug(f"Sanitized filename: {name}")
    return name