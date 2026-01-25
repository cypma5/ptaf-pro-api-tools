# roles_manager.py (оптимизированный с BaseManager)
import json
from base_manager import BaseManager

class RolesManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
    
    def get_roles(self):
        """Получает список ролей"""
        response = self.api_client.get_roles()
        return self._parse_response_items(response)
    
    def create_role(self, role_data):
        """Создает новую роль"""
        # Удаляем ID из данных, так как при создании будет сгенерирован новый
        create_data = role_data.copy()
        if 'id' in create_data:
            del create_data['id']
        if 'is_default' in create_data:
            del create_data['is_default']
        
        response = self.api_client.create_role(create_data)
        return response
    
    def check_role_exists(self, role_name, tenant_id=None):
        """Проверяет, существует ли роль с таким именем"""
        if tenant_id and tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return False
        
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
        snapshot_manager = SnapshotManager(self.api_client)
        tenants = snapshot_manager.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        # Выбор исходного тенанта
        source_tenant = self._select_item_from_list(
            tenants, 
            "Выберите исходный тенант (откуда копировать):"
        )
        if not source_tenant:
            return False
        
        source_tenant_id = source_tenant.get('id')
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Выбор целевого тенанта
        target_tenant = self._select_item_from_list(
            tenants,
            "Выберите целевой тенант (куда копировать):"
        )
        if not target_tenant:
            return False
        
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return False
        
        print(f"\nКопирование ролей из '{source_tenant_name}' в '{target_tenant_name}'")
        
        # Переключаемся на исходный тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        self.api_client.auth_manager.tenant_id = source_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            return False
        
        roles = self.get_roles()
        if not roles:
            print("Не удалось получить роли из исходного тенанта")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        # Фильтруем роли - исключаем системные
        custom_roles = [role for role in roles if not role.get('is_default', True)]
        
        if not custom_roles:
            print("В исходном тенанте нет пользовательских ролей для копирования")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
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
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            roles_to_copy = [custom_roles[i] for i in role_indices]
        elif choice == '3':
            print("Копирование отменено")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        else:
            print("Некорректный выбор")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        print(f"\nВыбрано {len(roles_to_copy)} ролей для копирования")
        
        # Подтверждение
        confirm_msg = f"Вы уверены, что хотите скопировать {len(roles_to_copy)} ролей из '{source_tenant_name}' в '{target_tenant_name}'?"
        if not self._confirm_action(confirm_msg):
            print("Копирование отменено")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        # Переключаемся на целевой тенант
        self.api_client.auth_manager.tenant_id = target_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
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
        self.api_client.auth_manager.tenant_id = original_tenant_id
        self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
        
        print(f"\nИтог копирования:")
        print(f"Успешно скопировано: {success_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")
        print(f"Ошибок: {error_count}")
        print(f"Всего ролей: {total_roles}")
        
        return success_count > 0