import asyncio
import time
import argparse
from api_client import E621Client
from models import Pool, Post
from downloader import download_image
from utils import create_directory, create_internet_shortcut
from logger_config import logger, set_log_level  # Import the centralized logger

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
            if elapsed_time < 2:  # Enforce 2s delay per request
                await asyncio.sleep(2 - elapsed_time)

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

    async def download_pool(self, pool_id):
        """Download all posts in a pool."""
        pool = await self.fetch_pool(pool_id)
        if not pool or not pool.post_ids:
            logger.warning(f"Skipping pool {pool_id}, no posts found.")
            return {"error": f"Failed to retrieve pool {pool_id} or no posts found."}

        # Determine artist name
        first_post = await self.fetch_post(pool.post_ids[0])
        if not first_post:
            return {"error": f"Failed to retrieve first post for pool {pool_id}."}

        artist = first_post.artists[1] if first_post.artists and first_post.artists[0] == "conditional_dnp" and len(first_post.artists) > 1 else first_post.artists[0] if first_post.artists else "Unknown Artist"

        # Create working directory
        working_dir = create_directory(pool.name, artist)
        create_internet_shortcut(f"https://e621.net/pools/{pool.id}", working_dir, working_dir)

        logger.info(f"Downloading {pool.post_count} posts from pool: {pool.name}")

        # Download all posts with rate limiting
        tasks = [
            self.download_post(post_id, i, working_dir)
            for i, post_id in enumerate(pool.post_ids)
        ]
        await asyncio.gather(*tasks)

        logger.info(f"Completed downloading pool {pool_id} - {pool.name}")
        return {"status": "completed", "pool_id": pool_id, "pool_name": pool.name, "total_posts": pool.post_count}

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
    """Process multiple pool IDs asynchronously."""
    downloader = E621Downloader()
    tasks = [downloader.download_pool(pool_id) for pool_id in pool_ids]
    await asyncio.gather(*tasks)

async def main():
    """Main execution: Parse input and process pools."""
    parser = argparse.ArgumentParser(description="Download pools from E621.")
    parser.add_argument("pool_ids", nargs="*", help="List of pool IDs or URLs (separated by space)")
    parser.add_argument("--log-level", help="Set logging level (DEBUG, INFO, WARNING, ERROR)", default="INFO")

    args = parser.parse_args()

    # Set log level from argument
    set_log_level(args.log_level)

    if args.pool_ids:
        # Process command-line arguments
        pool_ids = [int(pool.split("/")[-1]) for pool in args.pool_ids if pool.split("/")[-1].isdigit()]
    else:
        # Ask for input if no arguments are provided
        user_input = input("\nEnter the ID(s) or URL(s) of the pools to download (separate by space): ").strip()
        pool_ids = [int(pool.split("/")[-1]) for pool in user_input.split() if pool.split("/")[-1].isdigit()]

    if not pool_ids:
        logger.error("No valid pool IDs provided.")
        return

    logger.info(f"Processing {len(pool_ids)} pools: {pool_ids}")
    await process_pool_ids(pool_ids)

if __name__ == "__main__":
    asyncio.run(main())
