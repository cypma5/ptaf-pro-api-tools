# auth.py
import json
import uuid
from urllib.parse import urljoin
import requests

class AuthManager:
    def __init__(self, base_url, username, password, api_path, verify_ssl=False, ssl_cert_path=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.api_path = api_path
        self.verify_ssl = verify_ssl
        self.ssl_cert_path = ssl_cert_path
        self.access_token = None
        self.refresh_token = None
        self.tenant_id = None
        self.fingerprint = str(uuid.uuid4()).replace("-", "")
        
        if self.ssl_cert_path:
            self.ssl_verify = self.ssl_cert_path
        else:
            self.ssl_verify = self.verify_ssl

    def get_jwt_tokens(self, make_request_func):
        """Получает JWT токены (access и refresh)"""
        url = urljoin(self.base_url, f"{self.api_path}/auth/refresh_tokens")
        payload = {
            "username": self.username,
            "password": self.password,
            "fingerprint": self.fingerprint
        }
        
        response = make_request_func("POST", url, json=payload)
        if not response:
            return False
            
        if response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            print("Успешно получены JWT токены")
            return True
        else:
            print(f"Ошибка при получении токенов. Код: {response.status_code}, Ответ: {response.text}")
            return False

    def update_jwt_with_tenant(self, make_request_func):
        """Обновляет JWT токен с учетом выбранного тенанта"""
        if not self.refresh_token:
            print("Отсутствует refresh token")
            return False
        
        url = urljoin(self.base_url, f"{self.api_path}/auth/access_tokens")
        payload = {
            "refresh_token": self.refresh_token,
            "tenant_id": self.tenant_id,
            "fingerprint": self.fingerprint
        }
        
        response = make_request_func("POST", url, json=payload)
        if not response:
            return False
            
        if response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            print(f"Успешно обновлены JWT токены для тенанта {self.tenant_id}")
            return True
        else:
            print(f"Ошибка при обновлении токенов. Код: {response.status_code}, Ответ: {response.text}")
            return False

    def get_auth_headers(self):
        """Возвращает заголовки авторизации"""
        headers = {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json"
        }
        return headers