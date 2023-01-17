import os, uuid
from typing import List
from abc import ABC, abstractmethod

from .exceptions import FileOrDirNotFoundException
from .support import IMAGES
from .network import RequestsHelper, FileDownloader, HTTPClient
from .widgets import errorMsg
from .config import CONFIG

class ImageResource(ABC):
    def __init__(self, path) -> None:
        self.path = path
        self.cursor = -1  # 文件指针
        self.image_files = []
        super().__init__()

    @abstractmethod
    def current(self) -> str:
        pass

    @abstractmethod
    def prev(self) -> str:
        pass

    @abstractmethod
    def next(self) -> str:
        pass

    def path(self):
        return self.path

    def __len__(self):
        return len(self.image_files)

class LocalImageResource(ImageResource):

    def __init__(self, image_file_or_path) -> None:
        super().__init__(image_file_or_path)
        
        self.dir_path = None

        if not os.path.exists(image_file_or_path):
            raise FileOrDirNotFoundException(f'{image_file_or_path} not found')
        elif os.path.isdir(image_file_or_path):
            self.dir_path = image_file_or_path
            self.cursor = 0
        elif os.path.isfile(image_file_or_path):
            self.dir_path = os.path.dirname(image_file_or_path)

        self.image_files = LocalImageResource.getAllImagesInDir(self.dir_path)
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
                if suffix in IMAGES:
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


class WebpageImageResource(ImageResource):
    CACHE_ROOT_DIR = CONFIG.getOrDefault('cache_dir', CONFIG.TEMPLATE['cache_dir'])
    def __init__(self, url, proxy_config=None, donwload_sig=None) -> None:
        super().__init__(url)
        if not os.path.exists(self.CACHE_ROOT_DIR):
            os.mkdir(self.CACHE_ROOT_DIR)
        self.proxy_config = proxy_config
        self.url_to_files = {}
        self.cache_dir = os.path.join(self.CACHE_ROOT_DIR, str(uuid.uuid4()))
        os.mkdir(self.cache_dir)
        self.image_files = RequestsHelper(proxy_config).getImagesSrcFromURL(self.path)
        self.downloader = FileDownloader(self.cache_dir, self.download_cb_func)
        self.download_sig = donwload_sig
        
    def current(self) -> str:
        """
        获取当前图片文件
        """
        
        if self.cursor >= len(self.image_files):
            return ""

        if self.cursor < 0:
            self.cursor = 0
            
        image_url = self.image_files[self.cursor]
        
        if image_url in self.url_to_files:
            return self.url_to_files[image_url]

        self.downloader.addURL(HTTPClient(image_url, proxy_config=self.proxy_config))
    
        return self.downloader.getPath(image_url)

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

    def download_cb_func(self, url, save_path):
        if save_path != " " and url == self.image_files[self.cursor]:
            if self.download_sig:
                self.url_to_files[url] = save_path
                self.download_sig.emit(save_path)
            

class ImageResourceManager(object):
    LOCAL = 1
    WEBPAGE = 2

    def __init__(self, url_or_file: str, donwload_sig = None) -> None:
        self.setURLOrFile(url_or_file, donwload_sig)
        
    def setURLOrFile(self, url_or_file, donwload_sig):
        self.url_or_file = url_or_file
        self.resource_type = self.LOCAL
        if self.url_or_file.startswith("http") or self.url_or_file.startswith("https"):
            self.resource_type = self.WEBPAGE
            proxy_enable = CONFIG.getOrDefault("proxy_config.enable", False)
            proxy_config = CONFIG.getOrDefault("proxy_config.proxy", CONFIG.TEMPLATE['proxy_config']['proxy'])
            self.resource = WebpageImageResource(
                url_or_file, proxy_config=proxy_config if proxy_enable else None, donwload_sig=donwload_sig)
        else:
            self.resource = LocalImageResource(url_or_file)
   
    def getResource(self):
    
        return self.resource
    

def ImageResourceManagerWrapper(url_or_file: str, donwload_sig=None):
    try:
        manager = ImageResourceManager(url_or_file, donwload_sig)
    except Exception as e:
        manager = None
        errorMsg(e.args[0])
    
    return manager
        
        
    
    
        