import asyncio
import argparse
from backend.logger_config import set_log_level, logger
from backend.backend import process_pool_ids

async def main():
    """Command-line interface for downloading pools."""
    parser = argparse.ArgumentParser(description="Download pools from e621.")
    parser.add_argument("pool_ids", nargs="*", help="List of pool IDs or URLs")
    parser.add_argument("-l", "--log-level", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR)")

    args = parser.parse_args()

    # Set log level
    set_log_level(args.log_level)

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
        await process_pool_ids(pool_ids)
    except asyncio.CancelledError:
        logger.warning("Download process interrupted.")
    finally:
        logger.info("Shutting down gracefully...")

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