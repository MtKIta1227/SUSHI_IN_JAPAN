import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog, QListWidget, QVBoxLayout, QPushButton, QMessageBox

def load_data(filename):
    """Function to load data from a file."""
    data = np.loadtxt(filename, delimiter='\t', skiprows=1)
    wavelengths = np.loadtxt(filename, delimiter='\t', max_rows=1, dtype=str)[1:]
    return wavelengths, data

def plot_data_for_wavelength(wavelengths, data, selected_wavelengths):
    """Function to plot data for specified wavelengths."""
    time = data[:, 0]  # Convert time from milliseconds to minutes

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
 
    for wave in selected_wavelengths:
        if wave in wavelengths:
            idx = list(wavelengths).index(wave)
            intensity = data[:, idx+1]
            normalized_intensity = intensity / np.max(intensity)

            ax1.plot(time, intensity, label=f"{wave}nm")
            ax2.plot(time, normalized_intensity, label=f"{wave}nm (Normalized)")

            print(f"Wavelength: {wave}nm")
            for t, i in zip(time, intensity):
                print(f"Time: {t} minutes Intensity: {i}")
            print("------")

        else:
            print(f"{wave}nm does not exist in the data")

    ax1.set_ylabel("Intensity")
    ax1.set_title("Intensity over Time for Selected Wavelengths")
    ax1.legend()

    ax2.set_xlabel("Time / min")
    ax2.set_ylabel("Normalized Intensity")
    ax2.set_title("Normalized Intensity over Time for Selected Wavelengths")
    ax2.legend()
    plt.tight_layout()
    plt.show()

def select_file():
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(None, "Please select a file", "", "Text Files (*.txt);;All Files (*)", options=options)
    if not filename:
        print("No file selected.")
        return None
    return filename

class WavelengthSelectionDialog(QDialog):
    def __init__(self, wavelengths, data):
        super().__init__()
        self.wavelengths = wavelengths
        self.data = data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Select Wavelengths")

        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for wave in self.wavelengths:
            self.list_widget.addItem(wave)
        self.layout.addWidget(self.list_widget)

        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_selected_wavelengths)
        self.layout.addWidget(self.plot_button)

        self.setLayout(self.layout)

    def plot_selected_wavelengths(self):
        selected_items = self.list_widget.selectedItems()
        selected_wavelengths = [item.text() for item in selected_items]
        if not selected_wavelengths:
            QMessageBox.warning(self, "No Selection", "Please select at least one wavelength.")
            return
        plot_data_for_wavelength(self.wavelengths, self.data, selected_wavelengths)

def main():
    app = QApplication(sys.argv)

    filename = select_file()
    if not filename:
        return

    wavelengths, data = load_data(filename)

    dialog = WavelengthSelectionDialog(wavelengths, data)
    dialog.exec_()

if __name__ == "__main__":
    main()
