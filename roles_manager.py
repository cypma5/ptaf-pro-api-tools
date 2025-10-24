# roles_manager.py
import json
from urllib.parse import urljoin

class RolesManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_roles(self):
        """Получает список ролей"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/auth/roles")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            roles = response.json()
            if isinstance(roles, dict) and 'items' in roles:
                return roles['items']
            elif isinstance(roles, list):
                return roles
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(roles)}")
                return None
        else:
            print(f"Ошибка при получении списка ролей. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def create_role(self, role_data):
        """Создает новую роль"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/auth/roles")
        
        # Удаляем ID из данных, так как при создании будет сгенерирован новый
        create_data = role_data.copy()
        if 'id' in create_data:
            del create_data['id']
        if 'is_default' in create_data:
            del create_data['is_default']
        
        response = self.make_request("POST", url, json=create_data)
        return response

    def check_role_exists(self, role_name, tenant_id=None):
        """Проверяет, существует ли роль с таким именем"""
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
        
        # Получаем все существующие роли
        existing_roles = self.get_roles()
        if not existing_roles:
            return False
        
        # Проверяем совпадение по имени
        for role in existing_roles:
            if role.get('name') == role_name:
                return True
        
        return False

    def copy_roles_to_another_tenant(self):
        """Копирует роли из одного тенанта в другой"""
        print("\nКопирование ролей между тенантами")
        
        # Получаем список доступных тенантов
        from snapshot_manager import SnapshotManager
        snapshot_manager = SnapshotManager(self.auth_manager, self.make_request)
        tenants = snapshot_manager.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        source_index = self._select_index(tenants, "Выберите номер исходного тенанта: ")
        if source_index is None:
            return False
        
        source_tenant = tenants[source_index]
        source_tenant_id = source_tenant['id']
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Выбор целевого тенанта
        print(f"\nВыберите целевой тенант (куда копировать):")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        target_index = self._select_index(tenants, "Выберите номер целевого тенанта: ")
        if target_index is None:
            return False
        
        target_tenant = tenants[target_index]
        target_tenant_id = target_tenant['id']
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return False
        
        print(f"\nКопирование ролей из '{source_tenant_name}' в '{target_tenant_name}'")
        
        # Получаем роли из исходного тенанта
        original_tenant_id = self.auth_manager.tenant_id
        
        # Переключаемся на исходный тенант
        self.auth_manager.tenant_id = source_tenant_id
        if not self.auth_manager.update_jwt_with_tenant(self.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.auth_manager.tenant_id = original_tenant_id
            return False
        
        roles = self.get_roles()
        if not roles:
            print("Не удалось получить роли из исходного тенанта")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Фильтруем роли - исключаем системные (is_default=True)
        custom_roles = [role for role in roles if not role.get('is_default', True)]
        
        if not custom_roles:
            print("В исходном тенанте нет пользовательских ролей для копирования")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        print(f"\nНайдено {len(custom_roles)} пользовательских ролей для копирования:")
        for i, role in enumerate(custom_roles, 1):
            print(f"{i}. {role.get('name')} - {role.get('description', 'Без описания')}")
        
        # Выбор ролей для копирования
        print("\nВыберите роли для копирования:")
        print("1. Скопировать все пользовательские роли")
        print("2. Выбрать конкретные роли")
        print("3. Отмена")
        
        choice = input("\nВаш выбор (1-3): ").strip()
        
        roles_to_copy = []
        if choice == '1':
            roles_to_copy = custom_roles
        elif choice == '2':
            # Выбор конкретных ролей
            role_indices = self._select_multiple_indices(custom_roles, "Выберите номера ролей для копирования (через запятую): ")
            if not role_indices:
                print("Не выбрано ни одной роли")
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)
                return False
            roles_to_copy = [custom_roles[i] for i in role_indices]
        elif choice == '3':
            print("Копирование отменено")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        else:
            print("Некорректный выбор")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        print(f"\nВыбрано {len(roles_to_copy)} ролей для копирования")
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите скопировать {len(roles_to_copy)} ролей из '{source_tenant_name}' в '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Переключаемся на целевой тенант
        self.auth_manager.tenant_id = target_tenant_id
        if not self.auth_manager.update_jwt_with_tenant(self.make_request):
            print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Копируем каждую роль
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_roles = len(roles_to_copy)
        
        for role in roles_to_copy:
            role_name = role.get('name')
            
            # Проверяем, не существует ли уже такая роль в целевом тенанте
            if self.check_role_exists(role_name):
                print(f"Роль '{role_name}' уже существует в целевом тенанте, пропускаем")
                skipped_count += 1
                continue
            
            # Создаем роль в целевом тенанте
            response = self.create_role(role)
            if response and response.status_code == 201:
                print(f"Успешно скопирована роль: '{role_name}'")
                success_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при копировании роли '{role_name}': {error_msg}")
                error_count += 1
        
        # Восстанавливаем оригинальный тенант
        self.auth_manager.tenant_id = original_tenant_id
        self.auth_manager.update_jwt_with_tenant(self.make_request)
        
        print(f"\nИтог копирования:")
        print(f"Успешно скопировано: {success_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")
        print(f"Ошибок: {error_count}")
        print(f"Всего ролей: {total_roles}")
        
        return success_count > 0

    def _select_index(self, items, prompt):
        """Выбор индекса из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return index
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")

    def _select_multiple_indices(self, items, prompt):
        """Выбор нескольких индексов из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() == 'q':
                    return None
                
                indices = [int(num.strip()) - 1 for num in choice.split(',') if num.strip().isdigit()]
                valid_indices = [i for i in indices if 0 <= i < len(items)]
                
                if not valid_indices:
                    print("Некорректные номера")
                    continue
                
                return valid_indices
                
            except ValueError:
                print("Пожалуйста, введите номера через запятую (например: 1,2,3)")