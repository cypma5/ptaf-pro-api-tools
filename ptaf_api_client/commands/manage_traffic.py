import json
from typing import Optional, Dict, Any
from ..base import BaseCommand
from ...models import Tenant

class ManageTrafficCommand(BaseCommand):
    def get_traffic_settings(self) -> Optional[Dict[str, Any]]:
        """Получает текущие настройки трафика"""
        if not self.ensure_auth():
            return None
        
        if not self.auth_manager.tenant_id:
            print("Не выбран тенант")
            return None
        
        url = f"{self.config.api_path}/config/traffic_settings"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            return response.json()
        
        return None
    
    def update_traffic_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Обновляет настройки трафика"""
        if not self.ensure_auth():
            return False
        
        if not self.auth_manager.tenant_id:
            print("Не выбран тенант")
            return False
        
        url = f"{self.config.api_path}/config/traffic_settings"
        response = self.http_client.patch(url, json=settings_data)
        
        if response and response.status_code == 200:
            return True
        
        return False
    
    def _show_current_settings(self, settings: Dict[str, Any]):
        """Выводит текущие настройки"""
        print("\nТекущие настройки:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))
    
    def _edit_file_upload_settings(self, current_settings: Dict[str, Any]) -> Dict[str, Any]:
        """NGINX: Настройки загрузки файлов"""
        print("\nNGINX: Настройки загрузки файлов:")
        
        new_settings = current_settings.copy()
        
        print("Примеры значений: 10m (10 мегабайт), 1g (1 гигабайт), 0 - без ограничений")
        new_size = input(
            f"Максимальный размер загружаемого файла [{current_settings.get('core_nginx_client_max_body_size', '1g')}]: "
        )
        
        if new_size:
            new_settings['core_nginx_client_max_body_size'] = new_size
        
        if self.update_traffic_settings(new_settings):
            print("Настройки загрузки файлов обновлены")
            return new_settings
        return current_settings
    
    def _edit_sticky_session_settings(self, current_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Envoy Proxy: Sticky Session"""
        print("\nEnvoy Proxy: Sticky Session:")
        
        new_settings = current_settings.copy()
        current_cookie = current_settings.get('envoy_proxy_stateful_session_cookie', {})
        
        enabled = input(f"Включить Sticky Session? (y/n) [{'y' if current_cookie.get('enabled', False) else 'n'}]: ").lower() == 'y'
        
        if enabled:
            cookie_settings = {
                'enabled': True,
                'name': input(f"Имя куки [{current_cookie.get('name', 'STICKY_SESSION')}]: ") or current_cookie.get('name', 'STICKY_SESSION'),
                'path': input(f"Путь к ресурсу [{current_cookie.get('path', '/')}]: ") or current_cookie.get('path', '/'),
                'ttl': input(f"Время жизни куки (например, 3600s) [{current_cookie.get('ttl', '3600s')}]: ") or current_cookie.get('ttl', '3600s')
            }
            new_settings['envoy_proxy_stateful_session_cookie'] = cookie_settings
        else:
            new_settings['envoy_proxy_stateful_session_cookie'] = {'enabled': False}
        
        if self.update_traffic_settings(new_settings):
            print("Настройки Sticky Session обновлены")
            return new_settings
        return current_settings
    
    def execute(self, tenant: Optional[Tenant] = None):
        """Основной метод управления настройками трафика"""
        if tenant:
            if not self.auth_manager.update_jwt_with_tenant(tenant.id):
                print(f"Не удалось переключиться на тенанта {tenant.name}")
                return False
        else:
            tenant = self.select_tenant_interactive()
            if not tenant:
                return False
        
        current_settings = self.get_traffic_settings() or {}
        
        while True:
            print("\nУправление настройками трафика:")
            print("1. NGINX: Настройки загрузки файлов")
            print("2. Envoy Proxy: Sticky Session")
            print("3. Просмотр текущих настроек")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                current_settings = self._edit_file_upload_settings(current_settings)
            
            elif choice == '2':
                current_settings = self._edit_sticky_session_settings(current_settings)
            
            elif choice == '3':
                self._show_current_settings(current_settings)
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")