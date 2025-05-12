import sys, json
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton,
    QFormLayout, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QSpinBox,
    QMessageBox, QFileDialog, QSplitter
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MainWindow(QMainWindow):
    """Spectrometer wavelength‑calibration utility (ver 1.4)
    * Adds Matplotlib navigation toolbar
    * Displays live cursor (x, y) in the status bar
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chromex Calibration – multi‑point v1.4")
        self.setFixedSize(480, 840)
        self.setStyleSheet("font-size: 12pt; font-family: 'Arial';")
        self.setWindowIconText("Chromex Calibration")

        self.a = self.b = None      # calibration coefficients
        self.dark = None            # dark spectrum

        self._make_widgets()
        self._make_layout()

        # ── cursor tracker ──
        self.statusBar().showMessage("x: –, y: –")
        self.canvas.mpl_connect("motion_notify_event", self._on_move)

    # ─────────────────────── UI widgets ────────────────────────
    def _make_widgets(self):
        # calibration table
        self.calib_layout = QFormLayout()
        self.calib_rows = []
        for _ in range(2):
            self._add_calib_row()
        self.btn_add_row = QPushButton("＋行追加")
        self.btn_add_row.clicked.connect(self._add_calib_row)

        # peak‑detection parameters
        self.spin_prom = QDoubleSpinBox(); self.spin_prom.setRange(0, 1e6)
        self.spin_prom.setValue(50); self.spin_prom.setSuffix("  prominence")
        self.spin_dist = QSpinBox(); self.spin_dist.setRange(1, 2000)
        self.spin_dist.setValue(100); self.spin_dist.setSuffix("  distance(ch)")

        # action buttons
        self.btn_calib = QPushButton("校正");      self.btn_calib.clicked.connect(self.calibrate)
        self.btn_peak  = QPushButton("ピーク検出"); self.btn_peak.clicked.connect(self.detect_peaks)
        self.btn_savecal = QPushButton("保存");    self.btn_savecal.clicked.connect(self.save_calib)
        self.btn_dark  = QPushButton("ダーク測定"); self.btn_dark.clicked.connect(self.set_dark)
        self.btn_open  = QPushButton("ファイルを開く"); self.btn_open.clicked.connect(self.open_file)
        self.btn_plot  = QPushButton("スペクトル描画"); self.btn_plot.clicked.connect(self.plot_spectrum)

        # labels
        self.lbl_eqn   = QLabel("λ = a·ch + b  (未校正)"); self.lbl_eqn.setStyleSheet("font-weight:bold;")
        self.lbl_range = QLabel("観測可能波長範囲: N/A"); self.lbl_range.setStyleSheet("font-weight:bold;")
        self.lbl_dark  = QLabel("ダーク測定: 未実施");      self.lbl_dark.setStyleSheet("font-weight:bold;")

        # plot canvas & toolbar
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        self.ax  = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # data input
        self.txt = QTextEdit()
        self.txt.setPlaceholderText(
            "『チャネル<TAB>強度』形式または『強度のみ』1行1値を貼り付け、\nまたは［ファイルを開く］で読み込み")

    def _add_calib_row(self):
        le_lam = QLineEdit(); le_lam.setPlaceholderText("λ [nm] 例: 519.2")
        le_ch  = QLineEdit(); le_ch.setPlaceholderText("ch  (自動/手入力)")
        self.calib_layout.addRow(le_lam, le_ch)
        self.calib_rows.append((le_lam, le_ch))

    # ─────────────────────── layout ───────────────────────────
    def _make_layout(self):
        box_form = QWidget(); v = QVBoxLayout(box_form)
        v.addLayout(self.calib_layout)
        v.addWidget(self.btn_add_row)
        v.addWidget(self.btn_calib)
        v.addWidget(self.btn_savecal)

        peak_box = QWidget(); h = QHBoxLayout(peak_box)
        h.addWidget(self.spin_prom); h.addWidget(self.spin_dist)
        h.addStretch(); h.addWidget(self.btn_peak)

        top = QWidget(); vtop = QVBoxLayout(top)
        vtop.addWidget(box_form)
        vtop.addWidget(peak_box)
        vtop.addWidget(self.lbl_eqn)
        vtop.addWidget(self.lbl_range)
        vtop.addWidget(self.lbl_dark)

        bottom = QWidget(); vbot = QVBoxLayout(bottom)
        btn_row = QHBoxLayout()
        for w in (self.btn_open, self.btn_dark, self.btn_plot):
            btn_row.addWidget(w)
        btn_row.addStretch()
        vbot.addLayout(btn_row)
        vbot.addWidget(self.txt)

        # canvas + toolbar block
        canvas_block = QWidget(); vcb = QVBoxLayout(canvas_block)
        vcb.setContentsMargins(0, 0, 0, 0)
        vcb.addWidget(self.canvas)
        vcb.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(canvas_block); splitter.addWidget(bottom)
        splitter.setSizes([360, 260])

        central = QWidget(); layout = QVBoxLayout(central)
        layout.addWidget(top); layout.addWidget(splitter)
        self.setCentralWidget(central)

    # ────────────────── calibration & plotting ─────────────────
    def calibrate(self):
        lam, ch = [], []
        for le_lam, le_ch in self.calib_rows:
            t_lam, t_ch = le_lam.text().strip(), le_ch.text().strip()
            if not t_lam and not t_ch:
                continue
            try:
                lam.append(float(t_lam)); ch.append(float(t_ch))
            except ValueError:
                QMessageBox.warning(self, "入力エラー", "λ と ch は数値で入力してください")
                return
        if len(lam) < 2:
            QMessageBox.warning(self, "入力エラー", "少なくとも 2 点の (λ, ch) を入力してください")
            return
        lam, ch = np.array(lam), np.array(ch)
        self.a, self.b = np.polyfit(ch, lam, 1)
        self.lbl_eqn.setText(f"λ = {self.a:.6f}·ch + {self.b:.6f}")
        ch_max = 1343
        self.lbl_range.setText(
            f"観測可能波長範囲: {self.b:.2f} – {self.a * ch_max + self.b:.2f} nm")

        self.ax.cla(); ch_axis = np.arange(1344)
        self.ax.plot(ch_axis, self.a * ch_axis + self.b, lw=1.2, label="Calibration line")
        self.ax.scatter(ch, lam, c='red', zorder=5, label='Input points')
        self.ax.set_xlabel("Channel"); self.ax.set_ylabel("Wavelength [nm]"); self.ax.legend()
        self.canvas.draw()

    def save_calib(self):
        if self.a is None:
            QMessageBox.warning(self, "未校正", "［校正］を実行してから保存してください")
            return
        fname, _ = QFileDialog.getSaveFileName(
            self, "校正データを保存", "", "Calibration (*.json);;All (*)")
        if fname:
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump({'a': self.a, 'b': self.b}, f, indent=2)
            QMessageBox.information(self, "保存完了", f"校正係数を保存しました:\n{fname}")

    def detect_peaks(self):
        data = self._get_text_array()
        if data is None:
            return
        prom, dist = self.spin_prom.value(), self.spin_dist.value()
        peaks, _ = find_peaks(data, prominence=prom, distance=dist)
        if len(peaks) == 0:
            QMessageBox.warning(self, "ピークなし",
                                 f"prom={prom}, dist={dist} ではピークが見つかりません")
            return
        top = peaks[np.argsort(data[peaks])][::-1][:5]

        # clear & ensure rows
        for _, le_ch in self.calib_rows:
            le_ch.clear()
        while len(self.calib_rows) < len(top):
            self._add_calib_row()
        for i, ch_val in enumerate(top):
            _, le_ch = self.calib_rows[i]
            le_ch.setText(str(int(ch_val)))

        self.ax.cla()
        self.ax.plot(np.arange(len(data)), data, lw=0.8, label='Raw')
        self.ax.scatter(top, data[top], c='red', zorder=5, label='Peaks')
        self.ax.set_xlabel('Channel'); self.ax.set_ylabel('Intensity'); self.ax.legend()
        self.ax.set_title(f"find_peaks (prom={prom}, dist={dist})")
        self.canvas.draw()

        QMessageBox.information(self, "ピーク検出",
            "検出 ch を自動入力しました。対応 λ を入力後［校正］してください")

    def set_dark(self):
        data = self._get_text_array()
        if data is None:
            return
        self.dark = data
        self.lbl_dark.setText("ダーク測定: 完了")

        self.ax.cla(); x = np.arange(len(data))
        if self.a is not None:
            x = self.a * x + self.b; self.ax.set_xlabel("Wavelength [nm]")
        else:
            self.ax.set_xlabel("Channel")
        self.ax.plot(x, data, lw=1, label='Dark')
        self.ax.set_ylabel('Intensity'); self.ax.legend(); self.ax.set_title('Dark Spectrum')
        self.canvas.draw()

    def plot_spectrum(self):
        data = self._get_text_array()
        if data is None:
            return
        if self.dark is not None:
            if len(data) != len(self.dark):
                QMessageBox.warning(self, "長さ不一致", "ダークと長さが違います")
                return
            data = data - self.dark
        x = np.arange(len(data)); xlabel = "Channel"
        if self.a is not None:
            x = self.a * x + self.b; xlabel = "Wavelength [nm]"
        self.ax.cla()
        self.ax.plot(x, data, lw=1, label='Corrected' if self.dark is not None else 'Spectrum')
        self.ax.set_xlabel(xlabel); self.ax.set_ylabel('Intensity'); self.ax.legend()
        self.ax.set_title('Spectrum'); self.canvas.draw()

    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "強度データ", "", "Text (*.txt *.csv);;All (*)")
        if fname:
            with open(fname, encoding='utf-8') as f:
                self.txt.setPlainText(f.read())

    def _get_text_array(self):
        txt = self.txt.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "データなし", "データを貼り付けてください")
            return None
        vals = []
        for line in txt.splitlines():
            parts = line.split()
            try:
                vals.append(float(parts[-1]))
            except ValueError:
                QMessageBox.warning(self, "形式エラー", "数値以外を検出しました")
                return None
        return np.array(vals)

    # ────────────────── cursor tracker ─────────────────
    def _on_move(self, event):
        if event.inaxes == self.ax and event.xdata is not None and event.ydata is not None:
            self.statusBar().showMessage(f"x: {event.xdata:.2f}, y: {event.ydata:.2f}")
        else:
            self.statusBar().showMessage("x: –, y: –")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec_())