import sys
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
from matplotlib.figure import Figure


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chromex Calibration")
        # サイズを固定
        self.setFixedSize(400, 780)    # 高さを若干拡張
        self.setStyleSheet("font-size: 12pt; font-family: 'Arial';")
        self.setWindowIconText("Chromex Calibration")

        self.a = self.b = None        # 校正係数
        self.dark = None              # ダーク強度
        self._make_widgets()
        self._make_layout()

    def _make_widgets(self):
        # 校正入力欄
        self.lam1 = QLineEdit(); self.lam1.setPlaceholderText("λ₁ 例: 519.2")
        self.ch1  = QLineEdit(); self.ch1 .setPlaceholderText("ch₁ 自動/手入力")
        self.lam2 = QLineEdit(); self.lam2.setPlaceholderText("λ₂ 例: 653.8")
        self.ch2  = QLineEdit(); self.ch2 .setPlaceholderText("ch₂ 自動/手入力")

        # SciPy-find_peaks パラメータ
        self.spin_prom = QDoubleSpinBox(); self.spin_prom.setRange(0, 1e6)
        self.spin_prom.setValue(50); self.spin_prom.setSuffix("  prominence")
        self.spin_dist = QSpinBox(); self.spin_dist.setRange(1, 2000)
        self.spin_dist.setValue(100); self.spin_dist.setSuffix("  distance(ch)")

        # ボタン
        self.btn_calib  = QPushButton("校正");      self.btn_calib.clicked.connect(self.calibrate)
        self.btn_peak   = QPushButton("ピーク検出"); self.btn_peak.clicked.connect(self.detect_peaks)
        self.btn_dark   = QPushButton("ダーク測定"); self.btn_dark.clicked.connect(self.set_dark)
        self.btn_open   = QPushButton("ファイルを開く"); self.btn_open.clicked.connect(self.open_file)
        self.btn_plot   = QPushButton("スペクトル描画"); self.btn_plot.clicked.connect(self.plot_spectrum)

        # ラベル
        self.lbl_eqn   = QLabel("λ = a·ch + b  (未校正)"); self.lbl_eqn.setStyleSheet("font-weight:bold;")
        self.lbl_range = QLabel("観測可能波長範囲: N/A"); self.lbl_range.setStyleSheet("font-weight:bold;")
        self.lbl_dark  = QLabel("ダーク測定: 未実施");  self.lbl_dark.setStyleSheet("font-weight:bold;")

        # グラフ
        self.fig = Figure(figsize=(6,4), tight_layout=True)
        self.ax  = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # データ入力欄
        self.txt = QTextEdit()
        self.txt.setPlaceholderText(
            "「チャネル TAB 強度」形式または「強度のみ」1行1値で貼り付け\nまたは［ファイルを開く］"
        )

    def _make_layout(self):
        # 校正フォーム
        form = QFormLayout()
        form.addRow("λ₁ [nm]", self.lam1); self.lam1.setText("519.2")
        form.addRow("ch₁",      self.ch1)
        form.addRow("λ₂ [nm]", self.lam2); self.lam2.setText("653.8")
        form.addRow("ch₂",      self.ch2)
        form.addRow(self.btn_calib)

        box_form = QWidget(); box_form.setLayout(form)

        # ピーク検出設定
        peak_box = QWidget(); peak_layout = QHBoxLayout(peak_box)
        peak_layout.addWidget(self.spin_prom); peak_layout.addWidget(self.spin_dist)
        peak_layout.addStretch(); peak_layout.addWidget(self.btn_peak)

        # 上部
        top = QWidget(); vtop = QVBoxLayout(top)
        vtop.addWidget(box_form)
        vtop.addWidget(peak_box)
        vtop.addWidget(self.lbl_eqn)
        vtop.addWidget(self.lbl_range)
        vtop.addWidget(self.lbl_dark)

        # 下部
        bottom = QWidget(); vbot = QVBoxLayout(bottom)
        row = QHBoxLayout()
        for w in (self.btn_open, self.btn_dark, self.btn_plot):
            row.addWidget(w)
        row.addStretch()
        vbot.addLayout(row); vbot.addWidget(self.txt)

        # 分割
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.canvas); splitter.addWidget(bottom); splitter.setSizes([320,260])

        # 中央
        central = QWidget(); v = QVBoxLayout(central)
        v.addWidget(top); v.addWidget(splitter)
        self.setCentralWidget(central)

    def calibrate(self):
        try:
            lam1, lam2 = float(self.lam1.text()), float(self.lam2.text())
            ch1,  ch2  = float(self.ch1.text()),  float(self.ch2.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "λ と ch を数値で入力してください"); return
        if ch1 == ch2:
            QMessageBox.warning(self, "入力エラー", "ch₁ ≠ ch₂ にしてください"); return

        # 校正係数計算
        self.a = (lam2 - lam1) / (ch2 - ch1)
        self.b = lam1 - self.a * ch1
        self.lbl_eqn.setText(f"λ = {self.a:.6f}·ch + {self.b:.6f}")

        # 観測可能波長範囲の更新
        ch_max = 1344 - 1
        lam_min = self.a * 0 + self.b
        lam_max = self.a * ch_max + self.b
        self.lbl_range.setText(f"観測可能波長範囲: {lam_min:.2f} - {lam_max:.2f} nm")

        # キャリブレーション線描画
        self.ax.cla()
        ch = np.arange(1344)
        self.ax.plot(ch, self.a * ch + self.b, lw=1.2, label="Calibration line")
        self.ax.scatter([ch1, ch2], [lam1, lam2], c="red", zorder=5, label="Input pts")
        self.ax.set_xlabel("Channel"); self.ax.set_ylabel("Wavelength [nm]"); self.ax.legend()
        self.canvas.draw()

    # 以下のメソッドは変更なし
    def detect_peaks(self):
        data = self._get_text_array(); 
        if data is None: return

        prom = self.spin_prom.value()
        dist = self.spin_dist.value()
        peaks, _ = find_peaks(data, prominence=prom, distance=dist)
        if len(peaks) == 0:
            QMessageBox.warning(self, "ピークなし", f"prom={prom}, dist={dist} ではピークが見つかりません"); return

        top = peaks[np.argsort(data[peaks])[-2:]][::-1]
        self.ch1.setText(str(int(top[0]))); 
        if len(top) > 1: self.ch2.setText(str(int(top[1])))

        self.ax.cla()
        self.ax.plot(np.arange(len(data)), data, lw=0.8, label="Raw")
        self.ax.scatter(top, data[top], c="red", zorder=5, label="Peaks")
        self.ax.set_xlabel("Channel"); self.ax.set_ylabel("Intensity"); self.ax.legend()
        self.ax.set_title(f"find_peaks (prom={prom}, dist={dist})"); self.canvas.draw()

        QMessageBox.information(self, "ピーク検出",
            f"検出 ch: {', '.join(map(str, top))}\nλ を入力して［校正］してください")

    def set_dark(self):
        data = self._get_text_array(); 
        if data is None: return
        self.dark = data; self.lbl_dark.setText("ダーク測定: 完了")

        self.ax.cla()
        x = np.arange(len(data))
        if self.a is not None:
            x = self.a * x + self.b; self.ax.set_xlabel("Wavelength [nm]")
        else:
            self.ax.set_xlabel("Channel")
        self.ax.plot(x, data, lw=1, label="Dark"); self.ax.set_ylabel("Intensity"); self.ax.legend()
        self.ax.set_title("Dark Spectrum"); self.canvas.draw()

    def plot_spectrum(self):
        data = self._get_text_array(); 
        if data is None: return
        if self.dark is not None:
            if len(data) != len(self.dark):
                QMessageBox.warning(self, "長さ不一致", "ダークと長さが違います"); return
            data = data - self.dark
        x = np.arange(len(data)); xlabel = "Channel"
        if self.a is not None:
            x = self.a * x + self.b; xlabel = "Wavelength [nm]"
        self.ax.cla()
        self.ax.plot(x, data, lw        =1, label="Corrected" if self.dark is not None else "Spectrum")
        self.ax.set_xlabel(xlabel); self.ax.set_ylabel("Intensity"); self.ax.legend()
        self.ax.set_title("Spectrum"); self.canvas.draw()

    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "強度データ", "", "Text (*.txt *.csv);;All (*)")
        if fname:
            with open(fname, encoding="utf-8") as f:
                self.txt.setPlainText(f.read())

    def _get_text_array(self):
        txt = self.txt.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "データなし", "データを貼り付けてください")
            return None

        lines = txt.splitlines()
        vals = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 1:
                try:
                    vals.append(float(parts[0]))
                except ValueError:
                    QMessageBox.warning(self, "形式エラー", "数値以外を検出しました"); return None
            elif len(parts) >= 2:
                try:
                    vals.append(float(parts[-1]))
                except ValueError:
                    QMessageBox.warning(self, "形式エラー", "2 列目以降に数値がありません"); return None
            else:
                QMessageBox.warning(self, "形式エラー", "行の解析に失敗しました"); return None

        return np.array(vals)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec_())