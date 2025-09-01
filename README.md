# Sandy's e621 Pool Downloader
This is a little python package that I pretty much made for myself, since
I couldn't find any other script that would do this exactly how I wanted!

This downloads pools (specifically designed for comics) from e621.net.  
It will create a folder for each pool, named:  
**`{Pool Name} by {Artist Name}`**  

Inside each folder, it will download each image/gif/video in the pool, named:  
**`{Page Number}.{ext}`** (according to the order in the pool).  

Finally, it will create an **internet shortcut file (`.url`)** that will open the pool in your default browser.

---

## **📥 Installation**

### **1️⃣ Install pipx**
Make sure you have **Python 3.8+** installed. Then install pipx for isolated package management:

```bash
pip install pipx
pipx ensurepath
```

*Note: You'll need to restart your terminal after running `pipx ensurepath`.*

### **2️⃣ Install the CLI Tool**
Install the package globally with isolated dependencies:

```bash
pipx install .
```

### **3️⃣ Verify Installation**
After installation, you should be able to run:

```bash
e6 --help
```

If you see the help message, you're good to go! The `e6` command is now available globally.

## Usage
### **1️⃣ Download a single pool**
Run:
```bash
e6 123456
```

### **2️⃣ Download multiple pools**
Run:
```bash
e6 123456 987654 ...
```
You can specify multiple pools to download at once.

### **3️⃣ Download a pool by URL**
Run:
```bash
e6 https://e621.net/pool/123456
```

### **4️⃣ Enable debug logging** 
Want more details? Run:
```bash
e6 123456 --log-level=DEBUG
```

### **5️⃣ Update all previously downloaded pools**
Check all your downloaded pools for new posts and download them:
```bash
e6 --update
```

This will:
- Check all pools in your database for new posts
- Show you which pools have updates available
- Ask for confirmation before downloading
- Download only the new posts, maintaining existing numbering

You can also specify a custom download directory:
```bash
e6 --update -d /path/to/downloads
```

## Future Plans
- [x] Launch with arguments
- [x] Pool queue
- [ ] Live enqueueing
- [ ] Terminal GUI
    - [ ] Pool queue
    - [ ] Image queue
    - [ ] Download progress
- [x] PATH configuration
- [x] Skip existing
- [x] Download only missing
- [x] Download only new (via --update)
- [ ] Download resume