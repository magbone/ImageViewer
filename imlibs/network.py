import requests, os
from typing import List
from lxml import etree
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from .exceptions import RequestsModelException
from .support import IMAGES
from .config import CONFIG

class HTTPClient(object):
    USER_AGENT = {
        "User-Agent": "Mozilla/5.0.html (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.html.2171.71 Safari/537.36"}

    def __init__(self, url: str, headers=None, proxy_config=None) -> None:
        self.url = url
        self.proxy_config = proxy_config
        if headers:
            self.headers = HTTPClient.USER_AGENT.copy().update(headers)
        else:
            self.headers = HTTPClient.USER_AGENT.copy()

    def doGet(self) -> str:
        try:
            rs = requests.get(self.url, headers=self.headers, verify=False, proxies=self.proxy_config)
        except Exception as e:
            raise RequestsModelException(e.args[0])
        if rs.status_code != 200:
            raise RequestsModelException(
                f"Bad response status {rs.status_code} for {self.url}")

        rs.encoding = "utf-8"

        return rs.text

class BrowserClient(object):
    pass

class RequestsHelper:
    def __init__(self, proxy_config) -> None:
        self.proxy_config = proxy_config

    def getImagesSrcFromURL(self, url, headers=None) -> List[str]:
        html = HTTPClient(url, headers, self.proxy_config).doGet()
        et = etree.HTML(html)
        if et is None:
            # 空HTML文档或者内容不符合文档规范，尝试模拟浏览器
            return None
        imgs = et.xpath("//img")

        if len(imgs) == 0:
            # HTML文档里没有img标签，可以尝试模拟浏览器
            return None

        images = []
        for img in imgs:
            for (attr_name, attr_val) in img.items():
                if self.isImageSuffix(attr_val):
                    images.append(self.combineURL(url, img.get(attr_name)))
        
        return sorted(list(set(images)))

    def isImageSuffix(self, url: str) -> bool:
        url_splited = url.split(".")
        if len(url_splited) == 0:
            return False
        return url_splited[-1].lower() in IMAGES

    def combineURL(self, url: str, image_url: str) -> str:
        if image_url.startswith("http") or image_url.startswith("https"):
            return image_url
        
        return urljoin(url, image_url)

class FileDownloader(object):
    PREDOWNLOAD = 0
    DOWNLOADING = 1
    COMPLETED = 2
    DOWNLOADFAILED = 3
    
    class Job:
        def __init__(self, url=None, save_path=None, status=None) -> None:
            self.url = url
            self.save_path = save_path
            self.status = status
           
        
    def __init__(self, save_path: str, downloaded_cb_func=None) -> None:
        self.save_path = save_path
        self.jobs = {}
        self.pool = ThreadPoolExecutor(max_workers=10)
        self.downloaded_cb_func = downloaded_cb_func
        
    def addURL(self, client: HTTPClient) -> int:
        if client.url in self.jobs:
            return self.jobs[client.url].status
        self.jobs[client.url] = FileDownloader.Job(client.url)
        
        future = self.pool.submit(self._download, client)
        future.add_done_callback(self._getResult)
        
        return FileDownloader.PREDOWNLOAD
        
    def getPath(self, url: str) -> str:
        if url in self.jobs and self.jobs[url].status == FileDownloader.COMPLETED:
            return self.jobs[url].save_path
        return ""
    
    def _download(self, client: HTTPClient) -> 'Job':
        url_splited = client.url.split("/")
        if len(url_splited) == 1:
            return FileDownloader.Job(client.url, "", FileDownloader.DOWNLOADFAILED)
        file_path = os.path.join(self.save_path, url_splited[-1])
        job = FileDownloader.Job(client.url, file_path, FileDownloader.DOWNLOADING)
        
        def action(client, job, file_path) -> 'Exception':
            err = None
            for _ in range(CONFIG.getOrDefault('retry', CONFIG.TEMPLATE['retry'])):
                try:
                    print(f"下载{client.url}....")
                    rs = requests.get(client.url, headers=client.headers, verify=False, proxies=client.proxy_config)
                    
                    with open(file_path, "wb") as f:
                        for chunk in rs.iter_content(1024): 
                            f.write(chunk)
                    job.status = FileDownloader.COMPLETED
                except Exception as e:
                    err = e
                else:
                    err = None
                    break   
                finally:
                    if 'rs' in locals():
                        rs.close()
            return err
        
        error = action(client, job, file_path)
        if error != None:
            raise RequestsModelException(error.args[0])
        
        return job
    
    def _getResult(self, future):
        job = future.result()
        self.jobs[job.url] = job
        if self.downloaded_cb_func and callable(self.downloaded_cb_func):
            self.downloaded_cb_func(job.url, job.save_path)
            
    def cancel(self):
        pass

