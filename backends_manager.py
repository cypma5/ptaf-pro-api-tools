# backends_manager.py
import json
from urllib.parse import urljoin

class BackendsManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_tenant_backends(self, tenant_id=None):
        """Получает список бекендов тенанта"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        # Если указан tenant_id, обновляем токен для этого тенанта
        if tenant_id and tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/backends")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            backends = response.json()
            print("Успешно получены бекенды тенанта")
            return backends
        else:
            print(f"Ошибка при получении бекендов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def check_backend_exists(self, backend_data, tenant_id=None):
        """Проверяет, существует ли бекенд с такими же address и port"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return False
        
        # Если указан tenant_id, обновляем токен для этого тенанта
        if tenant_id and tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return False
        
        # Получаем все существующие бекенды
        existing_backends = self.get_tenant_backends()
        if not existing_backends:
            return False
        
        # Извлекаем список бекендов
        if isinstance(existing_backends, dict) and 'items' in existing_backends:
            backends_list = existing_backends['items']
        elif isinstance(existing_backends, list):
            backends_list = existing_backends
        else:
            return False
        
        # Проверяем совпадение по address и port
        target_address = backend_data.get('address')
        target_port = backend_data.get('port')
        target_protocol = backend_data.get('protocol')
        
        for backend in backends_list:
            if (backend.get('address') == target_address and 
                backend.get('port') == target_port and 
                backend.get('protocol') == target_protocol):
                return True
        
        return False

    def create_backend(self, backend_data):
        """Создает новый бекенд"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/backends")
        
        response = self.make_request("POST", url, json=backend_data)
        return response

    def _clean_backends_data(self, backends_data):
        """Очищает данные бекендов - удаляет traffic_profiles и id"""
        if isinstance(backends_data, dict) and 'items' in backends_data:
            items = backends_data['items']
            cleaned_items = []
            for backend in items:
                cleaned_backend = backend.copy()
                # Удаляем ненужные поля
                cleaned_backend.pop('id', None)
                cleaned_backend.pop('traffic_profiles', None)
                cleaned_items.append(cleaned_backend)
            return {'items': cleaned_items}
        elif isinstance(backends_data, list):
            cleaned_items = []
            for backend in backends_data:
                cleaned_backend = backend.copy()
                # Удаляем ненужные поля
                cleaned_backend.pop('id', None)
                cleaned_backend.pop('traffic_profiles', None)
                cleaned_items.append(cleaned_backend)
            return cleaned_items
        else:
            return backends_data