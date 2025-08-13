import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

class SearchThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    match_found = QtCore.pyqtSignal(str, int, str)
    search_done = QtCore.pyqtSignal()

    def __init__(self, folder, word):
        super().__init__()
        self.folder = folder
        self.word = word.lower()
        self._running = True

    def run(self):
        txt_files = []
        for root, _, files in os.walk(self.folder):
            for file in files:
                if file.lower().endswith(".txt"):
                    txt_files.append(os.path.join(root, file))

        total_files = len(txt_files)
        for i, filepath in enumerate(txt_files):
            if not self._running:
                break
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        if self.word in line.lower():
                            self.match_found.emit(filepath, line_num, line.strip())
            except Exception as e:
                pass

            self.progress.emit(int((i + 1) / total_files * 100))

        self.search_done.emit()

    def stop(self):
        self._running = False


class SearchApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ti Search")
        self.setGeometry(200, 200, 900, 600)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: white; font-family: Consolas; }
            QPushButton { background-color: #1f1f1f; border: 1px solid #333; padding: 5px; }
            QPushButton:hover { background-color: #333; }
            QLineEdit { background-color: #1e1e1e; border: 1px solid #333; padding: 4px; }
            QProgressBar { border: 1px solid #555; text-align: center; color: white; }
            QHeaderView::section { background-color: #1f1f1f; color: white; }
        """)

        layout = QtWidgets.QVBoxLayout()

        # Folder selection
        folder_layout = QtWidgets.QHBoxLayout()
        self.folder_input = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(QtWidgets.QLabel("Folder:"))
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # Search word
        word_layout = QtWidgets.QHBoxLayout()
        self.word_input = QtWidgets.QLineEdit()
        word_layout.addWidget(QtWidgets.QLabel("Word:"))
        word_layout.addWidget(self.word_input)
        layout.addLayout(word_layout)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start Search")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.save_btn = QtWidgets.QPushButton("Save Results")
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        # Progress bar + match counter
        self.progress_bar = QtWidgets.QProgressBar()
        self.match_label = QtWidgets.QLabel("Matches: 0")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.match_label)

        # Table for matches
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["File Path", "Line Number", "Line Text"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Connections
        self.start_btn.clicked.connect(self.start_search)
        self.stop_btn.clicked.connect(self.stop_search)
        self.save_btn.clicked.connect(self.save_results)

        self.search_thread = None
        self.match_count = 0

    def browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)

    def start_search(self):
        folder = self.folder_input.text().strip()
        word = self.word_input.text().strip()
        if not folder or not os.path.isdir(folder) or not word:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a valid folder and enter a search word.")
            return

        self.table.setRowCount(0)
        self.match_count = 0
        self.match_label.setText("Matches: 0")
        self.progress_bar.setValue(0)
        self.save_btn.setEnabled(False)

        self.search_thread = SearchThread(folder, word)
        self.search_thread.progress.connect(self.progress_bar.setValue)
        self.search_thread.match_found.connect(self.add_match)
        self.search_thread.search_done.connect(self.search_done)
        self.search_thread.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def add_match(self, filepath, line_num, line_text):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(filepath))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(line_num)))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(line_text))
        self.match_count += 1
        self.match_label.setText(f"Matches: {self.match_count}")

    def stop_search(self):
        if self.search_thread:
            self.search_thread.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def search_done(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(True)

    def save_results(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Results", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                for row in range(self.table.rowCount()):
                    f.write(f"{self.table.item(row, 0).text()} | Line {self.table.item(row, 1).text()} | {self.table.item(row, 2).text()}\n")
            QtWidgets.QMessageBox.information(self, "Saved", "Results saved successfully!")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SearchApp()
    window.show()
    sys.exit(app.exec_())

