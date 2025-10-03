import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class UnitConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("unit conversion tool")
        self.setGeometry(100, 100, 600, 400)

        #conversion data
        self.conversions = {
            "Length": {
                "Meters": 1,
                "Kilometers": 0.001,
                "Centimeters": 100,
                "Millimeters": 1000,
                "Miles": 0.000621371,
                "Yards": 1.09361,
                "Feet": 3.28084,
                "Inches": 39.3701
            },
            "Weight": {
                "Kilograms": 1,
                "Grams": 1000,
                "Milligrams": 1000000,
                "Pounds": 2.20462,
                "Ounces": 35.274,
                "Tons": 0.001
            },
            "Temperature": {
                "Celsius": "base",
                "Fahrenheit": "F",
                "Kelvin": "K"
            },
            "Volume": {
                "Liters": 1,
                "Milliliters": 1000,
                "Gallons": 0.264172,
                "Quarts": 1.05669,
                "Pints": 2.11338,
                "Cups": 4.22675,
                "Fluid Ounces": 33.814
            },
            "Area": {
                "Square Meters": 1,
                "Square Kilometers": 0.000001,
                "Square Centimeters": 10000,
                "Square Miles": 3.861e-7,
                "Square Feet": 10.7639,
                "Acres": 0.000247105,
                "Hectares": 0.0001
            },
            "Speed": {
                "Meters/second": 1,
                "Kilometers/hour": 3.6,
                "Miles/hour": 2.23694,
                "Feet/second": 3.28084,
                "Knots": 1.94384
            },
        }

        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        #title
        title = QLabel("Unit conversion")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        #categories
        category_group = QGroupBox("Category")
        category_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.conversions.keys())
        self.category_combo.currentTextChanged.connect(self.update_units)
        category_layout.addWidget(QLabel("Select category"))
        category_layout.addWidget(self.category_combo)
        category_group.setLayout(category_layout)
        main_layout.addWidget(category_group)

        #input
        input_group = QGroupBox("From")
        input_layout = QVBoxLayout()

        input_unit_layout = QHBoxLayout()
        self.from_unit = QComboBox()
        input_unit_layout.addWidget(QLabel("Unit:"))
        input_unit_layout.addWidget(self.from_unit)
        input_layout.addLayout(input_unit_layout)

        input_value_layout = QHBoxLayout()
        self.input_value = QLineEdit()
        self.input_value.setPlaceholderText("Enter value")
        self.input_value.textChanged.connect(self.convert)
        input_value_layout.addWidget(QLabel("Value:"))
        input_value_layout.addWidget(self.input_value)
        input_layout.addLayout(input_value_layout)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        #output
        output_group = QGroupBox("To")
        output_layout = QVBoxLayout()
        
        output_unit_layout = QHBoxLayout()
        self.to_unit = QComboBox()
        output_unit_layout.addWidget(QLabel("Unit:"))
        output_unit_layout.addWidget(self.to_unit)
        output_layout.addLayout(output_unit_layout)

        output_value_layout = QHBoxLayout()
        self.output_value = QLineEdit()
        self.output_value.setReadOnly(True)
        self.output_value.setPlaceholderText("Result")
        output_value_layout.addWidget(QLabel("Value:"))
        output_value_layout.addWidget(self.output_value)
        output_layout.addLayout(output_value_layout)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        #convert
        convert_btn = QPushButton("Convert")
        convert_btn.clicked.connect(self.convert)
        main_layout.addWidget(convert_btn)

        #clear
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_fields)
        main_layout.addWidget(clear_btn)

        main_layout.addStretch()
        central_widget.setLayout(main_layout)

        #connect
        self.from_unit.currentTextChanged.connect(self.convert)
        self.to_unit.currentTextChanged.connect(self.convert)

        self.update_units()

    def update_units(self):
        category = self.category_combo.currentText()
        units = list(self.conversions[category].keys())

        self.from_unit.clear()
        self.to_unit.clear()
        self.from_unit.addItems(units)
        self.to_unit.addItems(units)

        if len(units) > 1:
            self.to_unit.setCurrentIndex(1)

        self.from_unit.currentTextChanged.connect(self.convert)
        self.to_unit.currentTextChanged.connect(self.convert)

        self.convert()
        
    def convert(self):
        try:
            value = float(self.input_value.text())
            category = self.category_combo.currentText()
            from_unit = self.from_unit.currentText()
            to_unit = self.to_unit.currentText()

            if category == "Temperature":
                result = self.convert_temperature(value, from_unit, to_unit)
            else:
                from_factor = self.conversions[category][from_unit]
                to_factor = self.conversions[category][to_unit]
                base_value = value / from_factor
                result = base_value * to_factor
            
            self.output_value.setText(f"{result:.6f}")
        except ValueError:
            self.output_value.setText("")
    
    def convert_temperature(self, value, from_unit, to_unit):
        if from_unit == "Celsius":
            celsius = value
        elif from_unit == "Fahrenheit":
            celsius = (value - 32) * 5/9
        else:
            celsius = value -273.15
        
        if to_unit == "Celsius":
            return celsius
        elif to_unit == "Fahrenheit":
            return celsius * 9/5 + 32
        else:
            return celsius + 275.15
    
    def clear_fields(self):
        self.input_value.clear()
        self.output_value.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnitConverter()
    window.show()
    sys.exit(app.exec())

