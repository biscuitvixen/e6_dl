""" Handles API requests to e621.net """

import requests
from logger_config import logger

USER_AGENT = "sandydownloader/2.0 (by @biscuit_fox)";
API_URL = "https://e621.net";

class E621Client:
    """Handles API requests to e621.net"""

    def __init__(self):
        self.base_url = API_URL
        self.headers = {
            "User-Agent": USER_AGENT
        }
        logger.debug("E621Client initialized with base URL: %s", self.base_url)

    def make_request(self, url, params=None):
        """Handles GET requests to the API"""
        logger.debug("Making request to URL: %s with params: %s", url, params)
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            logger.debug("Request to %s successful", url)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Request to %s failed: %s", url, e)
            return None

    def get_pool(self, pool_id):
        url = f"{self.base_url}/pools/{pool_id}.json"
        logger.debug("Fetching pool with ID: %s", pool_id)
        response = self.make_request(url)
        if response:
            logger.debug("Pool %s fetched successfully", pool_id)
        return response
    
    def get_post(self, post_id):
        url = f"{self.base_url}/posts/{post_id}.json"
        logger.debug("Fetching post with ID: %s", post_id)
        response = self.make_request(url)
        if response:
            logger.debug("Post %s fetched successfully", post_id)
        return response
