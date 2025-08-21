# tenants.py
from urllib.parse import urljoin

class TenantManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_available_tenants(self):
        """Получает список доступных тенантов для текущего пользователя"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/auth/account/tenants")
        
        response = self.make_request("GET", url)
        if not response:
            return None
                
        if response.status_code == 200:
            tenants = response.json()
            if isinstance(tenants, dict) and 'items' in tenants:
                return tenants['items']
            elif isinstance(tenants, list):
                return tenants
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(tenants)}")
                return None
        else:
            print(f"Ошибка при получении списка тенантов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def select_tenant_interactive(self):
        """Позволяет пользователю выбрать тенант из списка доступных"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        print("\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            is_default = tenant.get("is_default", False)
            description = tenant.get("description", "Без описания")
            
            default_marker = " (по умолчанию)" if is_default else ""
            print(f"{i}. {name}{default_marker}")
            print(f"   ID: {tenant_id}")
            print(f"   Описание: {description}\n")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return False
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    selected_tenant = tenants[choice]
                    self.auth_manager.tenant_id = selected_tenant.get("id")
                    if self.auth_manager.tenant_id:
                        return self.auth_manager.update_jwt_with_tenant(self.make_request)
                    print("У выбранного тенанта отсутствует ID")
                else:
                    print("Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число или 'q' для выхода.")