import asyncio
from api_client import E621Client
from models import Pool, Post
from downloader import download_image
from utils import create_directory, create_internet_shortcut


async def main():
    """Main program execution."""
    client = E621Client()

    while True:
        user_input = input("\nEnter the ID or URL of the pool to download: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            pool_id = int(user_input.split("/")[-1])
        except ValueError:
            print("Invalid input. Please enter a valid pool ID.")
            continue

        print(f"Fetching pool {pool_id}...")

        pool_data = client.get_pool(pool_id)
        if not pool_data:
            print("Failed to retrieve pool.")
            continue

        pool = Pool(pool_data)
        print(f"Found pool: {pool.name}, {pool.post_count} posts.")

        if not pool.post_ids:
            print("No posts found in this pool.")
            continue

        first_post_data = client.get_post(pool.post_ids[0])
        if not first_post_data:
            print("Failed to retrieve post data.")
            continue

        first_post = Post(first_post_data)
        if first_post.artists:
            artist = first_post.artists[1] if first_post.artists[0] == "conditional_dnp" and len(first_post.artists) > 1 else first_post.artists[0]
        else:
            artist = "Unknown Artist"

        working_dir = create_directory(pool.name, artist)
        create_internet_shortcut(f"https://e621.net/pools/{pool.id}", working_dir, working_dir)

        # Download all posts
        tasks = [
            download_image(Post(client.get_post(post_id)), i, working_dir)
            for i, post_id in enumerate(pool.post_ids)
        ]
        await asyncio.gather(*tasks)

        print("Pool download complete!\n")
        retry = input("Download another pool? (y/n): ").strip().lower()
        if retry != "y":
            break


if __name__ == "__main__":
    asyncio.run(main())
