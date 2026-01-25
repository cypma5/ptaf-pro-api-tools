# tenants.py (обновленный)
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
        return False

    def select_single_tenant(self, prompt="Выберите тенант:"):
        """Выбирает один тенант и возвращает его данные"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return None
        
        print(f"\n{prompt}")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(tenants):
                    return tenants[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        return None

    def select_source_and_target_tenants(self):
        """Выбирает исходный и целевой тенанты для копирования"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return None, None
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер исходного тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None, None
                
                source_index = int(choice) - 1
                if 0 <= source_index < len(tenants):
                    source_tenant = tenants[source_index]
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        # Выбор целевого тенанта
        print("\nВыберите целевой тенант (куда копировать):")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер целевого тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None, None
                
                target_index = int(choice) - 1
                if 0 <= target_index < len(tenants):
                    target_tenant = tenants[target_index]
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        return source_tenant, target_tenant