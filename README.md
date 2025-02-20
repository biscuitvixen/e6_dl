# Sandy's e621 Pool Downloader
This is a little python package that I pretty much made for myself, since
I couldn't find any other script that would do this exactly how I wanted!

<div align="center">
  <h1>> This is a work in progress! <</h1>
</div>

This downloads pools (specifically designed for comics) from e621.net.
It will create a folder for each pool, named: `{Pool Name} by {Artist Name}`. 
Inside each folder, it will download each image/gif/video in the pool, named:
`{Page Number}.{ext}` according to the order in the pool. Finally, it will
create an internet shortcut file (`.url`) that will open the pool in your
default browser.

## Installation

### Dependencies
In order to use this script you will need to install the following:
- `requests`
- `colorlog`

```bash
pip install requests colorlog
```

## Usage
Launch the script with the following command:
```bash
python main.py
```
You will be prompted to enter the URL or ID of the pool you want to download.
Simply paste the URL or ID and press enter. The script will then download the
pool to the current directory.

> ## > This is the current, *temporary*, legacy interface <

## Future Plans
- [ ] Launch with arguments
- [ ] Pool queue
- [ ] Live enqueueing
- [ ] Terminal GUI
    - [ ] Pool queue
    - [ ] Image queue
    - [ ] Download progress
- [ ] PATH configuration