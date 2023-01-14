from typing import List
import sys
import os
from PyQt5.QtCore import QSize, QRect, Qt, QEvent, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QGridLayout, QPushButton, QScrollArea, QFileDialog, QMenu, QMenuBar
from PyQt5.QtGui import QResizeEvent, QImage, QPainter


class FileOrDirNotFoundException(Exception):
    pass


class ImageResource(object):
    IMAGE_SUFFIX = ['png', 'jpg', 'jpeg']

    def __init__(self, image_file_or_path) -> None:
        self.cursor = -1  # 文件指针
        self.dir_path = None

        if not os.path.exists(image_file_or_path):
            raise FileOrDirNotFoundException(f'{image_file_or_path} not found')
        elif os.path.isdir(image_file_or_path):
            self.dir_path = image_file_or_path
            self.cursor = 0
        elif os.path.isfile(image_file_or_path):
            self.dir_path = os.path.dirname(image_file_or_path)

        self.image_files = ImageResource.getAllImagesInDir(self.dir_path)
        self.image_files.sort()

        if self.cursor == -1:
            curr_image_name = os.path.basename(image_file_or_path)
            self.cursor = 0
            while self.cursor < len(self.image_files):
                if self.image_files[self.cursor] == curr_image_name:
                    break
                self.cursor += 1

    @staticmethod
    def getAllImagesInDir(dir: str) -> List[str]:
        images = []
        for file in os.listdir(dir):
            file_name_with_suffix = file.split(".")
            if len(file_name_with_suffix) > 1:
                suffix = file_name_with_suffix[-1].lower()
                if suffix in ImageResource.IMAGE_SUFFIX:
                    images.append(file)
        return images

    def current(self) -> str:
        """
        获取当前图片文件
        """
        if self.cursor >= len(self.image_files):
            return ""
        return os.path.join(self.dir_path, self.image_files[self.cursor])

    def prev(self) -> str:
        """
        获取前一个图片文件
        """
        if self.cursor >= len(self.image_files):
            return ""
        
        self.cursor = (self.cursor - 1 + len(self.image_files)
                       ) % len(self.image_files)
        return self.current()

    def next(self) -> str:
        """
        获取下一个图片文件
        """
        if self.cursor >= len(self.image_files):
            return ""
        self.cursor = (self.cursor + 1) % len(self.image_files)
        return self.current()

    def __len__(self):
        return len(self.image_files)
    
class ImageView(QWidget):
    SCALES = [0.2, 0.4, 0.6, 0.8, 0.9,
              1, 1.5, 2, 3, 4, 5, 6, 8, 10, 13, 17, 20]

    def __init__(self, image_file, parent: QScrollArea, top_widget):
        super().__init__(parent)
        self.setGeometry(0, 0, parent.size().width(),
                         parent.size().height() - 60)
        self.normalSize = True
        self.scales = [scale for scale in ImageView.SCALES]
        self.normalScaleIndex = -1
        self.currentScaleIndex = -1
        self.scroll_area = parent
        self.top_widget = top_widget
        self.setImage(image_file)
        
        
    def setImage(self, image_file: str):
        self.normalSize = True
        self.image_file = image_file
        self.image: QImage = QImage(self.image_file)
        
        if self.image.isNull():
            return
        
        self.orignal_size: QSize = self.image.size()
        self.resize(self.top_widget.size().width(),
                    self.top_widget.size().height() - 60)
        self.setGeometry(0, 0, self.top_widget.size().width(),
                         self.top_widget.size().height() - 60)
        self.scroll_area.resize(self.top_widget.size().width(),
                    self.top_widget.size().height() - 60)
        self.scroll_area.setGeometry(0, 0, self.top_widget.size().width(),
                         self.top_widget.size().height() - 60)
        self.autoAdjustImageSize()

    @property
    def orignalSize(self):
        return self.orignal_size

    @property
    def normalScale(self):
        return max(self.orignalSize.width() / self.size().width(),
                   self.orignalSize.height() / self.size().height())

    def shrinkScale(self) -> bool:
        if self.currentScaleIndex + 1 >= len(self.scales):
            # 超出scales能变化的范围，返回false
            return False
        self.currentScaleIndex += 1
        self.normalSize = (self.currentScaleIndex == self.normalScaleIndex)
        self.autoAdjustImageSize()
        return True

    def enlargeScale(self) -> bool:
        if self.currentScaleIndex - 1 < 0:
            # 超出scales能变化的范围，返回false
            return False
        self.currentScaleIndex -= 1
        self.normalSize = (self.currentScaleIndex == self.normalScaleIndex)
        self.autoAdjustImageSize()
        return True

    def getCurrentScale(self):
        if self.normalSize:  # 处于正常窗口最大情况(非缩放状态)
            scale = max(self.image.width() / self.size().width(),
                        self.image.height() / self.size().height())
            if self.normalScaleIndex != -1:
                del self.scales[self.normalScaleIndex]

            self.normalScaleIndex = 0
            while self.normalScaleIndex < len(self.scales):
                if scale < self.scales[self.normalScaleIndex]:
                    break
                self.normalScaleIndex += 1

            if self.scales[self.normalScaleIndex] > scale:
                self.scales.insert(self.normalScaleIndex, scale)

            self.currentScaleIndex = self.normalScaleIndex
        
        return self.scales[self.currentScaleIndex]

    def getCurrentRatio(self):
        return 1 / self.getCurrentScale()

    def autoAdjustImageSize(self):
        scale = self.getCurrentScale()
        
        self.adjustImageSize(scale)

    def adjustImageSize(self, scale) -> None:
        """
        根据缩放比调整图片尺寸
        """

        if scale != 1: 
            self.scaled_image = self.image.scaled(QSize(int(self.image.width(
            ) / scale), int(self.image.height() / scale)), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        if self.currentScaleIndex < self.normalScaleIndex:
            # 比正常都要大时，扩大当前画布尺寸
            width = max(self.scaled_image.width(), self.size().width())
            height = max(self.scaled_image.height(), self.size().height())
        else:
            width = self.top_widget.size().width()
            height = self.top_widget.size().height() - 60
        
        self.resize(width, height)
        self.setGeometry(0, 0, width, height)
        
        self.image_x = int(
            (self.size().width() - self.scaled_image.width()) / 2)
        self.image_y = int(
            (self.size().height() - self.scaled_image.height()) / 2)
        
        self.repaint()

    def paintEvent(self, _) -> None:
        if self.image.isNull():
            return
        painter = QPainter()
        painter.begin(self)
        rect = QRect(self.image_x, self.image_y,
                     self.scaled_image.width(), self.scaled_image.height())
        painter.drawImage(rect, self.scaled_image)
        painter.end()

    
class MainWindow(QWidget):
    resized = pyqtSignal()

    def __init__(self, args, parent=None):
        super(QWidget, self).__init__(parent)
        self.resource = None
        self.init = False
        if len(args) > 1:
            self.resource = ImageResource(args[1])
        else:
            self.onOpenFile()
        self.initUI()
    
        
    def initUI(self):
        self.menu_bar = QMenuBar(self)
        self.menu = QMenu("打开")
        open_file = self.menu.addAction("打开文件")
        open_dir  = self.menu.addAction("打开文件...")
        self.menu_bar.addMenu(self.menu)
        
        open_file.triggered.connect(self.onOpenFile)
        open_dir.triggered.connect(self.onOpenDir)
        
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
       
        image_file = self.resource.current() if self.resource else ""
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
        if self.resource is None:
            return
        self.setGeometry(0, 0, self.size().width(), self.size().height())
        self.main_layout.setGeometry(
            QRect(0, 0, self.size().width(), self.size().height()))
        self.image_view.autoAdjustImageSize()
        self.setTitleWithImageInfo(self.resource.current())
        super().resizeEvent(a0)

    def onOpenFile(self):
        image_file, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "/", "Images(*.png *.jpg *.jpeg)", "Images(*.png *.jpg *.jpeg)")
        if image_file:
            self.resource = ImageResource(image_file)
            if hasattr(self, "image_view"):
                self.image_view.setImage(self.resource.current())
                
    def onOpenDir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "打开文件夹", "/")
        if dir_path:
            self.resource = ImageResource(dir_path)
            if hasattr(self, "image_view"):
                self.image_view.setImage(self.resource.current())
                
    def onPrevImage(self):
        if self.resource is None or len(self.resource) == 0:
            return
        image_file = self.resource.prev()
        self.setTitleWithImageInfo(image_file)
        self.image_view.setImage(image_file)

    def onNextImage(self):
        if self.resource is None or len(self.resource) == 0:
            return
        image_file = self.resource.next()
        self.image_view.setImage(image_file)
        self.setTitleWithImageInfo(image_file)
        
    def onEnlarge(self):
        if self.resource is None or len(self.resource) == 0:
            return
        self.image_view.enlargeScale()
        self.setTitleWithImageInfo(self.resource.current())

    def onShrink(self):
        if self.resource is None or len(self.resource) == 0:
           return
        self.image_view.shrinkScale()
        self.setTitleWithImageInfo(self.resource.current())
        
    def setTitleWithImageInfo(self, image_file):
        if image_file == "":
            self.setWindowTitle("图片查看器")
            return
        width, height = self.image_view.orignalSize.width(
        ), self.image_view.orignalSize.width()
        ratio = int(self.image_view.getCurrentRatio() * 100)
        self.setWindowTitle(
            f"""图片查看器({image_file}) {width}x{height} 缩放比例:{ratio}%""")

    def event(self, a0: QEvent) -> bool:
        return super().event(a0)
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow(sys.argv)
    main.show()
    sys.exit(app.exec_())
