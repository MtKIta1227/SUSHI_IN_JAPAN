import os
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QVBoxLayout, QWidget
import matplotlib.pyplot as plt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Selector")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.button = QPushButton("Select Files")
        self.button.clicked.connect(self.select_files)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Text Files (*.txt)", options=options)

        if files:
            for file_path in files:
                with open(file_path, 'r', encoding='latin-1') as file:
                    lines = file.readlines()

                data_lines = []
                for line in lines[19:]:
                    if line.strip() == '':
                        break
                    data_lines.append(line)

                x_data = []
                y_data = []
                for line in data_lines:
                    values = line.split()
                    if len(values) >= 2:
                        x_data.append(float(values[0]))
                        y_data.append(float(values[1]))

                file_name = os.path.splitext(os.path.basename(file_path))[0]

                plt.plot(x_data, y_data, label=file_name)
                plt.xlabel('Wavelength/nm')
                plt.ylabel('Absorbance')

            plt.title('')
            plt.legend()
            plt.show()

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
