import uuid
from urllib.parse import urljoin

class AuthManager:
    def __init__(self, config, http_client):
        self.config = config
        self.http_client = http_client
        self.access_token = None
        self.refresh_token = None
        self.tenant_id = None
        self.fingerprint = str(uuid.uuid4()).replace("-", "")
    
    def get_jwt_tokens(self):
        """Получает JWT токены (access и refresh)"""
        url = urljoin(self.config.ptaf_url, f"{self.config.api_path}/auth/refresh_tokens")
        payload = {
            "username": self.config.username,
            "password": self.config.password,
            "fingerprint": self.fingerprint
        }
        
        response = self.http_client.post(url, json=payload)
        if response and response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            self.http_client.set_auth_token(self.access_token)
            return True
        return False
    
    def update_jwt_with_tenant(self, tenant_id):
        """Обновляет JWT токен с учетом выбранного тенанта"""
        if not self.refresh_token:
            return False
        
        url = urljoin(self.config.ptaf_url, f"{self.config.api_path}/auth/access_tokens")
        payload = {
            "refresh_token": self.refresh_token,
            "tenant_id": tenant_id,
            "fingerprint": self.fingerprint
        }
        
        response = self.http_client.post(url, json=payload)
        if response and response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            self.tenant_id = tenant_id
            self.http_client.set_auth_token(self.access_token)
            return True
        return False