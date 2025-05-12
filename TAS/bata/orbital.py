#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrogen Orbitals Viewer (1s, 2p, 3d) – exact, normalized
SciPy ≥1.11 / PyQt5 ≥5.15 / Matplotlib ≥3.8
"""
import sys
import numpy as np
from scipy.special import sph_harm, genlaguerre, factorial
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- constants (atomic units) -------------------------------------------------
a0 = 1.0  # Bohr radius

# --- hydrogenic radial function R_{n,l}(r) -----------------------------------
def R_nl(n: int, l: int, r: np.ndarray) -> np.ndarray:
    """Normalized radial part of hydrogenic wavefunction (atomic units)."""
    rho = 2.0 * r / (n * a0)
    norm = np.sqrt((2.0 / (n * a0))**3 * factorial(n - l - 1) /
                   (2 * n * factorial(n + l)))
    L = genlaguerre(n - l - 1, 2 * l + 1)(rho)
    return norm * np.exp(-rho / 2) * rho**l * L

# --- full wavefunction ψ_{n,l,m}(r,θ,φ) --------------------------------------
def psi_nlm(n, l, m, r, theta, phi, part="abs"):
    """Return requested part of ψ_{n,l,m}."""
    R = R_nl(n, l, r)
    Y = sph_harm(m, l, phi, theta)
    psi = R * Y
    if part == "real":
        return np.real(psi)
    if part == "imag":
        return np.imag(psi)
    return np.abs(psi)

# --- PyQt5 GUI ----------------------------------------------------------------
class OrbitalViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hydrogen Orbital 3D Viewer (exact, normalized)")

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout  = QtWidgets.QHBoxLayout(central)

        # ---------- control panel --------------------------------------------
        ctrl = QtWidgets.QVBoxLayout(); layout.addLayout(ctrl, 1)
        ctrl.addWidget(QtWidgets.QLabel("Orbital:"))
        self.cmb = QtWidgets.QComboBox()
        self.cmb.addItems([
            "1s",
            "2p_z", "2p_x", "2p_y",
            "3d_z2", "3d_xz", "3d_yz", "3d_xy", "3d_x2-y2"
        ])
        ctrl.addWidget(self.cmb)

        ctrl.addWidget(QtWidgets.QLabel("Scale (×0.1):"))
        self.sld = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld.setRange(1, 50); self.sld.setValue(10)
        ctrl.addWidget(self.sld)

        self.btn = QtWidgets.QPushButton("Plot"); ctrl.addWidget(self.btn)
        ctrl.addStretch()

        # ---------- canvas ---------------------------------------------------
        self.fig = Figure(figsize=(5, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, projection="3d")
        layout.addWidget(self.canvas, 4)

        # ---------- signals --------------------------------------------------
        for w in (self.cmb, self.sld, self.btn):
            w.clicked.connect(self.draw) if isinstance(w, QtWidgets.QPushButton) else \
            w.valueChanged.connect(self.draw) if isinstance(w, QtWidgets.QSlider) else \
            w.currentIndexChanged.connect(self.draw)

        self.draw()

    # ------------------------------------------------------------------------
    def draw(self):
        orb   = self.cmb.currentText()
        scale = self.sld.value() / 10.0

        # θ,φ grid
        theta = np.linspace(0, np.pi,   120)
        phi   = np.linspace(0, 2*np.pi, 120)
        th, ph = np.meshgrid(theta, phi)

        # quantum numbers map
        qmap = {
            "1s":       (1, 0,  0, "real"),
            "2p_z":     (2, 1,  0, "real"),
            "2p_x":     (2, 1,  1, "real"),
            "2p_y":     (2, 1,  1, "imag"),
            "3d_z2":    (3, 2,  0, "real"),
            "3d_xz":    (3, 2,  1, "real"),
            "3d_yz":    (3, 2,  1, "imag"),
            "3d_xy":    (3, 2,  2, "imag"),
            "3d_x2-y2": (3, 2,  2, "real"),
        }
        n, l, m, part = qmap[orb]

        # choose r at expected radius n^2 a0 (captures main lobe)
        r0 = n**2 * a0
        psi_ang = psi_nlm(n, l, m, r0, th, ph, part="abs")
        r_plot  = scale * psi_ang / psi_ang.max()

        # spherical -> cartesian
        x = r_plot * np.sin(th) * np.cos(ph)
        y = r_plot * np.sin(th) * np.sin(ph)
        z = r_plot * np.cos(th)

        # ---------- plot -----------------------------------------------------
        self.ax.clear(); self.ax.set_axis_off()
        self.ax.plot_surface(x, y, z, rstride=1, cstride=1,
                             linewidth=0, antialiased=True,
                             alpha=0.65, edgecolor="none")
        lim = r_plot.max()

        # axis arrows
        for dx, dy, dz, label in [
            ( lim,0,0,"X"),(-lim,0,0,""),
            (0, lim,0,"Y"),(0,-lim,0,""),
            (0,0, lim,"Z"),(0,0,-lim,""),
        ]:
            self.ax.quiver(0,0,0, dx,dy,dz, arrow_length_ratio=0.05)
            if label:
                self.ax.text(dx*1.1, dy*1.1, dz*1.1, label, fontsize=11)

        try:  # Matplotlib ≥3.3
            self.ax.set_box_aspect([1,1,1])
        except AttributeError:
            pass
        self.ax.set(xlim=(-lim, lim), ylim=(-lim, lim), zlim=(-lim, lim))
        self.fig.tight_layout(); self.canvas.draw()

# -----------------------------------------------------------------------------        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = OrbitalViewer(); w.resize(900,650); w.show()
    sys.exit(app.exec_())
