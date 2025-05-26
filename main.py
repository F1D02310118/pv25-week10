import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QMenu, QAction, QTabWidget, QInputDialog
)
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import Qt


class BookDatabase:
    def __init__(self, db_name="perpustakaan.sql"):
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(db_name)
        self.db.open()
        self._create_table()

    def _create_table(self):
        query = QSqlQuery()
        query.exec("""
            CREATE TABLE IF NOT EXISTS Buku (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Judul TEXT NOT NULL,
                Pengarang TEXT NOT NULL,
                Tahun INTEGER NOT NULL
            );
        """)

    def insert(self, title, author, year):
        if not title or not author or not year.isdigit():
            return False
        query = QSqlQuery()
        query.prepare("INSERT INTO Buku (Judul, Pengarang, Tahun) VALUES (?, ?, ?)")
        query.addBindValue(title)
        query.addBindValue(author)
        query.addBindValue(int(year))
        return query.exec()

    def update(self, field, value, book_id):
        query = QSqlQuery()
        query.prepare(f"UPDATE Buku SET {field} = ? WHERE ID = ?")
        query.addBindValue(value)
        query.addBindValue(book_id)
        return query.exec()

    def delete(self, book_id):
        query = QSqlQuery()
        query.prepare("DELETE FROM Buku WHERE ID = ?")
        query.addBindValue(book_id)
        return query.exec()

    def fetch(self, keyword=""):
        query = QSqlQuery()
        if keyword:
            query.prepare("SELECT * FROM Buku WHERE Judul LIKE ?")
            query.addBindValue(f"%{keyword}%")
        else:
            query.prepare("SELECT * FROM Buku")
        query.exec()
        return query

    def export_csv(self, path):
        query = QSqlQuery("SELECT * FROM Buku")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Judul", "Pengarang", "Tahun"])
            while query.next():
                writer.writerow([query.value(i) for i in range(4)])


class BookTable(QTableWidget):
    def __init__(self, db: BookDatabase):
        super().__init__()
        self.db = db
        self.columns = ["ID", "Judul", "Pengarang", "Tahun"]
        self.keyword = ""
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(self.columns)
        self.refresh()

        self.cellDoubleClicked.connect(self.edit_cell_dialog)

    def refresh(self):
        self.blockSignals(True)
        data = []
        query = self.db.fetch(self.keyword)
        while query.next():
            data.append([query.value(i) for i in range(4)])

        self.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if j == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(i, j, item)

        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)
        self.blockSignals(False)

    def set_filter(self, keyword):
        self.keyword = keyword
        self.refresh()

    def edit_cell_dialog(self, row, col):
        if col == 0:
            return

        current_value = self.item(row, col).text()
        field = self.columns[col]
        book_id = int(self.item(row, 0).text())

        new_value, ok = QInputDialog.getText(
            self, f"Edit {field}", f"{field}:", QLineEdit.Normal, current_value
        )

        if ok and new_value.strip():
            self.db.update(field, new_value.strip(), book_id)
            self.refresh()
            if col < 3:
                self.setCurrentCell(row, col + 1)


class BookApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manajemen Buku")
        self.setFixedSize(800, 500)
        self.db = BookDatabase()
        self._setup_menu()
        self._setup_ui()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        self.save_action = QAction("Simpan", self)
        self.export_action = QAction("Ekspor ke CSV", self)
        self.exit_action = QAction("Keluar", self)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.export_action)
        file_menu.addAction(self.exit_action)

        edit_menu = menubar.addMenu("Edit")
        self.search_action = QAction("Cari Judul", self)
        self.delete_action = QAction("Hapus Data", self)
        edit_menu.addAction(self.search_action)
        edit_menu.addAction(self.delete_action)

        self.save_action.triggered.connect(self.save)
        self.export_action.triggered.connect(self.export)
        self.exit_action.triggered.connect(self.close)
        self.search_action.triggered.connect(self.trigger_search)
        self.delete_action.triggered.connect(self.delete)

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab Data Buku
        data_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Lalu Maulana Rizki Hidayat - F1D02310118"))

        self.input_title = QLineEdit()
        self.input_author = QLineEdit()
        self.input_year = QLineEdit()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Cari judul...")
        self.input_search.textChanged.connect(self.trigger_search)

        form = QFormLayout()
        form.addRow("Judul:", self.input_title)
        form.addRow("Pengarang:", self.input_author)
        form.addRow("Tahun:", self.input_year)

        self.table = BookTable(self.db)

        save_btn = QPushButton("Simpan")
        delete_btn = QPushButton("Hapus Data")
        delete_btn.setStyleSheet("background-color: orange; font-weight: bold;")

        save_btn.clicked.connect(self.save)
        delete_btn.clicked.connect(self.delete)

        layout.addLayout(form)
        layout.addWidget(save_btn)
        layout.addWidget(self.input_search)
        layout.addWidget(self.table)
        layout.addWidget(delete_btn)
        data_tab.setLayout(layout)

        # Tab Ekspor
        export_tab = QWidget()
        export_layout = QVBoxLayout()
        export_label = QLabel("Klik tombol di bawah untuk ekspor data ke CSV")
        export_btn = QPushButton("Ekspor ke CSV")
        export_btn.clicked.connect(self.export)
        export_layout.addWidget(export_label)
        export_layout.addWidget(export_btn)
        export_tab.setLayout(export_layout)

        self.tabs.addTab(data_tab, "Data Buku")
        self.tabs.addTab(export_tab, "Ekspor")

    def save(self):
        title = self.input_title.text().strip()
        author = self.input_author.text().strip()
        year = self.input_year.text().strip()
        if self.db.insert(title, author, year):
            self.input_title.clear()
            self.input_author.clear()
            self.input_year.clear()
            self.table.refresh()
        else:
            QMessageBox.warning(self, "Input Salah", "Harap isi semua kolom dengan benar! Tahun harus angka.")

    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data yang dipilih!")
            return

        book_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(
            self, "Konfirmasi", f"Hapus buku ID {book_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.delete(book_id)
            self.table.refresh()

    def export(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "data_buku.csv", "CSV Files (*.csv)")
        if filename:
            if not filename.endswith(".csv"):
                filename += ".csv"
            self.db.export_csv(filename)
            QMessageBox.information(self, "Sukses", "Data berhasil diekspor!")

    def trigger_search(self):
        self.table.set_filter(self.input_search.text().strip())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookApp()
    window.show()
    sys.exit(app.exec())