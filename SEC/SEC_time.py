import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog

def main():
    app = QApplication(sys.argv)

    # ファイル選択
    options = QFileDialog.Options()
    filepath, _ = QFileDialog.getOpenFileName(None, "Please select a text file", "", "Text files (*.txt);;All Files (*)", options=options)
    if not filepath:
        return

    # データの読み込み
    data = np.loadtxt(filepath, delimiter="\t", skiprows=1)
    time_seconds = data[:, 0]
    intensities = data[:, 1:]

    # ヘッダー（波長）の読み込み
    with open(filepath, 'r') as f:
        wavelengths = [float(val) for val in f.readline().split("\t")[1:]]

    # 時間（分）を指定
    times_str, ok = QInputDialog.getText(None, "Input Dialog", "Specify the times in minutes (comma separated):")
    if not ok:
        return
    times_minutes = [float(t.strip()) for t in times_str.split(',')]

    for minute in times_minutes:
        target_time = minute * 60

        # 指定した時間に最も近いデータのインデックスを見つける
        idx = np.abs(time_seconds - target_time).argmin()

        # 指定した時間の強度を取得
        target_intensities = intensities[idx, :]

        # プロット
        plt.plot(wavelengths, target_intensities, label=f'{minute} minutes')

        # コンソールに波長と強度を表示
        print(f"\nData for {minute} minutes:")
        for wave, inten in zip(wavelengths, target_intensities):
            print(f"Wavelength: {wave}, Intensity: {inten}")

    plt.xlabel('Wavelength')
    plt.ylabel('Intensity')
    plt.xlim(200, 600)
    plt.ylim(0, )
    plt.title('Intensity for specified times')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
