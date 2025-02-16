""" Module for downloading images asynchronously """

import requests
import shutil
import os
import asyncio
from models import Post

async def download_image(post: Post, index, working_dir):
    """Downloads an image asynchronously."""
    if post.is_deleted:
        print(f"Skipping deleted post {post.id}")
        return

    if not post.file_url:
        print(f"Skipping post {post.id}, no URL found.")
        return

    filename = f"{index + 1}.{post.file_ext}"
    path = os.path.join(working_dir, filename)

    try:
        response = requests.get(post.file_url, stream=True)
        response.raise_for_status()
        with open(path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        print(f"Downloaded {path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {post.file_url}: {e}")