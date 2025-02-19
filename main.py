import asyncio
import time
from api_client import E621Client
from models import Pool, Post
from downloader import download_image
from utils import create_directory, create_internet_shortcut

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

            result = func(*args)
            self.last_request_time = time.time()
            return result

    async def fetch_pool(self, pool_id):
        """Retrieve pool data by ID with rate limiting."""
        pool_data = await self.rate_limited_request(self.client.get_pool, pool_id)
        return Pool(pool_data) if pool_data else None

    async def fetch_post(self, post_id):
        """Retrieve post data by ID with rate limiting."""
        post_data = await self.rate_limited_request(self.client.get_post, post_id)
        return Post(post_data) if post_data else None

    async def download_pool(self, pool_id):
        """Download all posts in a pool."""
        pool = await self.fetch_pool(pool_id)
        if not pool or not pool.post_ids:
            return {"error": "Failed to retrieve pool or no posts found."}

        # Determine artist name
        first_post = await self.fetch_post(pool.post_ids[0])
        if not first_post:
            return {"error": "Failed to retrieve post data."}

        artist = first_post.artists[1] if first_post.artists and first_post.artists[0] == "conditional_dnp" and len(first_post.artists) > 1 else first_post.artists[0] if first_post.artists else "Unknown Artist"

        # Create working directory
        working_dir = create_directory(pool.name, artist)
        create_internet_shortcut(f"https://e621.net/pools/{pool.id}", working_dir, working_dir)

        # Download all posts with rate limiting
        tasks = [
            self.download_post(post_id, i, working_dir)
            for i, post_id in enumerate(pool.post_ids)
        ]
        await asyncio.gather(*tasks)

        return {"status": "completed", "pool_id": pool_id, "pool_name": pool.name, "total_posts": pool.post_count}

    async def download_post(self, post_id, index, directory):
        """Download a single post with rate limiting."""
        post = await self.fetch_post(post_id)
        if post:
            await download_image(post, index, directory)
            return {"post_id": post.id, "status": "downloaded"}
        return {"post_id": post_id, "status": "failed"}


# Entry point for external execution
async def main():
    downloader = E621Downloader()
    pool_id = int(input("\nEnter the ID of the pool to download: ").strip())
    result = await downloader.download_pool(pool_id)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
