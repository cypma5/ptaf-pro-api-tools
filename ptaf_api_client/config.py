import json
import os

class Config:
    def __init__(self, config_file="ptaf_api_client_config.json"):
        self.config_file = config_file
        self.ptaf_url = None
        self.username = None
        self.password = None
        self.api_path = None
        self.verify_ssl = False
        self.ssl_cert_path = None
        
        self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.ptaf_url = config_data.get("ptaf_url")
            self.username = config_data.get("username")
            self.password = config_data.get("password")
            self.api_path = config_data.get("api_path", "/api/ptaf/v4")
            self.verify_ssl = config_data.get("verify_ssl", False)
            self.ssl_cert_path = config_data.get("ssl_cert_path")
            
        except FileNotFoundError:
            raise Exception(f"Конфигурационный файл {self.config_file} не найден")
        except json.JSONDecodeError:
            raise Exception(f"Ошибка при чтении конфигурационного файла {self.config_file}")