import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLineEdit, QPushButton, QTextEdit, QLabel, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QProgressBar, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from api_functions import get_product_by_barcode, search_products, extract_kcal

class SearchWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, search_type, query):
        super().__init__()
        self.search_type = search_type
        self.query = query
    
    def run(self):
        try:
            if self.search_type == "barcode":
                result = get_product_by_barcode(self.query)
                if result.get("product"):
                    result = {"products": [result["product"]]}
                else:
                    result = {"products": []}
            else:
                result = search_products(self.query, page_size=10)
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"Ошибка: {str(e)}")

class CalorieFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Поиск калорийности продуктов')
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        title = QLabel('Поиск калорийности продуктов')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.barcode_tab = self.create_barcode_tab()
        self.tabs.addTab(self.barcode_tab, "Поиск по штрихкоду")
        
        self.search_tab = self.create_search_tab()
        self.tabs.addTab(self.search_tab, "Поиск по названию")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Штрихкод", "Название", "Бренд", "Калории/100г", 
            "Белки/100г", "Жиры/100г", "Углеводы/100г"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.doubleClicked.connect(self.on_table_double_click)
        layout.addWidget(self.results_table)
        
    def create_barcode_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        barcode_group = QGroupBox("Поиск по штрихкоду")
        barcode_layout = QHBoxLayout(barcode_group)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Введите штрихкод продукта...")
        self.barcode_input.returnPressed.connect(self.search_by_barcode)
        barcode_layout.addWidget(self.barcode_input)
        
        self.barcode_button = QPushButton("Найти")
        self.barcode_button.clicked.connect(self.search_by_barcode)
        barcode_layout.addWidget(self.barcode_button)
        
        layout.addWidget(barcode_group)
        
        examples_group = QGroupBox("Примеры штрихкодов для тестирования")
        examples_layout = QVBoxLayout(examples_group)
        
        examples_text = QLabel(
            "5449000000996 - Coca-Cola\n"
            "3017620422003 - Nutella\n"
            "7613034626844 - Lindt Chocolate\n"
            "5000159459228 - Pepsi Cola"
        )
        examples_text.setWordWrap(True)
        examples_layout.addWidget(examples_text)
        
        layout.addWidget(examples_group)
        layout.addStretch()
        
        return widget
    
    def create_search_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        search_group = QGroupBox("Поиск по названию")
        search_layout = QHBoxLayout(search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название продукта...")
        self.search_input.returnPressed.connect(self.search_by_name)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.search_by_name)
        search_layout.addWidget(self.search_button)
        
        layout.addWidget(search_group)
        
        examples_group = QGroupBox("Примеры запросов для тестирования")
        examples_layout = QVBoxLayout(examples_group)
        
        examples_text = QLabel(
            "творог 5%\n"
            "шоколад молочный\n"
            "хлеб белый\n"
            "йогурт натуральный"
        )
        examples_text.setWordWrap(True)
        examples_layout.addWidget(examples_text)
        
        layout.addWidget(examples_group)
        layout.addStretch()
        
        return widget
    
    def search_by_barcode(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            QMessageBox.warning(self, "Ошибка", "Введите штрихкод")
            return
        
        self.start_search("barcode", barcode)
    
    def search_by_name(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите название продукта")
            return
        
        self.start_search("name", query)
    
    def start_search(self, search_type, query):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.barcode_button.setEnabled(False)
        self.search_button.setEnabled(False)
        
        self.search_worker = SearchWorker(search_type, query)
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.start()
    
    def on_search_finished(self, result):
        self.progress_bar.setVisible(False)
        self.barcode_button.setEnabled(True)
        self.search_button.setEnabled(True)
        
        products = result.get("products", [])
        
        if not products:
            self.results_text.setText("Продукты не найдены")
            self.results_table.setRowCount(0)
            return
        
        self.update_results_table(products)
        
        if products:
            self.show_product_details(products[0])
    
    def on_search_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.barcode_button.setEnabled(True)
        self.search_button.setEnabled(True)
        
        QMessageBox.critical(self, "Ошибка", error_message)
        self.results_text.setText(f"Ошибка: {error_message}")
    
    def update_results_table(self, products):
        self.results_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            code_item = QTableWidgetItem(product.get("code", "N/A"))
            name_item = QTableWidgetItem(product.get("product_name", "Неизвестно"))
            brand_item = QTableWidgetItem(product.get("brands", "Неизвестно"))
            
            nutriments = extract_kcal(product.get("nutriments", {}))
            
            kcal_item = QTableWidgetItem(str(nutriments.get("kcal_100g", "N/A")))
            protein_item = QTableWidgetItem(str(nutriments.get("protein_100g", "N/A")))
            fat_item = QTableWidgetItem(str(nutriments.get("fat_100g", "N/A")))
            carbs_item = QTableWidgetItem(str(nutriments.get("carbs_100g", "N/A")))
            
            self.results_table.setItem(row, 0, code_item)
            self.results_table.setItem(row, 1, name_item)
            self.results_table.setItem(row, 2, brand_item)
            self.results_table.setItem(row, 3, kcal_item)
            self.results_table.setItem(row, 4, protein_item)
            self.results_table.setItem(row, 5, fat_item)
            self.results_table.setItem(row, 6, carbs_item)
    
    def on_table_double_click(self, index):
        row = index.row()
        product_code = self.results_table.item(row, 0).text()
        if product_code != "N/A":
            self.barcode_input.setText(product_code)
            self.tabs.setCurrentIndex(0)
            self.search_by_barcode()
    
    def show_product_details(self, product):
        details = f"""=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПРОДУКТЕ ===

Название: {product.get('product_name', 'Неизвестно')}
Бренд: {product.get('brands', 'Неизвестно')}
Штрихкод: {product.get('code', 'N/A')}
Упаковка: {product.get('quantity', 'N/A')}
Размер порции: {product.get('serving_size', 'N/A')}

ПИТАТЕЛЬНАЯ ЦЕННОСТЬ (на 100г):
"""
        
        nutriments = extract_kcal(product.get("nutriments", {}))
        
        if nutriments:
            details += f"Калории: {nutriments.get('kcal_100g', 'N/A')} ккал\n"
            details += f"Белки: {nutriments.get('protein_100g', 'N/A')} г\n"
            details += f"Жиры: {nutriments.get('fat_100g', 'N/A')} г\n"
            details += f"Углеводы: {nutriments.get('carbs_100g', 'N/A')} г\n"
            
            if any(k.endswith('_serving') for k in nutriments.keys()):
                details += "\nПИТАТЕЛЬНАЯ ЦЕННОСТЬ (на порцию):\n"
                details += f"Калории: {nutriments.get('kcal_serving', 'N/A')} ккал\n"
                details += f"Белки: {nutriments.get('protein_serving', 'N/A')} г\n"
                details += f"Жиры: {nutriments.get('fat_serving', 'N/A')} г\n"
                details += f"Углеводы: {nutriments.get('carbs_serving', 'N/A')} г\n"
        else:
            details += "Информация о питательной ценности отсутствует\n"
        
        self.results_text.setText(details)

def main():
    app = QApplication(sys.argv)
    window = CalorieFinderApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()