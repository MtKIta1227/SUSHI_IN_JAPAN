import sys
import numpy as np
import pandas as pd
import matplotlib
# Use Qt5Agg backend explicitly
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QMessageBox,
    QDialog, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout
)

# ---------------------- Data Loading ---------------------- #

def load_data(filename):
    """Load SEC data (same style as SEC_auto.py).

    * Skip the first 12 header lines.
    * Whitespace‑delimited values after that.
    * Build a time axis (0, 0.003333…, …) and an implicit wavelength axis
      starting at 200 nm, 1 nm step.
    """
    df = pd.read_csv(filename, sep="\s+", skiprows=12, header=None)

    raw = df.values
    rows, cols = raw.shape

    # Time axis (s)
    dt = 0.003333333
    time = np.arange(0, dt * rows, dt)[:rows]

    # Wavelength axis (nm) – assumes 200 nm start, 1 nm step
    wavelengths = np.arange(200, 200 + cols, 1)

    # Merge into one array: [time | intensities]
    df.insert(0, "Time", time)
    data = df.values
    return wavelengths, data

# ---------------------- Plot Dialog ----------------------- #

class SpectraDialog(QDialog):
    """Dialog showing spectra plot with toolbar and interactive canvas."""
    def __init__(self, wavelengths, data, selected_times, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spectra at Selected Times")

        # --- Create FigureCanvas --- #
        fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(fig)
        self.ax = fig.add_subplot(111)

        # Plot spectra
        for st in selected_times:
            idx = (np.abs(data[:, 0] - st)).argmin()
            spectrum = data[idx, 1:]
            self.ax.plot(wavelengths, spectrum, label=f"{st:.6f} s")
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.legend()
        fig.tight_layout()

        # Toolbar
        toolbar = NavigationToolbar(self.canvas, self)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # Show immediately (non‑modal)
        self.show()

# ---------------------- UI Dialog ------------------------- #

class TimeSelectionDialog(QDialog):
    """List‑based multi‑selection of times, then open SpectraDialog."""
    def __init__(self, wavelengths, data):
        super().__init__()
        self.wavelengths = wavelengths
        self.data = data
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Select Time Points")
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for t in self.data[:, 0]:
            self.list_widget.addItem(f"{t:.6f}")
        layout.addWidget(self.list_widget)

        btn_plot = QPushButton("Plot Spectra")
        btn_plot.clicked.connect(self._on_plot)
        layout.addWidget(btn_plot)

    def _on_plot(self):
        items = self.list_widget.selectedItems()
        if not items:
            QMessageBox.warning(self, "No Selection", "Please select at least one time point.")
            return
        selected_times = [float(item.text()) for item in items]
        # Open non‑modal SpectraDialog so matplotlib remains interactive
        SpectraDialog(self.wavelengths, self.data, selected_times, parent=self)

# ---------------------- Helpers --------------------------- #

def select_file():
    filename, _ = QFileDialog.getOpenFileName(None, "Select data file", "", "All Files (*)")
    return filename

# ---------------------- Main ------------------------------ #

def main():
    app = QApplication(sys.argv)

    filename = select_file()
    if not filename:
        QMessageBox.information(None, "No File", "No file selected – exiting.")
        sys.exit()

    try:
        wavelengths, data = load_data(filename)
    except Exception as e:
        QMessageBox.critical(None, "Load Error", f"Failed to load data:\n{e}")
        sys.exit(1)

    dialog = TimeSelectionDialog(wavelengths, data)
    dialog.exec_()

if __name__ == "__main__":
    main()
