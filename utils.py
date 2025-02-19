""" This file contains utility functions for the project """

import os
from logger_config import logger

def create_directory(pool_name, artist):
    """Creates a directory for the downloaded pool and returns the
    sanitized name of the directory."""
    sanitized_name = sanitize_filename(f"{pool_name} by {artist}")
    logger.debug(f"Sanitized directory name: {sanitized_name}")
    if not os.path.exists(sanitized_name):
        os.makedirs(sanitized_name)
        logger.info(f"Directory created: {sanitized_name}")
    else:
        logger.info(f"Directory already exists: {sanitized_name}")
    return sanitized_name

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