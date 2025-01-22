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
- Recompresses extracted images to reduce file size (optional, toggleable).
- Recreates `.cbz` files, overwriting the originals.

### Rename CBZ to CBR 🔃  
- Rename .cbz files to .cbr format or vice versa.

### New Features (Added) 🌟
- **Toggle Compression**: Enable or disable image compression with a single click.

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

---

## **Usage** 🛠️  

### **Start Full Processing**

1. Launch the tool and select your source folder containing manga image folders.
2. Click Start Full Processing to:
   - Compress images (optional, toggleable).
   - Bundle them into .cbz files.
   - Delete the original folders for a clean directory structure.
  
### **Reverse Process CBZ**

1. Select your source folder containing .cbz files.
2. Click Reverse Process CBZ to:
   - Extract .cbz archives into image folders.
   - Recompress the extracted images (optional, toggleable).
   - Repack the images back into .cbz files, overwriting the originals.
  
### **Convert CBZ to CBR**

1. Select your source folder containing .cbz or .cbr files.
2. Click Convert CBZ/CBR to rename .cbz files to .cbr format and vice versa.

### **Toggle Compression**

- Use the Compress On/Off button to enable or disable image compression.
  - **Checked**: Compression is enabled.
  - **Unchecked**: Compression is disabled.

---

## **Screenshots**

![image](https://github.com/user-attachments/assets/d55ba6c4-9fc8-44bc-a825-e0ad6c1a419b)


---

## **Contributing**

Feel free to contribute to the project by opening issues or submitting pull requests. Any improvements or new features are welcome.

