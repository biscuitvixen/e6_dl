from setuptools import setup, find_packages

setup(
    name="e6dl",
    version="1.0.0",
    packages=find_packages(include=["backend", "backend.*"]),
    install_requires=[
        "aiohttp",
        "aiofiles",
        "colorlog",
    ],
    entry_points={
        "console_scripts": [
            "e6dl=backend.main:cli",
        ],
    },
    author="Sandra Biscuit",
    description="A command-line tool to download pools from e621.",
    python_requires=">=3.7",
)
