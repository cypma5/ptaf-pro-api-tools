# backends_manager.py (оптимизированный с BaseManager)
import json
from base_manager import BaseManager

class BackendsManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
    
    def get_tenant_backends(self, tenant_id=None):
        """Получает список бекендов тенанта"""
        if tenant_id and tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return None
        
        response = self.api_client.get_backends()
        if response and response.status_code == 200:
            print("Успешно получены бекенды тенанта")
            return response.json()
        else:
            print(f"Ошибка при получении бекендов")
            return None
    
    def check_backend_exists(self, backend_data, tenant_id=None):
        """Проверяет, существует ли бекенд с такими же address и port"""
        if tenant_id and tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
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
        
        # Проверяем совпадение по address, port и protocol
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
        response = self.api_client.create_backend(backend_data)
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