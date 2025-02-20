""" Module for downloading images asynchronously """

import aiohttp
import aiofiles
import os
from backend.models import Post
from backend.logger_config import logger

async def download_image(post: Post, index, working_dir):
    """Downloads an image asynchronously using aiohttp."""
    if post.is_deleted:
        logger.warning(f"Skipping deleted post {post.id}")
        return

    if not post.file_url:
        logger.warning(f"Skipping post {post.id}, no URL found.")
        return

    filename = f"{index + 1}.{post.file_ext}"
    path = os.path.join(working_dir, filename)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(post.file_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {post.file_url}: HTTP {response.status}")
                    return

                # Asynchronous file writing
                async with aiofiles.open(path, "wb") as f:
                    await f.write(await response.read())

        logger.info(f"Downloaded {path}")
    
    except aiohttp.ClientError as e:
        logger.warning(f"Failed to download {post.file_url}: {e}")
