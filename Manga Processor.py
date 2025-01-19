import os
import sys
import shutil
import zipfile
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QProgressBar, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QTextEdit, QWidget, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class ProcessingThread(QThread):
    update_console = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    processing_complete = pyqtSignal()
    
    def __init__(self, source_dir, processing_type, file_conversion, compress):
        super().__init__()
        self.source_dir = source_dir
        self.processing_type = processing_type
        self.file_conversion = file_conversion
        self.compress = compress  # New parameter for compression toggle
        self.stop_requested = False

    def run(self):
        try:
            if self.processing_type == 'forward':
                self.process_manga_folders()
            elif self.processing_type == 'reverse':
                self.reverse_process_cbz_files()
            elif self.processing_type == 'convert':
                self.convert_cbz_cbr()
        except Exception as e:
            self.update_console.emit(f"Error during processing: {e}")
        finally:
            self.processing_complete.emit()

    def stop_processing(self):
        self.stop_requested = True

    def process_manga_folders(self):
        if not self.source_dir:
            self.update_console.emit("Please select a source folder.")
            return

        # Find all image files in the source directory and subdirectories
        image_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_files.append(os.path.join(root, file))

        # Count total pages for progress tracking
        total_pages = len(image_files)
        processed_pages = 0

        # Create a temporary directory for compressed images
        temp_dir = os.path.join(self.source_dir, "temp_compressed")
        os.makedirs(temp_dir, exist_ok=True)

        # Compress and copy images to temp directory
        for image_path in image_files:
            # Check if stop was requested
            if self.stop_requested:
                self.update_console.emit("Processing stopped by user")
                break

            try:
                # Create the same relative path in temp directory
                rel_path = os.path.relpath(image_path, self.source_dir)
                temp_image_path = os.path.join(temp_dir, rel_path)

                # Ensure the directory exists
                os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)

                if self.compress:
                    # Open and compress the image
                    image = Image.open(image_path)

                    # Save compressed image
                    if image_path.lower().endswith(".png"):
                        # For PNG, use optimize and compress_level
                        image.save(temp_image_path, format="PNG", optimize=True, compress_level=9)
                    else:
                        # For JPG/JPEG, use optimize and quality
                        image.save(temp_image_path, optimize=True, quality=80)
                else:
                    # If compression is disabled, just copy the file
                    shutil.copy(image_path, temp_image_path)

                    # Ensure the file is properly closed after copying
                    try:
                        with open(temp_image_path, 'rb') as f:
                            pass  # Just open and close the file to ensure it's not locked
                    except Exception as e:
                        self.update_console.emit(f"Error ensuring file is closed: {e}")

                self.update_console.emit(f"Processed: {image_path}")

                # Update progress
                processed_pages += 1
                progress_percentage = int((processed_pages / total_pages) * 100)
                self.update_progress.emit(progress_percentage)

            except Exception as e:
                self.update_console.emit(f"Error processing {image_path}: {e}")

        # If processing was not stopped, create CBZ files
        if not self.stop_requested:
            self.create_cbz_from_temp(temp_dir)

            # Clean up temporary directory
            shutil.rmtree(temp_dir)

            # Delete original folders
            for root, dirs, files in os.walk(self.source_dir, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    if file_path.endswith((".png", ".jpg", ".jpeg")):
                        os.remove(file_path)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    if dir_path != temp_dir:
                        shutil.rmtree(dir_path)

            self.update_console.emit("\nForward Processing Complete! UwU!")
            self.update_progress.emit(100)

    def create_cbz_from_temp(self, temp_dir):
        """Create CBZ files from compressed images in the temporary directory"""
        # Group images into directories
        for root, dirs, files in os.walk(temp_dir):
            # Skip if no image files
            image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if not image_files:
                continue

            # Create CBZ name based on folder name
            rel_path = os.path.relpath(root, temp_dir)
            base_name = os.path.basename(rel_path) if rel_path != '.' else 'manga'
            cbz_name = f"{base_name}.cbz"
            cbz_path = os.path.join(self.source_dir, cbz_name)

            # Create CBZ file
            with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in sorted(image_files):
                    file_path = os.path.join(root, file)
                    # Use relative path within the zip
                    arcname = os.path.join(rel_path, file)
                    zipf.write(file_path, arcname=arcname)

                self.update_console.emit(f"Created CBZ: {cbz_name}")

    def reverse_process_cbz_files(self):
        if not self.source_dir:
            self.update_console.emit("Please select a source folder.")
            return

        # Find all CBZ files
        cbz_files = [
            f for f in os.listdir(self.source_dir) 
            if f.lower().endswith('.cbz')
        ]

        # Count total pages across all CBZ files
        total_pages = 0
        for cbz_file in cbz_files:
            try:
                full_cbz_path = os.path.join(self.source_dir, cbz_file)
                with zipfile.ZipFile(full_cbz_path, 'r') as zip_ref:
                    total_pages += len([name for name in zip_ref.namelist() 
                                        if any(name.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg'))])
            except Exception as e:
                self.update_console.emit(f"Error counting pages in {cbz_file}: {e}")

        # Set up progress tracking
        processed_pages = 0

        # Process each CBZ file
        for cbz_file in cbz_files:
            # Check if stop was requested
            if self.stop_requested:
                self.update_console.emit("Processing stopped by user")
                break

            try:
                # Full path of the CBZ file
                full_cbz_path = os.path.join(self.source_dir, cbz_file)

                # Step 1: Extract CBZ
                self.update_console.emit(f"\nProcessing CBZ: {cbz_file}")
                self.update_console.emit("Stage 1: Extracting CBZ")

                # Create extraction folder (same name as CBZ without extension)
                extract_folder = os.path.join(self.source_dir, os.path.splitext(cbz_file)[0])
                os.makedirs(extract_folder, exist_ok=True)

                # Extract the CBZ
                with zipfile.ZipFile(full_cbz_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)

                # Step 2: Compress extracted images
                self.update_console.emit("Stage 2: Compressing Extracted Images")
                image_files = [
                    os.path.join(root, file)
                    for root, _, files in os.walk(extract_folder)
                    for file in files
                    if file.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

                for image_path in image_files:
                    if self.stop_requested:
                        self.update_console.emit("Processing stopped by user")
                        return

                    try:
                        image = Image.open(image_path)
                        if self.compress:
                            image.save(image_path, optimize=True, quality=80)
                        self.update_console.emit(f"Compressed: {image_path}")

                        # Update progress
                        processed_pages += 1
                        progress_percentage = int((processed_pages / total_pages) * 100)
                        self.update_progress.emit(progress_percentage)
                    except Exception as e:
                        self.update_console.emit(f"Error compressing {image_path}: {e}")

                # Step 3: Repack into CBZ
                self.update_console.emit("Stage 3: Repacking into CBZ")
                new_cbz_path = os.path.join(self.source_dir, cbz_file)
                with zipfile.ZipFile(new_cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(extract_folder):
                        for file in sorted(files):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, extract_folder)
                            zipf.write(file_path, arcname=arcname)

                # Remove extracted folder
                shutil.rmtree(extract_folder)
                self.update_console.emit(f"Repacked and Overwritten: {cbz_file}")

            except Exception as e:
                self.update_console.emit(f"Error processing {cbz_file}: {e}")

        self.update_console.emit("\nReverse Processing Complete!")

    def convert_cbz_cbr(self):
        if not self.source_dir:
            self.update_console.emit("Please select a source folder.")
            return

        files_to_convert = [
            f for f in os.listdir(self.source_dir)
            if f.lower().endswith((".cbz", ".cbr", ".zip"))  # Include .zip files
        ]

        for file in files_to_convert:
            if self.stop_requested:
                self.update_console.emit("Conversion stopped by user")
                break

            old_path = os.path.join(self.source_dir, file)

            # Determine the new extension
            if file.lower().endswith(".cbz"):
                new_extension = ".cbr"
            elif file.lower().endswith(".cbr"):
                new_extension = ".cbz"
            elif file.lower().endswith(".zip"):
                new_extension = ".cbz"  # Convert .zip to .cbz
            else:
                continue

            new_path = os.path.join(self.source_dir, os.path.splitext(file)[0] + new_extension)

            try:
                os.rename(old_path, new_path)
                self.update_console.emit(f"Converted: {file} -> {os.path.basename(new_path)}")
            except Exception as e:
                self.update_console.emit(f"Error converting {file}: {e}")

        self.update_console.emit("\nFile Conversion Complete!")


class MangaProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manga Processing Tool")
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("background-color: #333333; color: #FFFFFF;")

        # Main layout
        main_layout = QVBoxLayout()

        # Folder paths
        self.source_folder_label = QLabel("Source Folder:")
        self.source_folder_input = QLineEdit()
        self.source_folder_input.setStyleSheet("background-color: #444444; color: #FFFFFF; border: 1px solid #666666; padding: 5px; font-size: 12px;")

        # Browse button
        self.source_browse_button = QPushButton("Browse")
        self.source_browse_button.setStyleSheet("background-color: #555555; color: #FFFFFF; border: none; padding: 8px 16px;")
        self.source_browse_button.clicked.connect(self.browse_folder)

        # Folder path layout
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.source_folder_label)
        folder_layout.addWidget(self.source_folder_input)
        folder_layout.addWidget(self.source_browse_button)

        # Button layout
        button_layout = QHBoxLayout()

        # Process button
        self.process_button = QPushButton("Start Full Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setStyleSheet("background-color: #00CC00; color: #FFFFFF; border: none; padding: 8px 16px;")

        # Reverse Process button
        self.reverse_process_button = QPushButton("Reverse Process CBZ")
        self.reverse_process_button.clicked.connect(self.start_reverse_processing)
        self.reverse_process_button.setStyleSheet("background-color: #0066CC; color: #FFFFFF; border: none; padding: 8px 16px;")

        # Convert CBZ/CBR/ZIP button
        self.convert_button = QPushButton("Convert CBZ/CBR/ZIP")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setStyleSheet("background-color: #FF9900; color: #FFFFFF; border: none; padding: 8px 16px;")

        # Compression toggle checkbox
        self.compress_checkbox = QCheckBox("Compress Images")
        self.compress_checkbox.setChecked(True)  # Default to checked (compression on)
        self.compress_checkbox.setStyleSheet("color: #FFFFFF; font-size: 12px;")

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setStyleSheet("background-color: #CC0000; color: #FFFFFF; border: none; padding: 8px 16px; max-width: 80px; width: 80px;")
        self.stop_button.setEnabled(False)

        # Add buttons and checkbox to button layout
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.reverse_process_button)
        button_layout.addWidget(self.convert_button)
        button_layout.addWidget(self.compress_checkbox)  # Add the checkbox here
        button_layout.addWidget(self.stop_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #666666; border-radius: 4px; background-color: #555555; text-align: center; } QProgressBar::chunk { background-color: #00CC00; }")

        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #444444; color: #FFFFFF; border: 1px solid #666666; padding: 5px; font-size: 11px; font-family: 'Consolas', 'Courier New', monospace;")
        
        font = QFont()
        font.setPointSize(12)
        self.console_output.setFont(font)

        # Add widgets to main layout
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("Console Output:"))
        main_layout.addWidget(self.console_output)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.current_thread = None

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.source_folder_input.setText(folder_path)

    def start_processing(self):
        source_dir = self.source_folder_input.text()
        compress = self.compress_checkbox.isChecked()  # Get the compression toggle state
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'forward', None, compress)
        self.setup_thread(self.current_thread)
        self.current_thread.start()

    def start_reverse_processing(self):
        source_dir = self.source_folder_input.text()
        compress = self.compress_checkbox.isChecked()  # Get the compression toggle state
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'reverse', None, compress)
        self.setup_thread(self.current_thread)
        self.current_thread.start()

    def start_conversion(self):
        source_dir = self.source_folder_input.text()
        compress = self.compress_checkbox.isChecked()  # Get the compression toggle state
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'convert', None, compress)
        self.setup_thread(self.current_thread)
        self.current_thread.start()

    def setup_thread(self, thread):
        thread.update_console.connect(self.update_console)
        thread.update_progress.connect(self.update_progress)
        thread.processing_complete.connect(self.processing_complete)
        self.process_button.setEnabled(False)
        self.reverse_process_button.setEnabled(False)
        self.convert_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)

    def stop_processing(self):
        if self.current_thread:
            self.current_thread.stop_processing()
            self.console_output.append("Stopping processing... Please wait.")

    def update_console(self, message):
        self.console_output.append(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def processing_complete(self):
        self.process_button.setEnabled(True)
        self.reverse_process_button.setEnabled(True)
        self.convert_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.current_thread = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    processor = MangaProcessor()
    processor.show()
    sys.exit(app.exec_())