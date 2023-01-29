from PyQt5.QtCore import QRect, Qt, QEvent, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QGridLayout, QPushButton, QScrollArea, QFileDialog, QInputDialog, QMenu, QMenuBar, QMessageBox, QLineEdit
from PyQt5.QtGui import QResizeEvent, QKeyEvent

from .resource import ImageResourceManagerWrapper
from .widgets import ImageView, ConfigEditDialog

class MainWindow(QWidget):
    reloadImage = pyqtSignal(str)
    def __init__(self, args, parent=None):
        super(QWidget, self).__init__(parent)
        self.resource_manager = None
        self.init = False
        self.reloadImage.connect(self.onReloadImage)
        if len(args) > 1:
            self.resource_manager = ImageResourceManagerWrapper(
                args[1], self.reloadImage)

        self.initUI()

    def initUI(self):
        self.menu_bar = QMenuBar(self)
        self.open_menu = QMenu("打开")
        open_file = self.open_menu.addAction("打开文件")
        open_dir = self.open_menu.addAction("打开文件...")
        open_webpage = self.open_menu.addAction("打开网页")
        self.menu_bar.addMenu(self.open_menu)
        
        self.config_menu = QMenu("设置")
        edit_config = self.config_menu.addAction("编辑配置")
        self.menu_bar.addMenu(self.config_menu)

        open_file.triggered.connect(self.onOpenFile)
        open_dir.triggered.connect(self.onOpenDir)
        open_webpage.triggered.connect(self.onOpenWebpage)
        edit_config.triggered.connect(self.onEditConfig)
        
        desktop = QApplication.desktop()
        srceen = desktop.screenGeometry()
        baseWidth = max(srceen.width(), srceen.height())
        # 宽高比 1：2
        self.resize(int(baseWidth / 1.2), int(baseWidth / 2.4))
        self.setGeometry(0, 0, self.size().width(), self.size().height())
        # 设置主窗口的标题
        self.setWindowTitle('图片查看器')

        # 整体布局
        self.main_layout = QGridLayout()
        self.main_layout.setGeometry(
            QRect(0, 0, self.size().width(), self.size().height()))
        # 上部分图片区域
        # 加载图片
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(
            0, 0, self.size().width(), self.size().height() - 40)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setEnabled(True)

        image_file = self.resource_manager.getResource(
        ).current() if self.resource_manager else ""
        self.image_view = ImageView(image_file, self.scroll_area, self)
        self.image_view.setGeometry(
            0, 0, self.size().width(), self.size().height() - 60)

        self.image_view.setStyleSheet("border:none")

        self.setTitleWithImageInfo(image_file)
        self.scroll_area.setWidget(self.image_view)
        self.main_layout.addWidget(self.scroll_area, 1, 0)

        # 底部按钮
        btns = QWidget()
        btns.setMaximumHeight(40)
        btns.setMinimumHeight(40)
        btn_layout = QHBoxLayout()
        self.prev_image = QPushButton("上一张")

        self.enlarge_image = QPushButton("放大")
        self.shrink_image = QPushButton("缩小")
        self.next_image = QPushButton("下一张")

        btn_layout.addWidget(self.prev_image)
        btn_layout.addWidget(self.enlarge_image)
        btn_layout.addWidget(self.shrink_image)
        btn_layout.addWidget(self.next_image)

        btns.setLayout(btn_layout)
        self.main_layout.addWidget(btns, 2, 0)

        self.setLayout(self.main_layout)

        #信号-槽函数连接器
        self.prev_image.clicked.connect(self.onPrevImage)
        self.next_image.clicked.connect(self.onNextImage)
        self.enlarge_image.clicked.connect(self.onEnlarge)
        self.shrink_image.clicked.connect(self.onShrink)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        if self.resource_manager is None:
            return
        self.setGeometry(0, 0, self.size().width(), self.size().height())
        self.main_layout.setGeometry(
            QRect(0, 0, self.size().width(), self.size().height()))
        self.image_view.autoAdjustImageSize(True)
        self.setTitleWithImageInfo(self.resource_manager.getResource().current())
        super().resizeEvent(a0)

    def onOpenFile(self):
        image_file, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "/", "Images(*.png *.jpg *.jpeg)", "Images(*.png *.jpg *.jpeg)")
        if image_file and len(image_file) != 0:
            self.resource_manager = ImageResourceManagerWrapper(image_file)
            if hasattr(self, "image_view"):
                current = self.resource_manager.getResource().current()
                self.image_view.setImage(current)
                self.setTitleWithImageInfo(current)

    def onOpenDir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "打开文件夹", "/")
        if dir_path or len(dir) != 0:
            self.resource_manager = ImageResourceManagerWrapper(dir_path)
            if hasattr(self, "image_view"):
                current = self.resource_manager.getResource().current()
                self.image_view.setImage(current)
                self.setTitleWithImageInfo(current)
                
    def onOpenWebpage(self):
        url, ok = QInputDialog.getText(self, "打开网页", "请输入网址")
        if ok and len(url) != 0:
            self.resource_manager = ImageResourceManagerWrapper(
                url, self.reloadImage)
            if self.resource_manager and hasattr(self, "image_view"):
                current = self.resource_manager.getResource().current()
                self.image_view.setImage(current)
                self.setTitleWithImageInfo(current)
    
    def onPrevImage(self):
        if self.resource_manager is None or len(self.resource_manager.getResource()) == 0:
            return
        image_file = self.resource_manager.getResource().prev()
        self.image_view.setImage(image_file)
        self.setTitleWithImageInfo(image_file)

    def onNextImage(self):
        if self.resource_manager is None or len(self.resource_manager.getResource()) == 0:
            return
        image_file = self.resource_manager.getResource().next()
        self.image_view.setImage(image_file)
        self.setTitleWithImageInfo(image_file)

    def onEnlarge(self):
        if self.resource_manager is None or len(self.resource_manager.getResource()) == 0:
            return
        self.image_view.enlargeScale()
        self.setTitleWithImageInfo(
            self.resource_manager.getResource().current())

    def onShrink(self):
        if self.resource_manager is None or len(self.resource_manager.getResource()) == 0:
            return
        self.image_view.shrinkScale()
        self.setTitleWithImageInfo(
            self.resource_manager.getResource().current())

    def onReloadImage(self, image_path):
        if self.resource_manager is None or len(self.resource_manager.getResource()) == 0:
            return
        self.image_view.setImage(image_path)
        self.setTitleWithImageInfo(
           image_path)

    def onEditConfig(self):
        ConfigEditDialog().exec_()
        
    def setTitleWithImageInfo(self, image_file):
        if image_file == "":
            self.setWindowTitle("图片查看器")
            return
        
        width, height = self.image_view.orignalSize().width(
        ), self.image_view.orignalSize().width()
        ratio = int(self.image_view.getCurrentRatio() * 100)
        total = len(self.resource_manager.getResource())
        index = self.resource_manager.getResource().index()
        self.setWindowTitle(
            f"""图片查看器({image_file}) {width}x{height} 缩放比例:{ratio}% ({index}/{total})""")

    def event(self, a0: QEvent) -> bool:

        if a0.type() == QEvent.FileOpen:
            QMessageBox.information(self, "打开", a0.file())

        return super().event(a0)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        key = a0.key()
        if key == Qt.Key.Key_A:  # 敲击A键跳转前一张
            self.onPrevImage()
        elif key == Qt.Key.Key_D:  # 敲击D键跳转后一张
            self.onNextImage()

        super().keyPressEvent(a0)
