""" Main backend module for downloading pools from e621.net """

import asyncio
import time
import os
from backend.api_client import E621Client
from backend.models import Pool, Post
from backend.downloader import download_image
from backend.utils import create_directory, create_internet_shortcut
from backend.database import DownloadDatabase
from backend.logger_config import logger
from tqdm.asyncio import tqdm

RATE_LIMIT = 2 # Seconds. e621 API rate limit is 2 requests per second

class E621Downloader:
    def __init__(self, base_download_dir="."):
        """Initialize downloader with API client, rate limiter, and database."""
        self.client = E621Client()
        self.base_download_dir = base_download_dir
        self.db = DownloadDatabase(base_download_dir=base_download_dir)
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

    async def download_pool(self, pool_id, progress_bar, skip_existing=True):
        """Download all posts in a pool, optionally skipping existing ones."""
        pool = await self.fetch_pool(pool_id)
        if not pool or not pool.post_ids:
            logger.warning(f"Skipping pool {pool_id}, no posts found.")
            return

        # Check for existing pool info in database
        existing_pool = self.db.get_pool_info(pool_id)
        
        if existing_pool:
            logger.info(f"Found existing pool record in database: {existing_pool['name']}")
            logger.info(f"  - Artist: {existing_pool['artist']}")
            logger.info(f"  - Post count: {existing_pool['post_count']}")
            logger.info(f"  - Directory: {existing_pool['folder_path']}")
        else:
            logger.info(f"Pool {pool_id} not found in database - will create new record")
        
        # Determine artist name
        logger.info(f"Fetching first post to determine artist...")
        first_post = await self.fetch_post(pool.post_ids[0])
        if not first_post:
            logger.error(f"Failed to fetch first post {pool.post_ids[0]} for artist detection")
            return

        artist = first_post.artists[1] if first_post.artists and first_post.artists[0] == "conditional_dnp" and len(first_post.artists) > 1 else first_post.artists[0] if first_post.artists else "Unknown Artist"
        logger.info(f"Detected artist: {artist}")

        # Determine working directory
        if existing_pool and os.path.exists(existing_pool['folder_path']):
            # Use existing directory
            working_dir = existing_pool['folder_path']
            logger.info(f"Using existing directory: {working_dir}")
        else:
            # Create new directory
            logger.info(f"Creating new directory for pool: {pool.name}")
            working_dir = create_directory(pool.name, artist, self.base_download_dir)
            logger.info(f"Created directory: {working_dir}")
            create_internet_shortcut(f"https://e621.net/pools/{pool.id}", working_dir, working_dir)
            logger.info(f"Created pool shortcut in directory")

        # Save/update pool info in database
        self.db.save_pool(pool_id, pool.name, artist, working_dir, pool.post_count)
        logger.info(f"Pool information saved to database")

        if skip_existing:
            logger.info(f"Checking for existing downloads (skip_existing=True)")
            
            # Verify existing files and clean up missing ones
            logger.info(f"Verifying downloaded files against filesystem...")
            missing_files = self.db.verify_downloaded_files(pool_id)
            if missing_files:
                logger.info(f"Found {len(missing_files)} missing files in filesystem, will re-download")
            else:
                logger.info(f"All previously downloaded files verified as present")

            # Get posts that need to be downloaded
            posts_to_download = self.db.get_missing_posts(pool_id, pool.post_ids)
            
            if not posts_to_download:
                logger.info(f"Pool {pool.name} is already fully downloaded! ({pool.post_count} posts)")
                return
            
            already_downloaded = pool.post_count - len(posts_to_download)
            logger.info(f"Download plan: {already_downloaded} posts already downloaded, {len(posts_to_download)} posts need downloading")
            logger.info(f"Downloading {len(posts_to_download)} new/missing posts from pool: {pool.name} (Total: {pool.post_count})")
        else:
            posts_to_download = pool.post_ids
            logger.info(f"Re-downloading ALL posts (skip_existing=False)")
            logger.info(f"Re-downloading all {pool.post_count} posts from pool: {pool.name}")

        async def track_download(post_id, directory):
            """Download a single post, update progress, and yield result."""
            # Find the position of this post in the original pool order
            position = pool.post_ids.index(post_id)
            result = await self.download_post(post_id, position, directory, pool_id)
            progress_bar.update(1)
            yield result  # Yield success/failure info

        # Download missing posts with rate limiting and collect results
        for post_id in posts_to_download:
            async for result in track_download(post_id, working_dir):
                yield result  # Pass results back to process_pool_ids
        
    async def download_post(self, post_id, index, directory, pool_id):
        """Download a single post with rate limiting and database tracking."""
        post = await self.fetch_post(post_id)
        if post:
            filename = f"{index + 1}.{post.file_ext}"
            file_path = os.path.join(directory, filename)
            
            await download_image(post, index, directory)
            
            # Mark as downloaded in database
            self.db.mark_post_downloaded(post_id, pool_id, file_path, index)
            
            logger.debug(f"Downloaded post {post.id}")
            return {"post_id": post.id, "status": "downloaded"}
        logger.warning(f"Failed to download post {post_id}")
        return {"post_id": post_id, "status": "failed"}

    async def check_pool_for_updates(self, pool_id):
        """Check if a pool has new posts since last download."""
        logger.info(f"Checking pool {pool_id} for updates...")
        
        # Get current pool data from API
        current_pool = await self.fetch_pool(pool_id)
        if not current_pool:
            logger.warning(f"Could not fetch current data for pool {pool_id}")
            return None
        
        # Get stored pool data from database
        stored_pool = self.db.get_pool_info(pool_id)
        if not stored_pool:
            logger.info(f"Pool {pool_id} not found in database - treating as new pool")
            return {
                'pool_id': pool_id,
                'pool_name': current_pool.name,
                'has_updates': True,
                'old_count': 0,
                'new_count': current_pool.post_count,
                'new_posts': len(current_pool.post_ids)
            }
        
        # Compare post counts
        old_count = stored_pool['post_count']
        new_count = current_pool.post_count
        
        if new_count > old_count:
            # Get posts that need to be downloaded
            missing_posts = self.db.get_missing_posts(pool_id, current_pool.post_ids)
            
            logger.info(f"Pool '{current_pool.name}' has {new_count - old_count} new posts")
            return {
                'pool_id': pool_id,
                'pool_name': current_pool.name,
                'has_updates': True,
                'old_count': old_count,
                'new_count': new_count,
                'new_posts': len(missing_posts)
            }
        else:
            logger.info(f"Pool '{current_pool.name}' is up to date ({new_count} posts)")
            return {
                'pool_id': pool_id,
                'pool_name': current_pool.name,
                'has_updates': False,
                'old_count': old_count,
                'new_count': new_count,
                'new_posts': 0
            }


async def process_pool_ids(pool_ids, skip_existing=True, base_download_dir="."):
    """Process multiple pool IDs asynchronously with progress tracking."""
    downloader = E621Downloader(base_download_dir=base_download_dir)

    logger.info(f"Starting download process for {len(pool_ids)} pool(s)")
    logger.info(f"Base download directory: {base_download_dir}")
    logger.info(f"Skip existing files: {skip_existing}")

    all_failed = {}  # Store failed downloads for retrying later

    for i, pool_id in enumerate(pool_ids, 1):
        logger.info(f"Processing pool {i}/{len(pool_ids)}: {pool_id}")
        
        # Fetch pool info before creating a progress bar
        pool = await downloader.fetch_pool(pool_id)
        if not pool:
            logger.warning(f"Skipping pool {pool_id}, no valid data.")
            continue

        pool_name = pool.name
        logger.info(f"Pool details: '{pool_name}' ({pool.post_count} posts)")
        success, failed = [], []

        if skip_existing:
            # Get the number of posts that actually need downloading
            missing_posts = downloader.db.get_missing_posts(pool_id, pool.post_ids)
            total_images = len(missing_posts)
            
            if total_images == 0:
                tqdm.write(f"Pool {pool_name} is already complete!")
                logger.info(f"Pool {pool_name} is already complete!")
                continue
        else:
            total_images = pool.post_count

        # Create a new progress bar for this pool
        with tqdm(total=total_images, desc=f"Downloading {pool_name}", unit="image", position=0, leave=True) as progress_bar:
            async for post_result in downloader.download_pool(pool_id, progress_bar, skip_existing):
                if post_result["status"] == "downloaded":
                    success.append(post_result["post_id"])
                else:
                    failed.append(post_result["post_id"])

        # Print success message after pool download completes
        if success:
            tqdm.write(f"Successfully downloaded {len(success)} images for {pool_name}")

        # Store failed downloads for potential retrying
        if failed:
            all_failed[pool_id] = failed

    return all_failed  # Return failed downloads for retrying later


async def update_all_pools(base_download_dir="."):
    """Check all previously downloaded pools for updates and download new posts."""
    downloader = E621Downloader(base_download_dir=base_download_dir)
    
    # Get all pools from database
    all_pools = downloader.db.get_all_downloaded_pools()
    
    if not all_pools:
        logger.info("No pools found in database to update")
        return
    
    logger.info(f"Checking {len(all_pools)} pools for updates...")
    
    pools_with_updates = []
    
    # Check each pool for updates
    for pool_info in all_pools:
        pool_id = pool_info['id']
        update_info = await downloader.check_pool_for_updates(pool_id)
        
        if update_info and update_info['has_updates']:
            pools_with_updates.append(update_info)
    
    if not pools_with_updates:
        logger.info("All pools are up to date!")
        print("All pools are up to date!")
        return
    
    # Show summary of updates found
    logger.info(f"Found updates for {len(pools_with_updates)} pools:")
    print(f"\nFound updates for {len(pools_with_updates)} pools:")
    for update in pools_with_updates:
        update_msg = f"  - {update['pool_name']}: {update['old_count']} -> {update['new_count']} posts (+{update['new_posts']} new)"
        logger.info(update_msg)
        print(update_msg)
    
    # Ask user if they want to proceed with downloads
    try:
        response = input(f"\nDownload updates for {len(pools_with_updates)} pools? [Y/n]: ").strip().lower()
        if response and response not in ['y', 'yes']:
            logger.info("Update cancelled by user")
            print("Update cancelled by user")
            return
    except KeyboardInterrupt:
        logger.info("Update cancelled by user")
        print("\nUpdate cancelled by user")
        return
    
    # Download updates
    pool_ids_to_update = [update['pool_id'] for update in pools_with_updates]
    logger.info(f"Downloading updates for {len(pool_ids_to_update)} pools...")
    
    failed_downloads = await process_pool_ids(pool_ids_to_update, skip_existing=True, base_download_dir=base_download_dir)
    
    if failed_downloads:
        logger.warning(f"Some downloads failed: {failed_downloads}")
        print(f"⚠️  Some downloads failed: {len(failed_downloads)} pools had issues")
    else:
        logger.info("All pool updates completed successfully!")
        print("All pool updates completed successfully!")