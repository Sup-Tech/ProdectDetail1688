from PyQt5.QtWidgets import QApplication
from gui import *
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)
    print(sys.platform)

    main_window = MainWindow()
    main_window.show()
    app.aboutToQuit.connect(main_window.quit)

    sys.exit(app.exec_())
