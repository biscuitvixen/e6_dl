""" Main backend module for downloading pools from e621.net """

import asyncio
import time
from backend.api_client import E621Client
from backend.models import Pool, Post
from backend.downloader import download_image
from backend.utils import create_directory, create_internet_shortcut
from backend.logger_config import logger
from tqdm.asyncio import tqdm

RATE_LIMIT = 2 # Seconds. e621 API rate limit is 2 requests per second

class E621Downloader:
    def __init__(self):
        """Initialize downloader with API client and rate limiter."""
        self.client = E621Client()
        self.rate_limit = asyncio.Semaphore(1)  # Controls concurrent requests
        self.last_request_time = 0  # Track last API request

    async def rate_limited_request(self, func, *args):
        """Rate-limited API request function."""
        async with self.rate_limit:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < RATE_LIMIT:  # Enforce delay per request
                await asyncio.sleep(RATE_LIMIT - elapsed_time)

            result = await func(*args)  # Await the function call
            self.last_request_time = time.time()
            return result

    async def fetch_pool(self, pool_id):
        """Retrieve pool data by ID with rate limiting."""
        logger.info(f"Fetching pool {pool_id}...")
        pool_data = await self.rate_limited_request(self.client.get_pool, pool_id)
        if not pool_data:
            logger.warning(f"Pool {pool_id} not found.")
            return None
        return Pool(pool_data)

    async def fetch_post(self, post_id):
        """Retrieve post data by ID with rate limiting."""
        logger.debug(f"Fetching post {post_id}...")
        post_data = await self.rate_limited_request(self.client.get_post, post_id)
        if not post_data:
            logger.warning(f"Post {post_id} not found.")
            return None
        return Post(post_data)

    async def download_pool(self, pool_id, progress_bar):
        """Download all posts in a pool."""
        pool = await self.fetch_pool(pool_id)
        if not pool or not pool.post_ids:
            logger.warning(f"Skipping pool {pool_id}, no posts found.")
            return

        # Determine artist name
        first_post = await self.fetch_post(pool.post_ids[0])
        if not first_post:
            return

        artist = first_post.artists[1] if first_post.artists and first_post.artists[0] == "conditional_dnp" and len(first_post.artists) > 1 else first_post.artists[0] if first_post.artists else "Unknown Artist"

        # Create working directory
        working_dir = create_directory(pool.name, artist)
        create_internet_shortcut(f"https://e621.net/pools/{pool.id}", working_dir, working_dir)

        logger.info(f"Downloading {pool.post_count} posts from pool: {pool.name}")

        async def track_download(post_id, index, directory):
            """Download a single post, update progress, and yield result."""
            result = await self.download_post(post_id, index, directory)
            progress_bar.update(1)
            yield result  # Yield success/failure info

        # Download all posts with rate limiting and collect results
        for index, post_id in enumerate(pool.post_ids):
            async for result in track_download(post_id, index, working_dir):
                yield result  # Pass results back to process_pool_ids
        
    async def download_post(self, post_id, index, directory):
        """Download a single post with rate limiting."""
        post = await self.fetch_post(post_id)
        if post:
            await download_image(post, index, directory)
            logger.debug(f"Downloaded post {post.id}")
            return {"post_id": post.id, "status": "downloaded"}
        logger.warning(f"Failed to download post {post_id}")
        return {"post_id": post_id, "status": "failed"}


async def process_pool_ids(pool_ids):
    """Process multiple pool IDs asynchronously with progress tracking."""
    downloader = E621Downloader()

    all_failed = {}  # Store failed downloads for retrying later

    for pool_id in pool_ids:
        # Fetch pool info before creating a progress bar
        pool = await downloader.fetch_pool(pool_id)
        if not pool:
            logger.warning(f"Skipping pool {pool_id}, no valid data.")
            continue

        total_images = pool.post_count
        pool_name = pool.name
        success, failed = [], []

        # Create a new progress bar for this pool
        with tqdm(total=total_images, desc=f"Downloading {pool_name}", unit="image", position=0, leave=True) as progress_bar:
            async for post_result in downloader.download_pool(pool_id, progress_bar):
                if post_result["status"] == "downloaded":
                    success.append(post_result["post_id"])
                else:
                    failed.append(post_result["post_id"])

        # Print success message after pool download completes
        tqdm.write(f"✅ Successfully downloaded {pool_name} - {len(success)} images")

        # Store failed downloads for potential retrying
        if failed:
            all_failed[pool_id] = failed

    return all_failed  # Return failed downloads for retrying later