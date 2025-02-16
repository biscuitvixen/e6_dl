""" This file contains utility functions for the project """

import os

def create_directory(pool_name, artist):
    """Creates a directory for the downloaded pool and returns the
    sanitized name of the directory."""
    sanitized_name = sanitize_filename(f"{pool_name} by {artist}")
    if not os.path.exists(sanitized_name):
        os.makedirs(sanitized_name)
    return sanitized_name

def create_internet_shortcut(url, directory, name):
    """Creates an internet shortcut file."""
    with open(f"{directory}/{name}.url", "w") as shortcut:
        shortcut.write("[InternetShortcut]\n")
        shortcut.write(f"URL={url}")
    

def sanitize_filename(filename):
    """Removes illegal characters from folder names."""
    forbidden_chars = ('<', '>', ':', '\"', '/', '\\', '?', '*', '|')
    name = filename
    for char in forbidden_chars:
        name = name.replace(char, "")
    return name