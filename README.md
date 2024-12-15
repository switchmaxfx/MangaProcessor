# Manga Processor Tool 📚  

A versatile and efficient tool for **compressing, organizing, and processing manga image folders into `.cbz` files** and reversing `.cbz` archives back into images. Designed with automation and user-friendliness in mind, the Manga Processor is ideal for manga enthusiasts looking to clean up and manage their collections.  

---

## Features  

### Forward Processing 🔄  
- Compresses images while maintaining visual quality.  
- Bundles optimized images into `.cbz` files.  
- Deletes original folders after processing for a clean directory structure.  

### Reverse Processing 🔃  
- Extracts `.cbz` archives back into image folders.  
- Recompresses extracted images to reduce file size.  
- Recreates `.cbz` files, overwriting the originals.

### Rename CBZ to CBR 🔃  
- Can also rename your CBZ files to CBR format. 

---

## Requirements
- **Python 3.x**
- **Pillow** - For image handling and compression.
    ```bash
   pip install pillow
- **PyQt5** - For the graphical user interface.
   ```bash
   pip install pyqt5

---

## Installation 

1. Clone the repository:
   ```bash
   git clone https://github.com/switchmaxfx/MangaProcessor.git
   cd MangaProcessor

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Run the script:
   ```bash
   python manga_processor.py

## **Usage** 🛠️  

1. Start the tool and select your source folder.  
2. Pick your mode:  
   - **Start Full Processing**: Compress and convert images into `.cbz`.  
   - **Reverse Process CBZ**: Extract and optimize images, then turns them back into `.cbz` files.  
3. Watch the progress bar and console for updates! 
4. Sit back, relax, and enjoy your perfectly processed manga. 

![pythonw_YxfDaiBmzl](https://github.com/user-attachments/assets/b8de3407-1e94-44e2-9b79-f87c5b961c90)

