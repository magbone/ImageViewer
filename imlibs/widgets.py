from PyQt5.QtCore import QSize, QRect, Qt
from PyQt5.QtWidgets import QWidget, QScrollArea, QMessageBox, QDialog, QLineEdit, QGridLayout, QLabel, QDialogButtonBox, QApplication, QRadioButton
from PyQt5.QtGui import QImage, QPainter

from .config import CONFIG

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

        if self.image.isNull() or self.image.width() == 0 or self.image.height() == 0:
            self.image_file = "图片占位.png"
            self.image: QImage = QImage(self.image_file)

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
        if self.image.isNull():
            return

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


class ConfigEditDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        srceen = desktop.screenGeometry()
        baseWidth = max(srceen.width(), srceen.height())
        # 宽高比 1：2
        self.setFixedSize(int(baseWidth / 2.4), int(baseWidth / 4.8))
        self.setGeometry(int((srceen.width() - self.size().width()) / 2),
                         int((srceen.height() - self.size().height()) / 2),
                         self.size().width(), self.size().height())
        
        self.setWindowTitle("编辑配置") 

        self.glayout = QGridLayout()

        self.max_try_times = QLabel('最大尝试次数:')
        self.max_try_times.setObjectName('max_try_times')
        self.glayout.addWidget(self.max_try_times, 0, 0)
        self.cache_dir = QLabel('缓存路径:')
        self.cache_dir.setObjectName('cache_dir')
        self.glayout.addWidget(self.cache_dir, 1, 0)
        self.proxy_config_enable = QLabel('代理设置:')
        self.proxy_config_enable.setObjectName('proxy_config_enable')
        self.glayout.addWidget(self.proxy_config_enable, 2, 0)
        self.http_proxy_ip_with_port = QLabel('HTTP:')
        self.http_proxy_ip_with_port.setObjectName('http_proxy_ip_with_port')
        self.glayout.addWidget(self.http_proxy_ip_with_port, 3, 0)
        self.https_proxy_ip_with_port = QLabel('HTTPS:')
        self.https_proxy_ip_with_port.setObjectName('https_proxy_ip_with_port')
        self.glayout.addWidget(self.https_proxy_ip_with_port, 4, 0)


        self.max_try_times_edit = QLineEdit() 
        self.max_try_times_edit.setObjectName('max_try_times_edit')
        self.max_try_times_edit.setText(str(CONFIG.getOrDefault('retry', CONFIG.TEMPLATE['retry'])))
        
        self.glayout.addWidget(self.max_try_times_edit, 0, 1)

        self.cache_dir_edit = QLineEdit()   # 用于接收用户输入的端口号
        self.cache_dir_edit.setObjectName("cache_dir_edit")
        self.cache_dir_edit.setText(CONFIG.getOrDefault(
            'cache_dir',  CONFIG.TEMPLATE['cache_dir']))
        self.glayout.addWidget(self.cache_dir_edit, 1, 1)


        proxy_enable = CONFIG.getOrDefault('proxy_config.enable', False)
        
        self.proxy_config_radio = QRadioButton()
        self.proxy_config_radio.setChecked(proxy_enable)
        self.proxy_config_radio.toggled.connect(self.onProxyConfigEnable)
        self.glayout.addWidget(self.proxy_config_radio, 2, 1)
        
        
        
        self.http_proxy_ip_with_port_edit = QLineEdit()
        self.http_proxy_ip_with_port_edit.setObjectName(
            'http_proxy_ip_with_port_edit')
        self.http_proxy_ip_with_port_edit.setText(CONFIG.getOrDefault(
            'proxy_config.proxy.http',  CONFIG.TEMPLATE['proxy_config']['proxy']['http']))
        self.http_proxy_ip_with_port_edit.setEnabled(proxy_enable)
        self.glayout.addWidget(self.http_proxy_ip_with_port_edit, 3, 1)
        
        self.https_proxy_ip_with_port_edit = QLineEdit()
        self.https_proxy_ip_with_port_edit.setObjectName(
            'https_proxy_ip_with_port_edit')
        self.https_proxy_ip_with_port_edit.setText(CONFIG.getOrDefault(
            'proxy_config.proxy.https',  CONFIG.TEMPLATE['proxy_config']['proxy']['https']))
        self.https_proxy_ip_with_port_edit.setEnabled(proxy_enable)
        self.glayout.addWidget(self.https_proxy_ip_with_port_edit, 4, 1)
        
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # 窗口中建立确认和取消按钮
        self.glayout.addWidget(self.buttons, 5, 1)

        self.buttons.accepted.connect(self.onConfirm)
        self.buttons.rejected.connect(self.reject)

        self.setLayout(self.glayout)

    def onProxyConfigEnable(self, val):
        self.http_proxy_ip_with_port_edit.setEnabled(val)
        self.https_proxy_ip_with_port_edit.setEnabled(val)

    def dataValidator(self):
        # TODO
        pass
    
    def onConfirm(self):
        self.dataValidator()
        proxy_enable = self.proxy_config_radio.isChecked()
        http_proxy = self.http_proxy_ip_with_port_edit.text() if proxy_enable else CONFIG.getOrDefault(
            'proxy_config.proxy.http', CONFIG.TEMPLATE['proxy_config']['proxy']['http'])
        https_proxy = self.https_proxy_ip_with_port_edit.text() if proxy_enable else CONFIG.getOrDefault(
            'proxy_config.proxy.https', CONFIG.TEMPLATE['proxy_config']['proxy']['https'])
        CONFIG.writeIntoConfig({
            'retry': int(self.max_try_times_edit.text()),
            'cache_dir': self.cache_dir_edit.text(),
            'proxy_config': {
                'enable': proxy_enable,
                'proxy': {
                    'http': http_proxy,
                    'https': https_proxy 
                }
            }
        })
        self.accept()
        
def errorMsg(content: str):
    QMessageBox.critical(None, "错误", content)