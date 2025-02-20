""" Handles API requests to e621.net """

import aiohttp
from backend.logger_config import logger

USER_AGENT = "sandydownloader/2.0 (by @biscuit_fox)"
API_URL = "https://e621.net"

class E621Client:
    """Handles asynchronous API requests to e621.net"""

    def __init__(self):
        self.base_url = API_URL
        self.headers = {
            "User-Agent": USER_AGENT
        }
        logger.debug("E621Client initialized with base URL: %s", self.base_url)

    async def make_request(self, url, params=None):
        """Handles GET requests to the API asynchronously."""
        logger.debug("Making request to URL: %s with params: %s", url, params)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        logger.debug("Request to %s successful", url)
                        return await response.json()
                    else:
                        logger.error("Request to %s failed with status: %s", url, response.status)
                        return None
            except aiohttp.ClientError as e:
                logger.error("Request to %s failed: %s", url, e)
                return None

    async def get_pool(self, pool_id):
        """Fetch a pool by ID asynchronously."""
        url = f"{self.base_url}/pools/{pool_id}.json"
        logger.debug("Fetching pool with ID: %s", pool_id)
        response = await self.make_request(url)
        if response:
            logger.debug("Pool %s fetched successfully", pool_id)
        return response
    
    async def get_post(self, post_id):
        """Fetch a post by ID asynchronously."""
        url = f"{self.base_url}/posts/{post_id}.json"
        logger.debug("Fetching post with ID: %s", post_id)
        response = await self.make_request(url)
        if response:
            logger.debug("Post %s fetched successfully", post_id)
        return response
