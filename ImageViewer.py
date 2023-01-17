import sys
from PyQt5.QtWidgets import QApplication

from imlibs import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = MainWindow(sys.argv)
    main.show()
    

    sys.exit(app.exec_())
