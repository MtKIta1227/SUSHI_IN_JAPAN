import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QTextEdit

def load_data_preprocess(filename):
    # 最初の12行をスキップしてファイルをPandasで読み込む
    df = pd.read_csv(filename, sep='\s+', skiprows=12)
    
    # 一行目に200から700まで1刻みで数値を代入
    new_header = np.arange(200, 701, 1)
    df.columns = new_header
    
    # 一列目に0から0.003333333刻みで数値を追加
    num_rows = len(df)
    time_values = np.arange(0, 0.003333333 * num_rows, 0.003333333)[:num_rows]
    df.insert(0, '', time_values)  # 列名を空白にする
    
    return df

def load_data(filename):
    df = load_data_preprocess(filename)
    lines = df.to_string(index=False).split('\n')

    # 波長軸を抽出
    wavelengths = list(map(float, lines[0].strip().split()[1:]))

    # 強度のデータを抽出
    intensity_data = []
    times = []
    for line in lines[1:]:
        values = line.strip().split()
        time = float(values[0])  # 秒から分への変換
        times.append(time)
        intensities = list(map(float, values[1:]))
        intensity_data.append(intensities)

    return wavelengths, times, np.array(intensity_data)

def save_data_to_file(df, filename):
    # データフレームをテキストファイルに保存
    df.to_csv(filename, sep='\t', index=False)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 - File Dialog'
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 600
        self.initUI()
        self.df = None  # データフレームを初期化

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QVBoxLayout()

        self.openButton = QPushButton('Open file', self)
        self.openButton.clicked.connect(self.show_file_dialog)
        layout.addWidget(self.openButton)

        self.saveButton = QPushButton('Save processed data', self)
        self.saveButton.clicked.connect(self.save_file_dialog)
        self.saveButton.setEnabled(False)  # 初期状態では無効
        layout.addWidget(self.saveButton)

        self.textEdit = QTextEdit(self)
        layout.addWidget(self.textEdit)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def show_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filename, _ = QFileDialog.getOpenFileName(self, "Select a text file", "", "Text Files (*.txt);;All Files (*)", options=options)
        if filename:
            self.df = load_data_preprocess(filename)  # データフレームを保存
            self.plot_data(filename)
            self.saveButton.setEnabled(True)  # ファイルを開いた後、保存ボタンを有効にする

    def save_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        save_filename, _ = QFileDialog.getSaveFileName(self, "Save processed data", "", "Text Files (*.txt);;All Files (*)", options=options)
        if save_filename:
            save_data_to_file(self.df, save_filename)

    def plot_data(self, filename):
        #ウィンドウサイズを変更
        plt.figure(figsize=(10, 4))
        wavelengths, times, intensity_data = load_data(filename)
        intensity_data = np.transpose(intensity_data)
        #Intensityの数値表示を指数表記にする
        plt.imshow(intensity_data, aspect='auto', cmap='nipy_spectral', origin='lower', extent=[times[0], times[-1], wavelengths[0], wavelengths[-1]])
        plt.xlabel('Rt/ min')  # x軸のラベルを変更
        plt.ylabel('Wavelength / nm')
        plt.ylim(250, 600)
        cbar = plt.colorbar()
        cbar.set_label('Intensity')
        # スケールバーの数値を指数表記に設定
        formatter = ticker.ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-2, 2))
        cbar.ax.yaxis.set_major_formatter(formatter)

        plt.show()

def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
