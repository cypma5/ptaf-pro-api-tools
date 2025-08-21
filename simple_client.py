#!/usr/bin/env python3
import argparse
import sys
import os
import json
import requests
import uuid
from urllib.parse import urljoin
import urllib3

# Отключаем предупреждения о неверифицированном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimplePTAFClient:
    def __init__(self, config_file="ptaf_api_client_config.json", debug=False):
        self.config = self.load_config(config_file)
        self.debug = debug
        self.access_token = None
        self.refresh_token = None
        self.tenant_id = None
        self.fingerprint = str(uuid.uuid4()).replace("-", "")
        
        self.headers = {
            "User-Agent": "PTAF-API-Client/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return {}
    
    def get_jwt_tokens(self):
        """Простая версия получения токенов"""
        url = urljoin(self.config.get("ptaf_url"), f"{self.config.get('api_path', '/api/ptaf/v4')}/auth/refresh_tokens")
        payload = {
            "username": self.config.get("username"),
            "password": self.config.get("password"),
            "fingerprint": self.fingerprint
        }
        
        try:
            response = requests.post(url, json=payload, verify=self.config.get("verify_ssl", False))
            if response.status_code == 201:
                tokens = response.json()
                self.access_token = tokens.get("access_token")
                self.refresh_token = tokens.get("refresh_token")
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                return True
        except Exception as e:
            print(f"Ошибка получения токенов: {e}")
        
        return False

def main():
    parser = argparse.ArgumentParser(description="Simple PTAF PRO API Client")
    parser.add_argument("--config", default="ptaf_api_client_config.json", help="Путь к конфигурационному файлу")
    parser.add_argument("--debug", action="store_true", help="Включить отладочный режим")
    
    args = parser.parse_args()
    
    client = SimplePTAFClient(config_file=args.config, debug=args.debug)
    
    if client.get_jwt_tokens():
        print("Успешно авторизован!")
        print(f"Access Token: {client.access_token[:20]}...")
    else:
        print("Ошибка авторизации")

if __name__ == "__main__":
    main()