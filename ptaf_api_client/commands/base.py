import os
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..http_client import HttpClient
from ..auth import AuthManager
from ..models import Tenant

class BaseCommand(ABC):
    def __init__(self, config, http_client: HttpClient, auth_manager: AuthManager):
        self.config = config
        self.http_client = http_client
        self.auth_manager = auth_manager
        self.tenants: Optional[List[Tenant]] = None
    
    def ensure_auth(self):
        """Обеспечивает наличие действительного access token"""
        if not self.auth_manager.access_token:
            return self.auth_manager.get_jwt_tokens()
        return True
    
    def get_available_tenants(self) -> Optional[List[Tenant]]:
        """Получает список доступных тенантов"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/auth/account/tenants"
        full_url = f"{self.config.ptaf_url}/{url.lstrip('/')}"
        response = self.http_client.get(full_url)
        
        if response and response.status_code == 200:
            tenants_data = response.json()
            items = tenants_data.get('items', []) if isinstance(tenants_data, dict) else tenants_data
            
            tenants = []
            for tenant_data in items:
                tenants.append(Tenant(
                    id=tenant_data.get('id'),
                    name=tenant_data.get('name', 'Без названия'),
                    description=tenant_data.get('description', 'Без описания'),
                    is_default=tenant_data.get('is_default', False)
                ))
            
            self.tenants = tenants
            return tenants
        
        return None
    
    def select_tenant_interactive(self) -> Optional[Tenant]:
        """Интерактивный выбор тенанта"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return None
        
        print("\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            default_marker = " (по умолчанию)" if tenant.is_default else ""
            print(f"{i}. {tenant.name}{default_marker}")
            print(f"   ID: {tenant.id}")
            print(f"   Описание: {tenant.description}\n")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return None
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    selected_tenant = tenants[choice]
                    if self.auth_manager.update_jwt_with_tenant(selected_tenant.id):
                        return selected_tenant
                    print("Не удалось обновить токен для тенанта")
                else:
                    print("Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число или 'q' для выхода.")
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Основной метод выполнения команды"""
        pass