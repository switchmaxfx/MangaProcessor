import os
import sys
import shutil
import zipfile
import subprocess
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QProgressBar, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QTextEdit, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# Zopfli integration (optional, requires zopfli installed)
try:
    import zopfli.zipfile
except ImportError:
    zopfli_available = False
else:
    zopfli_available = True

class ProcessingThread(QThread):
    update_console = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    processing_complete = pyqtSignal()
    
    def __init__(self, source_dir, processing_type, file_conversion, compress_images):
        super().__init__()
        self.source_dir = source_dir
        self.processing_type = processing_type
        self.file_conversion = file_conversion
        self.compress_images = compress_images  # New parameter to enable/disable compression
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

        image_files = self.find_image_files(self.source_dir)
        total_pages = len(image_files)
        processed_pages = 0

        temp_dir = os.path.join(self.source_dir, "temp_compressed")
        os.makedirs(temp_dir, exist_ok=True)

        for image_path in image_files:
            if self.stop_requested:
                self.update_console.emit("Processing stopped by user")
                break

            try:
                rel_path = os.path.relpath(image_path, self.source_dir)
                temp_image_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)

                # Compress images only if the toggle is enabled
                if self.compress_images:
                    self.compress_image(image_path, temp_image_path)
                    self.update_console.emit(f"Compressed: {image_path}")
                else:
                    # If compression is disabled, just copy the file
                    shutil.copy(image_path, temp_image_path)
                    self.update_console.emit(f"Copied: {image_path}")

                processed_pages += 1
                progress_percentage = int((processed_pages / total_pages) * 100)
                self.update_progress.emit(progress_percentage)

            except Exception as e:
                self.update_console.emit(f"Error processing {image_path}: {e}")

        if not self.stop_requested:
            self.create_cbz_from_temp(temp_dir)
            shutil.rmtree(temp_dir)
            self.delete_original_files(self.source_dir, temp_dir)
            self.update_console.emit("\nForward Processing Complete! UwU!")
            self.update_progress.emit(100)

    def find_image_files(self, directory):
        image_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_files.append(os.path.join(root, file))
        return image_files

    def compress_image(self, input_path, output_path):
        """Compress images using Pillow for JPEGs and pngquant for PNGs."""
        try:
            if input_path.lower().endswith(('.png')):
                self.compress_png_with_pngquant(input_path, output_path)
            elif input_path.lower().endswith(('.jpg', '.jpeg')):
                self.compress_jpeg_with_pillow(input_path, output_path)
            else:
                raise ValueError(f"Unsupported file format: {input_path}")
        except Exception as e:
            self.update_console.emit(f"Error compressing {input_path}: {e}")

    def compress_jpeg_with_pillow(self, input_path, output_path):
        """Compress JPEG/JPG images using Pillow."""
        try:
            image = Image.open(input_path)
            # Remove metadata to reduce file size
            image.info.pop('exif', None)
            # Use high quality (95) and optimize for better compression
            image.save(output_path, "JPEG", optimize=True, quality=90)
            self.update_console.emit(f"Compressed JPEG: {output_path}")
        except Exception as e:
            self.update_console.emit(f"Error compressing JPEG {input_path}: {e}")

    def compress_png_with_pngquant(self, input_path, output_path):
        """Compress PNG images using pngquant."""
        try:
            # Call pngquant to compress the PNG file
            subprocess.run(['pngquant', '--quality=75-80', input_path, '--output', output_path])
            self.update_console.emit(f"Compressed PNG: {output_path}")
        except Exception as e:
            self.update_console.emit(f"Error compressing PNG {input_path}: {e}")

    def create_cbz_from_temp(self, temp_dir):
        """Create CBZ files from compressed images in the temporary directory."""
        for root, dirs, files in os.walk(temp_dir):
            image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            if not image_files:
                continue

            rel_path = os.path.relpath(root, temp_dir)
            base_name = os.path.basename(rel_path) if rel_path != '.' else 'manga'
            cbz_name = f"{base_name}.cbz"
            cbz_path = os.path.join(self.source_dir, cbz_name)

            # Use Zopfli for efficient ZIP compression if available
            if zopfli_available:
                with zopfli.zipfile.ZipFile(cbz_path, 'w', compression=zopfli.zipfile.ZIP_DEFLATED) as zipf:
                    for file in sorted(image_files):
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(rel_path, file)
                        zipf.write(file_path, arcname=arcname)
                self.update_console.emit(f"Created CBZ (Zopfli): {cbz_name}")
            else:
                with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in sorted(image_files):
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(rel_path, file)
                        zipf.write(file_path, arcname=arcname)
                self.update_console.emit(f"Created CBZ: {cbz_name}")

    def delete_original_files(self, source_dir, temp_dir):
        """Delete original image files after compression."""
        for root, dirs, files in os.walk(source_dir, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                if file_path.endswith((".png", ".jpg", ".jpeg")):
                    os.remove(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                if dir_path != temp_dir:
                    shutil.rmtree(dir_path)

    def reverse_process_cbz_files(self):
        if not self.source_dir:
            self.update_console.emit("Please select a source folder.")
            return

        cbz_files = [f for f in os.listdir(self.source_dir) if f.lower().endswith('.cbz')]
        total_pages = self.count_total_pages(cbz_files)
        processed_pages = 0

        for cbz_file in cbz_files:
            if self.stop_requested:
                self.update_console.emit("Processing stopped by user")
                break

            try:
                full_cbz_path = os.path.join(self.source_dir, cbz_file)
                extract_folder = os.path.join(self.source_dir, os.path.splitext(cbz_file)[0])
                os.makedirs(extract_folder, exist_ok=True)

                with zipfile.ZipFile(full_cbz_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)

                image_files = self.find_image_files(extract_folder)
                for image_path in image_files:
                    if self.stop_requested:
                        self.update_console.emit("Processing stopped by user")
                        return

                    try:
                        # Compress images only if the toggle is enabled
                        if self.compress_images:
                            self.compress_image(image_path, image_path)
                            self.update_console.emit(f"Compressed: {image_path}")
                        else:
                            self.update_console.emit(f"Skipped compression for: {image_path}")

                        processed_pages += 1
                        progress_percentage = int((processed_pages / total_pages) * 100)
                        self.update_progress.emit(progress_percentage)
                    except Exception as e:
                        self.update_console.emit(f"Error compressing {image_path}: {e}")

                new_cbz_path = os.path.join(self.source_dir, cbz_file)
                # Use Zopfli for efficient ZIP compression if available
                if zopfli_available:
                    with zopfli.zipfile.ZipFile(new_cbz_path, 'w', compression=zopfli.zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(extract_folder):
                            for file in sorted(files):
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, extract_folder)
                                zipf.write(file_path, arcname=arcname)
                    self.update_console.emit(f"Repacked and Overwritten (Zopfli): {cbz_file}")
                else:
                    with zipfile.ZipFile(new_cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(extract_folder):
                            for file in sorted(files):
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, extract_folder)
                                zipf.write(file_path, arcname=arcname)
                    self.update_console.emit(f"Repacked and Overwritten: {cbz_file}")

                shutil.rmtree(extract_folder)

            except Exception as e:
                self.update_console.emit(f"Error processing {cbz_file}: {e}")

        self.update_console.emit("\nReverse Processing Complete!")

    def count_total_pages(self, cbz_files):
        total_pages = 0
        for cbz_file in cbz_files:
            try:
                full_cbz_path = os.path.join(self.source_dir, cbz_file)
                with zipfile.ZipFile(full_cbz_path, 'r') as zip_ref:
                    total_pages += len([name for name in zip_ref.namelist() 
                                        if any(name.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg'))])
            except Exception as e:
                self.update_console.emit(f"Error counting pages in {cbz_file}: {e}")
        return total_pages

    def convert_cbz_cbr(self):
        if not self.source_dir:
            self.update_console.emit("Please select a source folder.")
            return

        files_to_convert = [f for f in os.listdir(self.source_dir) if f.lower().endswith((".cbz", ".cbr"))]

        for file in files_to_convert:
            if self.stop_requested:
                self.update_console.emit("Conversion stopped by user")
                break

            old_path = os.path.join(self.source_dir, file)
            new_extension = ".cbr" if file.lower().endswith(".cbz") else ".cbz"
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

        main_layout = QVBoxLayout()

        self.source_folder_label = QLabel("Source Folder:")
        self.source_folder_input = QLineEdit()
        self.source_folder_input.setStyleSheet("background-color: #444444; color: #FFFFFF; border: 1px solid #666666; padding: 5px; font-size: 12px;")

        self.source_browse_button = QPushButton("Browse")
        self.source_browse_button.setStyleSheet("background-color: #555555; color: #FFFFFF; border: none; padding: 8px 16px;")
        self.source_browse_button.clicked.connect(self.browse_folder)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.source_folder_label)
        folder_layout.addWidget(self.source_folder_input)
        folder_layout.addWidget(self.source_browse_button)

        button_layout = QHBoxLayout()

        self.process_button = QPushButton("Start Full Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setStyleSheet("background-color: #00CC00; color: #FFFFFF; border: none; padding: 8px 16px;")

        self.reverse_process_button = QPushButton("Reverse Process CBZ")
        self.reverse_process_button.clicked.connect(self.start_reverse_processing)
        self.reverse_process_button.setStyleSheet("background-color: #0066CC; color: #FFFFFF; border: none; padding: 8px 16px;")

        self.convert_button = QPushButton("Convert CBZ/CBR")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setStyleSheet("background-color: #FF9900; color: #FFFFFF; border: none; padding: 8px 16px;")

        # Add the toggle button for compression
        self.compress_toggle_button = QPushButton("Compress On/Off")
        self.compress_toggle_button.setCheckable(True)  # Make it a toggle button
        self.compress_toggle_button.setChecked(True)  # Default to "On"
        self.compress_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #00CC00; color: #FFFFFF; border: none; padding: 8px 16px; max-width: 120px; width: 120px;
            }
            QPushButton:checked {
                background-color: #CC0000;
            }
        """)
        self.compress_toggle_button.clicked.connect(self.toggle_compression)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setStyleSheet("background-color: #CC0000; color: #FFFFFF; border: none; padding: 8px 16px; max-width: 80px; width: 80px;")
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.reverse_process_button)
        button_layout.addWidget(self.convert_button)
        button_layout.addWidget(self.compress_toggle_button)  # Add the toggle button here
        button_layout.addWidget(self.stop_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #666666; border-radius: 4px; background-color: #555555; text-align: center; } QProgressBar::chunk { background-color: #00CC00; }")

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #444444; color: #FFFFFF; border: 1px solid #666666; padding: 5px; font-size: 11px; font-family: 'Consolas', 'Courier New', monospace;")
        
        font = QFont()
        font.setPointSize(12)
        self.console_output.setFont(font)

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
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'forward', None, self.compress_toggle_button.isChecked())
        self.setup_thread(self.current_thread)
        self.current_thread.start()

    def start_reverse_processing(self):
        source_dir = self.source_folder_input.text()
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'reverse', None, self.compress_toggle_button.isChecked())
        self.setup_thread(self.current_thread)
        self.current_thread.start()

    def start_conversion(self):
        source_dir = self.source_folder_input.text()
        if not source_dir:
            self.console_output.append("Please select a source folder.")
            return
        self.current_thread = ProcessingThread(source_dir, 'convert', None, self.compress_toggle_button.isChecked())
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

    def toggle_compression(self):
        """Toggle the compression state and update the button color."""
        if self.compress_toggle_button.isChecked():
            self.compress_toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #00CC00; color: #FFFFFF; border: none; padding: 8px 16px; max-width: 120px; width: 120px;
                }
            """)
        else:
            self.compress_toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #CC0000; color: #FFFFFF; border: none; padding: 8px 16px; max-width: 120px; width: 120px;
                }
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    processor = MangaProcessor()
    processor.show()
    sys.exit(app.exec_())