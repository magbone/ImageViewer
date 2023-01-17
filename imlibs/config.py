import os, json

class _Config():
    TEMPLATE = {
        "retry": 5,
        "cache_dir": os.getcwd() + "/cache",
        "proxy_config": {
            "enable": False,
            "proxy": {
                "http": "http://127.0.0.1:8001",
                "https": "http://127.0.0.1:8001"
            }
        }
    }
    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        self.config = self.getConfigOrCreate(config_file)
    
    def getConfigOrCreate(self, config_file: str):
        if not os.path.exists(config_file):
            json.dump(_Config.TEMPLATE, open(config_file, "w"))
        
        return json.load(open(config_file))
    
    
    def getOrDefault(self, key, default=None):
        # 使用js风格的.运算获取键值，访问TEMPLATE的retry使用getOrDefault("retry")
        # 访问proxy_config下的proxy的http使用getOrDefault("proxy_config.proxy.http")
        # default是在键不存在时，返回的默认值
        subkeys = key.split(".")
        obj_dict = self.config
        for subkey in subkeys:
            if not obj_dict or not isinstance(obj_dict, dict):
                return default
            obj_dict = obj_dict.get(subkey)
            
        return obj_dict
    
    def writeIntoConfig(self, obj):
        json.dump(obj, open(self.config_file, "w"))
        self.config = self.getConfigOrCreate(self.config_file)
    
CONFIG = _Config("./config.json")