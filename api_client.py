""" Handles API requests to e621.net """

import requests

USER_AGENT = "sandydownloader/2.0 (by @biscuit_fox)";
API_URL = "https://e621.net";

class E621Client:
    """Handles API requests to e621.net"""

    def __init__(self):
        self.base_url = API_URL
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def make_request(self, url, params=None):
        """Handles GET requests to the API"""
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_pool(self, pool_id):
        url = f"{self.base_url}/pools/{pool_id}.json"
        response = self.make_request(url)
        return response
    
    def get_post(self, post_id):
        url = f"{self.base_url}/posts/{post_id}.json"
        response = self.make_request(url)
        return response
