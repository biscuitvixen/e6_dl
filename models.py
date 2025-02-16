""" Class structures for storing e621 api data """

class Pool:
    """Represents a pool on e621.net"""
    def __init__(self, data):
        print("Pool data:")
        print(data)
        try:
            pool_data = data  # e621 API returns a list
            self.id = pool_data["id"]
            self.name = pool_data["name"].replace("_", " ")
            self.post_ids = pool_data["post_ids"]
            self.creator_name = pool_data["creator_name"]
            self.post_count = pool_data["post_count"]
        except (IndexError, KeyError):
            raise ValueError("Invalid pool data received.")

class Post:
    """Represents a post on e621.net"""
    def __init__(self, data):
        print("Post data:")
        print(data)
        try:
            post_data = data["post"]  # e621 API returns a list
            self.artists = post_data["tags"]["artist"]
            self.id = post_data["id"]
            self.is_deleted = post_data["flags"]["deleted"]
            self.file_url = post_data["file"]["url"]
            self.file_ext = post_data["file"]["ext"]
        except (IndexError, KeyError):
            raise ValueError("Invalid post data received.")