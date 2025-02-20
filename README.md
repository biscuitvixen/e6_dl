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

### **1️⃣ Install Dependencies**
Make sure you have **Python 3.7+** installed. Then install the required dependencies:

```bash
pip install aiohttp aiofiles colorlog setuptools
```

## **2️⃣ Install the CLI Tool**
You can install the package as a system-wide command:

```bash
pip install --editable .
```

## **3️⃣ Verify Installation**
After installation, you should be able to run the following command:

```bash
e6dl --help
```

If you see the help message, you're good to go!

## Usage
### **1️⃣ Download a single pool**
Run:
```bash
e6dl 123456
```

### **2️⃣ Download multiple pools**
Run:
```bash
e6dl 123456 987654 ...
```
You can specify multiple pools to download at once.

### **3️⃣ Download a pool by URL**
Run:
```bash
e6dl https://e621.net/pool/123456
```

### **4️⃣ Enable debug logging** 
Want more details? Run:
```bash
e6dl 123456 --log-level=DEBUG
```

### **5️⃣ Using the Legacy Interface**
If you'd like to use the older — interactive — interface, you can still do so using:
```bash
python backend/main.py
```
This will ask you for the pool ID or URL, and download the pool to the current directory.
> 💡 **Note**: The CLI (e6dl) is the new default interface.

## Future Plans
- [x] Launch with arguments
- [x] Pool queue
- [ ] Live enqueueing
- [ ] Terminal GUI
    - [ ] Pool queue
    - [ ] Image queue
    - [ ] Download progress
- [ ] PATH configuration