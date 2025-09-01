import asyncio
import argparse
from backend.logger_config import set_log_level, logger
from backend.backend import process_pool_ids, update_all_pools

async def main():
    """Command-line interface for downloading pools."""
    parser = argparse.ArgumentParser(description="Download pools from e621.")
    parser.add_argument("pool_ids", nargs="*", help="List of pool IDs or URLs")
    parser.add_argument("-l", "--log-level", default="WARNING", help="Set logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--force-redownload", action="store_true", help="Redownload all files, even if they already exist")
    parser.add_argument("-d", "--download-dir", default=".", help="Base directory for downloads (default: current directory)")
    parser.add_argument("--update", action="store_true", help="Check all previously downloaded pools for updates and download new posts")

    args = parser.parse_args()

    # Set log level
    logger.info(f"Setting log level to {args.log_level}")
    set_log_level(args.log_level)

    # Handle update mode
    if args.update:
        if args.pool_ids:
            logger.warning("Pool IDs are ignored when using --update mode")
            print("⚠️  Pool IDs are ignored when using --update mode")
        
        logger.info("Checking all pools for updates...")
        await update_all_pools(base_download_dir=args.download_dir)
        return

    raw_ids = args.pool_ids

    if not raw_ids:
        logger.error("No pool IDs provided.")
        raw_ids = input("Enter pool IDs or URLs: ").split()

    logger.debug(f"Input: {raw_ids}") 

    # Extract numeric pool IDs from URLs if necessary
    pool_ids = [int(pool.split("/")[-1]) for pool in raw_ids if pool.split("/")[-1].isdigit()]

    if not pool_ids:
        logger.error("No valid pool IDs provided.")
        return

    try:
        skip_existing = not args.force_redownload
        total_posts = await process_pool_ids(pool_ids, skip_existing=skip_existing, base_download_dir=args.download_dir)
        logger.info(f"Download complete. {len(total_posts) if total_posts else 0} failed downloads.")
    except asyncio.CancelledError:
        logger.warning("Download process interrupted.")
    finally:
        logger.debug("Shutting down gracefully...")

def cli():
    """Entry point for console script"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Cancelling tasks...")

        loop = asyncio.get_event_loop()
        tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
        for task in tasks:
            task.cancel()

        try:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except Exception as e:
            logger.error(f"Exception during shutdown: {e}")

        logger.info("Exiting gracefully.")

if __name__ == "__main__":
    cli()