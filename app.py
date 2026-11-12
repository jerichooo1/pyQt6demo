import csv
import ctypes
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QMessageBox, QProgressBar, QPushButton, QRadioButton,
    QTextEdit, QVBoxLayout, QWidget
)
import qdarktheme


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(780, 680)
        self.setWindowIcon(QIcon("icon.png"))
        self.setWindowTitle("Quick System Cleaner")

        self.current_theme = "dark"
        self.space_before = 0.0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Theme toggle
        self.btn_theme = QPushButton("Switch to Light Mode")
        self.btn_theme.clicked.connect(self.toggle_theme)
        layout.addWidget(self.btn_theme)

        # Header
        self.label_header = QLabel("Quick System Cleaner")
        self.label_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.label_header)

        # Checkbox Options Group
        self.options_group = QGroupBox("Select items to clean")
        group_layout = QVBoxLayout(self.options_group)

        # Cache
        h_cache = QHBoxLayout()
        self.cb_cache = QCheckBox("System Cache Files")
        self.cb_cache.setChecked(True)
        self.btn_open_cache = QPushButton("Open Folder")
        self.btn_open_cache.setFixedWidth(100)
        self.btn_open_cache.clicked.connect(self.open_cache_folder)
        h_cache.addWidget(self.cb_cache)
        h_cache.addWidget(self.btn_open_cache)
        group_layout.addLayout(h_cache)

        # Temp
        h_temp = QHBoxLayout()
        self.cb_temp = QCheckBox("Temporary Files")
        self.cb_temp.setChecked(True)
        self.btn_open_temp = QPushButton("Open Folder")
        self.btn_open_temp.setFixedWidth(100)
        self.btn_open_temp.clicked.connect(self.open_temp_folder)
        h_temp.addWidget(self.cb_temp)
        h_temp.addWidget(self.btn_open_temp)
        group_layout.addLayout(h_temp)

        # Trash
        h_trash = QHBoxLayout()
        self.cb_trash = QCheckBox("Empty Trash/Recycle Bin")
        self.btn_open_trash = QPushButton("Open Folder")
        self.btn_open_trash.setFixedWidth(100)
        self.btn_open_trash.clicked.connect(self.open_trash_folder)
        h_trash.addWidget(self.cb_trash)
        h_trash.addWidget(self.btn_open_trash)
        group_layout.addLayout(h_trash)

        layout.addWidget(self.options_group)

        # Mode Selection
        self.mode_group = QGroupBox("Cleaning Mode")
        mode_layout = QVBoxLayout(self.mode_group)
        self.rb_quarantine = QRadioButton("Move files to Quarantine")
        self.rb_permanent = QRadioButton("Permanently Delete Files")
        self.rb_quarantine.setChecked(True)
        mode_layout.addWidget(self.rb_quarantine)
        mode_layout.addWidget(self.rb_permanent)
        layout.addWidget(self.mode_group)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Scan System")
        self.btn_pdf = QPushButton("Export to PDF")
        self.btn_txt = QPushButton("Export to Plain Text")
        self.btn_pdf.setEnabled(False)
        self.btn_txt.setEnabled(False)
        

        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_txt.clicked.connect(self.export_to_txt)
        self.btn_pdf.clicked.connect(self.export_to_pdf) 
        


        buttons_layout.addWidget(self.btn_scan)
        buttons_layout.addWidget(self.btn_pdf)
        buttons_layout.addWidget(self.btn_txt)
        layout.addLayout(buttons_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Results Group
        self.results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(self.results_group)
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setPlaceholderText("Click 'Scan System' to see details of junk files.")
        results_layout.addWidget(self.txt_results)
        layout.addWidget(self.results_group)

        # History and Quarantine navigation
        nav_layout = QHBoxLayout()
        self.btn_open_logs_history = QPushButton("View Deletion History")
        self.btn_open_logs_history.clicked.connect(self.open_deletion_history)
        self.btn_open_quarantine = QPushButton("Open Quarantine Folder")
        self.btn_open_quarantine.clicked.connect(self.open_quarantine_folder)
        nav_layout.addWidget(self.btn_open_logs_history)
        nav_layout.addWidget(self.btn_open_quarantine)
        layout.addLayout(nav_layout)

        # Clean Button
        self.btn_clean = QPushButton("Clean Selected")
        self.btn_clean.clicked.connect(self.confirm_cleaning)
        self.btn_clean.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 6px;")
        self.btn_clean.setEnabled(False)
        layout.addWidget(self.btn_clean)

        

    #Themes & Path Helpers
    def toggle_theme(self):
        if self.current_theme == "dark":
            qdarktheme.setup_theme("light")
            self.btn_theme.setText("Switch to Dark Mode")
            self.current_theme = "light"
        else:
            qdarktheme.setup_theme("dark")
            self.btn_theme.setText("Switch to Light Mode")
            self.current_theme = "dark"

    def get_quarantine_folder(self):
        folder = Path.home() / "QuickSystemCleaner" / "Quarantine"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_log_file(self):
        log_folder = Path.home() / "QuickSystemCleaner" / "Logs"
        log_folder.mkdir(parents=True, exist_ok=True)
        return log_folder / "deletion_history.csv"

    def open_cache_folder(self):
        cache_path = "C:\\Windows\\SoftwareDistribution\\Download"
        if os.path.exists(cache_path):
            os.startfile(cache_path)
        else:
            self.txt_results.append(f"Directory not found: {cache_path}")

    def open_temp_folder(self):
        temp_path = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
        if os.path.exists(temp_path):
            os.startfile(temp_path)
        else:
            self.txt_results.append(f"Directory not found: {temp_path}")

    def open_trash_folder(self):
        try:
            os.startfile("shell:RecycleBinFolder")
        except Exception:
            self.txt_results.append("Unable to open Recycle Bin.")

    def open_quarantine_folder(self):
        os.startfile(str(self.get_quarantine_folder()))

    def open_deletion_history(self):
        log_file = self.get_log_file()
        if log_file.exists():
            os.startfile(str(log_file))
        else:
            QMessageBox.information(self, "No History", f"No deletion history found.\n\nLocation:\n{log_file}")

    def get_free_disk_space_gb(self):
        try:
            _, _, free = shutil.disk_usage("C:\\")
            return free / (1024 ** 3)
        except Exception:
            return 0.0

    def get_dir_size(self, path_str):
        total_size = 0
        file_count = 0
        path = Path(path_str)
        if not path.exists():
            return 0, 0

        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                    file_count += 1
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        return total_size, file_count

    # --- Scanning ---
    def start_scan(self):
        self.txt_results.clear()
        self.space_before = self.get_free_disk_space_gb()
        self.txt_results.append(f"Current Free Disk Space: {self.space_before:.2f} GB\n")
        self.txt_results.append("Starting system scan...\n")
        self.progress_bar.setValue(10)

        overall_size = 0

        if self.cb_temp.isChecked():
            temp_path = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
            size, count = self.get_dir_size(temp_path)
            size_mb = size / (1024 * 1024)
            overall_size += size_mb
            self.txt_results.append(f"Temporary Files ({temp_path}):\n  -> Found {count} files ({size_mb:.2f} MB)")
        self.progress_bar.setValue(45)

        if self.cb_cache.isChecked():
            cache_path = "C:\\Windows\\SoftwareDistribution\\Download"
            size, count = self.get_dir_size(cache_path)
            size_mb = size / (1024 * 1024)
            overall_size += size_mb
            self.txt_results.append(f"Cache Files ({cache_path}):\n  -> Found {count} files ({size_mb:.2f} MB)")
        self.progress_bar.setValue(80)

        if self.cb_trash.isChecked():
            trash_path = "C:\\$Recycle.Bin"
            size, count = self.get_dir_size(trash_path)
            size_mb = size / (1024 * 1024)
            overall_size += size_mb
            self.txt_results.append(f"Recycle Bin ({trash_path}):\n  -> Found {count} files ({size_mb:.2f} MB)")

        self.progress_bar.setValue(100)
        self.txt_results.append("\n" + "=" * 45)
        self.txt_results.append(f"Total potential space to clean: {overall_size:.2f} MB")
        self.txt_results.append("=" * 45)

        self.btn_clean.setEnabled(True)
        self.btn_pdf.setEnabled(True)
        self.btn_txt.setEnabled(True)
        

    
    # --- Cleaning ---
    def confirm_cleaning(self):
        if not (self.cb_temp.isChecked() or self.cb_cache.isChecked() or self.cb_trash.isChecked()):
            QMessageBox.information(self, "Nothing Selected", "Please select at least one item to clean.")
            return

        if self.rb_quarantine.isChecked():
            title = "Confirm Quarantine"
            message = "Move the selected files to Quarantine?"
            info = "Files will be moved to the quarantine folder. (Recycle Bin is skipped in Quarantine Mode)."
        else:
            title = "Confirm Permanent Deletion"
            message = "Are you sure you want to permanently delete the selected files?"
            info = "This action cannot be undone."

        reply = QMessageBox.warning(
            self, title, message + "\n\n" + info,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.execute_cleaning()

    def execute_cleaning(self):
        self.progress_bar.setValue(0)
        is_quarantine = self.rb_quarantine.isChecked()

        paths = []
        if self.cb_temp.isChecked():
            paths.append(("Temporary Files", os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))))
        if self.cb_cache.isChecked():
            paths.append(("Cache Files", "C:\\Windows\\SoftwareDistribution\\Download"))

        total_cleaned_bytes = 0
        total_count = 0
        total_failed = 0

        # Process directories
        for name, folder in paths:
            self.txt_results.append(f"\nProcessing {name}...")
            if is_quarantine:
                size, count, failed = self.quarantine_dir_files(folder)
            else:
                size, count, failed = self.delete_dir_files(folder)

            total_cleaned_bytes += size
            total_count += count
            total_failed += failed
            self.txt_results.append(f"-> Done: {count} processed, {failed} failed.")

        # Process Recycle Bin
        if self.cb_trash.isChecked():
            if not is_quarantine:
                self.txt_results.append("\nEmptying Recycle Bin...")
                if self.empty_recycle_bin():
                    self.txt_results.append("-> Recycle Bin emptied successfully.")
                    self.batch_log_actions([("Recycle Bin", "C:\\$Recycle.Bin", 0, "Permanent Deletion")])
                else:
                    self.txt_results.append("-> Failed to empty Recycle Bin.")
            else:
                self.txt_results.append("\n-> Skipped: Recycle Bin not supported in Quarantine mode.")

        # Summary
        self.progress_bar.setValue(100)
        space_after = self.get_free_disk_space_gb()
        cleaned_mb = total_cleaned_bytes / (1024 * 1024)

        self.txt_results.append("\n" + "=" * 45)
        self.txt_results.append("CLEANING COMPLETE!")
        self.txt_results.append(f"Processed: {total_count} files ({cleaned_mb:.2f} MB)")
        self.txt_results.append(f"Failed/Locked: {total_failed} files")
        self.txt_results.append(f"Free Disk Space: {self.space_before:.2f} GB -> {space_after:.2f} GB")
        self.txt_results.append("=" * 45)
        self.btn_clean.setEnabled(False)

    def delete_dir_files(self, path_str):
        path = Path(path_str)
        if not path.exists():
            return 0, 0, 0

        cleaned_size, count, failed = 0, 0, 0
        logs = []

        for entry in list(path.rglob("*")):
            if entry.is_file():
                try:
                    fsize = entry.stat().st_size
                    entry.unlink()
                    logs.append((entry.name, str(entry), fsize, "Permanent Deletion"))
                    cleaned_size += fsize
                    count += 1
                except (PermissionError, FileNotFoundError, OSError):
                    failed += 1

        self.batch_log_actions(logs)
        return cleaned_size, count, failed

    def quarantine_dir_files(self, path_str):
        source = Path(path_str)
        if not source.exists():
            return 0, 0, 0

        quarantine_path = self.get_quarantine_folder()
        session_folder = quarantine_path / datetime.now().strftime("quarantine_%Y%m%d_%H%M%S")
        session_folder.mkdir(parents=True, exist_ok=True)

        moved_size, count, failed = 0, 0, 0
        logs = []

        for entry in source.rglob("*"):
            if entry.is_file():
                try:
                    fsize = entry.stat().st_size
                    rel = entry.relative_to(source)
                    dest = session_folder / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    shutil.move(str(entry), str(dest))
                    logs.append((entry.name, str(entry), fsize, "Quarantine"))
                    moved_size += fsize
                    count += 1
                except (PermissionError, FileNotFoundError, OSError):
                    failed += 1

        self.batch_log_actions(logs)
        return moved_size, count, failed

    def batch_log_actions(self, records):
        """Batches writes to disk so we do not open/close the CSV thousands of times."""
        if not records:
            return
        log_file = self.get_log_file()
        file_exists = log_file.exists()

        try:
            with open(log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["File Name", "Original Path", "File Size (Bytes)", "Date", "Cleaning Mode"])
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for name, path_str, size, mode in records:
                    writer.writerow([name, path_str, size, now, mode])
        except Exception as e:
            self.txt_results.append(f"[Log Error]: {e}")

    def empty_recycle_bin(self):
        try:
            # SHERB_NOCONFIRMATION = 0x00000001, SHERB_NOPROGRESSUI = 0x00000002, SHERB_NOSOUND = 0x00000004
            flags = 0x00000001 | 0x00000002 | 0x00000004
            res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            return res == 0
        except Exception:
            return False

    #Exports 
    def export_to_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf)")
        if file_path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            self.txt_results.document().print(printer)

    def export_to_txt(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Text", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.txt_results.toPlainText())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    win = Window()
    win.show()
    sys.exit(app.exec())

