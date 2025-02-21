from setuptools import setup, find_packages

setup(
    name="e6dl",
    version="1.0.0",
    packages=find_packages(include=["backend", "backend.*"]),
    py_modules=["cli_entry"],
    install_requires=[
        "aiohttp",
        "aiofiles",
        "colorlog",
    ],
    entry_points={
        "console_scripts": [
            "e6dl=cli_entry:cli",
        ],
    },
    author="Sandra Biscuit",
    description="A command-line tool to download pools from e621.",
    python_requires=">=3.7",
)
