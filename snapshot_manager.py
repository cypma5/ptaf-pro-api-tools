# snapshot_manager.py (оптимизированный с BaseManager)
import os
import json
from base_manager import BaseManager

class SnapshotManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
        from backup_manager import BackupManager
        self.backup_manager = BackupManager(api_client)
    
    def get_tenant_snapshot(self, tenant_id=None):
        """Получает конфигурацию тенанта"""
        if tenant_id and tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return None
        
        response = self.api_client.get_snapshot()
        if response and response.status_code == 200:
            print("Успешно получена конфигурация тенанта")
            return response.json()
        else:
            print(f"Ошибка при получении конфигурации")
            return None
    
    def get_available_tenants(self):
        """Получает список доступных тенантов"""
        response = self.api_client.get_tenants()
        return self._parse_response_items(response)
    
    def get_single_tenant_snapshot(self, tenant_id=None):
        """Получает конфигурацию выбранного тенанта"""
        if not tenant_id:
            # Используем TenantManager для выбора
            from tenants import TenantManager
            tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
            tenant = tenant_manager.select_single_tenant("Выберите тенант для получения конфигурации:")
            if not tenant:
                return False
            tenant_id = tenant.get('id')
            tenant_name = tenant.get('name', 'Без названия')
            print(f"\nПолучение конфигурации тенанта {tenant_name} (ID: {tenant_id})...")
        
        # Получаем конфигурацию
        snapshot = self.get_tenant_snapshot(tenant_id)
        if not snapshot:
            print("Не удалось получить конфигурацию")
            return False
        
        # Получаем бекенды
        from backends_manager import BackendsManager
        backends_manager = BackendsManager(self.api_client)
        backends = backends_manager.get_tenant_backends(tenant_id)
        
        # Получаем роли
        from roles_manager import RolesManager
        roles_manager = RolesManager(self.api_client)
        roles = roles_manager.get_roles()
        
        # Получаем пользовательские действия
        from actions_backup_manager import ActionsBackupManager
        actions_manager = ActionsBackupManager(self.api_client)
        custom_actions = actions_manager.get_custom_actions()
        
        # Сохраняем в файлы
        snapshot_filepath = self.backup_manager.save_snapshot_to_file(snapshot, tenant_id)
        backends_filepath = None
        roles_filepath = None
        actions_filepath = None
        
        if backends:
            backends_filepath = self.backup_manager.save_backends_to_file(backends, tenant_id)
        
        if roles:
            roles_filepath = self.backup_manager.save_roles_to_file(roles, tenant_id)
        
        if custom_actions:
            actions_filepath = self.backup_manager.save_custom_actions_to_file(custom_actions, tenant_id)
        
        success_files = [f for f in [snapshot_filepath, backends_filepath, roles_filepath, actions_filepath] if f]
        
        if len(success_files) >= 2:  # Хотя бы 2 файла успешно сохранены
            print("Данные тенанта успешно сохранены")
            return True
        else:
            print("Не удалось сохранить основные данные")
            return False
    
    def get_all_tenants_snapshots(self):
        """Получает конфигурации со всех доступных тенантов"""
        print("\nПолучение конфигураций со всех доступных тенантов...")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Получаем список всех тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        success_count = 0
        total_tenants = len(tenants)
        
        for tenant in tenants:
            tenant_id = tenant.get('id')
            tenant_name = tenant.get('name', 'Без названия')
            
            print(f"\nОбработка тенанта: {tenant_name} (ID: {tenant_id})")
            
            # Получаем конфигурацию тенанта
            snapshot = self.get_tenant_snapshot(tenant_id)
            if snapshot:
                # Получаем бекенды тенанта
                from backends_manager import BackendsManager
                backends_manager = BackendsManager(self.api_client)
                backends = backends_manager.get_tenant_backends(tenant_id)
                
                # Получаем роли тенанта
                from roles_manager import RolesManager
                roles_manager = RolesManager(self.api_client)
                roles = roles_manager.get_roles()
                
                # Получаем пользовательские действия
                from actions_backup_manager import ActionsBackupManager
                actions_manager = ActionsBackupManager(self.api_client)
                custom_actions = actions_manager.get_custom_actions()
                
                # Сохраняем в файлы
                snapshot_filepath = self.backup_manager.save_snapshot_to_file(snapshot, tenant_id)
                backends_success = False
                roles_success = False
                actions_success = False
                
                if backends:
                    backends_filepath = self.backup_manager.save_backends_to_file(backends, tenant_id)
                    backends_success = backends_filepath is not None
                
                if roles:
                    roles_filepath = self.backup_manager.save_roles_to_file(roles, tenant_id)
                    roles_success = roles_filepath is not None
                
                if custom_actions:
                    actions_filepath = self.backup_manager.save_custom_actions_to_file(custom_actions, tenant_id)
                    actions_success = actions_filepath is not None
                
                success_files = sum([snapshot_filepath is not None, backends_success, roles_success, actions_success])
                
                if success_files >= 2:  # Хотя бы 2 файла успешно сохранены
                    success_count += 1
                    print(f"Данные тенанта {tenant_name} успешно сохранены")
                else:
                    print(f"Не удалось сохранить основные данные тенанта {tenant_name}")
            else:
                print(f"Не удалось получить конфигурацию тенанта {tenant_name}")
        
        # Восстанавливаем оригинальный тенант
        if original_tenant_id:
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
        
        print(f"\nИтог: успешно обработано {success_count} из {total_tenants} тенантов")
        return success_count > 0
    
    def restore_security_config(self):
        """Восстанавливает конфигурацию безопасности из снапшота"""
        if not self.api_client.auth_manager.access_token:
            if not self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
                return False
        
        if not self.api_client.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return False
        
        # Поиск доступных снапшотов
        snapshot_files = self.backup_manager._find_available_snapshots(self.api_client.auth_manager.tenant_id)
        if not snapshot_files:
            print("Не найдены файлы снапшотов для восстановления")
            return False
        
        print("\nДоступные снапшоты:")
        for i, (filepath, timestamp) in enumerate(snapshot_files, 1):
            print(f"{i}. {timestamp} - {os.path.basename(filepath)}")
        
        snapshot_index = self._select_index(snapshot_files, "Выберите номер снапшота для восстановления: ")
        if snapshot_index is None:
            return False
        
        selected_file = snapshot_files[snapshot_index][0]
        print(f"Выбран файл: {selected_file}")
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла снапшота: {e}")
            return False
        
        if not snapshot_data:
            print("Файл снапшота пуст")
            return False
        
        # Подтверждение
        print("\nВНИМАНИЕ: Восстановление конфигурации безопасности перезапишет текущую конфигурацию!")
        if not self._confirm_action("Вы уверены, что хотите восстановить конфигурацию безопасности?"):
            print("Восстановление отменено")
            return False
        
        # Восстанавливаем конфигурацию
        response = self._restore_snapshot(snapshot_data)
        if response and response.status_code == 201:
            print("Конфигурация безопасности успешно восстановлена")
            return True
        else:
            error_msg = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при восстановлении конфигурации: {error_msg}")
            return False
    
    def _restore_snapshot(self, snapshot_data):
        """Восстанавливает конфигурацию из снапшота"""
        response = self.api_client.restore_snapshot(snapshot_data)
        return response
    
    def manage_snapshots(self):
        """Управление получением конфигураций"""
        while True:
            print("\nПолучение конфигураций тенантов:")
            print("1. Получить конфигурацию текущего тенанта")
            print("2. Получить конфигурацию выбранного тенанта")
            print("3. Получить конфигурации со всех тенантов")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                if not self.api_client.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                self.get_single_tenant_snapshot(self.api_client.auth_manager.tenant_id)
            
            elif choice == '2':
                self.get_single_tenant_snapshot()
            
            elif choice == '3':
                self.get_all_tenants_snapshots()
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def manage_restore(self):
        """Управление восстановлением конфигураций"""
        while True:
            print("\nВосстановление конфигураций тенантов:")
            print("1. Восстановить 'Конфигурацию безопасности' (с выбором версии снапшота)")
            print("2. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-2): ")
            
            if choice == '1':
                if not self.api_client.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                self.restore_security_config()
            
            elif choice == '2':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def get_snapshots_from_cli(self):
        """Получает конфигурации со всех тенантов (для вызова из CLI)"""
        return self.get_all_tenants_snapshots()
    
    def manage_tenant_transfer(self):
        """Управление переносом объектов между тенантами"""
        while True:
            print("\nПеренос объектов между тенантами:")
            print("1. Перенос защищаемых серверов в другой тенант")
            print("2. Перенос ролей в другой тенант")
            print("3. Перенос пользовательских действий в другой тенант")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                self.copy_backends_to_another_tenant()
            elif choice == '2':
                from roles_manager import RolesManager
                roles_manager = RolesManager(self.api_client)
                roles_manager.copy_roles_to_another_tenant()
            elif choice == '3':
                self.copy_custom_actions_to_another_tenant()
            elif choice == '4':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def copy_backends_to_another_tenant(self):
        """Копирует бекенды из одного тенанта в другой"""
        print("\nКопирование бекендов между тенантами")
        
        # Используем TenantManager для выбора тенантов
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        
        source_tenant, target_tenant = tenant_manager.select_source_and_target_tenants()
        if not source_tenant or not target_tenant:
            print("Копирование отменено")
            return False
        
        source_tenant_id = source_tenant.get('id')
        source_tenant_name = source_tenant.get('name', 'Без названия')
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return False
        
        print(f"\nКопирование бекендов из '{source_tenant_name}' в '{target_tenant_name}'")
        
        # Получаем бекенды из исходного тенанта
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Переключаемся на исходный тенант
        self.api_client.auth_manager.tenant_id = source_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            return False
        
        from backends_manager import BackendsManager
        backends_manager = BackendsManager(self.api_client)
        backends = backends_manager.get_tenant_backends()
        if not backends:
            print("Не удалось получить бекенды из исходного тенанта")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        # Очищаем данные бекендов
        cleaned_backends = backends_manager._clean_backends_data(backends)
        if isinstance(cleaned_backends, dict) and 'items' in cleaned_backends:
            backends_list = cleaned_backends['items']
        elif isinstance(cleaned_backends, list):
            backends_list = cleaned_backends
        else:
            print("Неподдерживаемый формат бекендов")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        if not backends_list:
            print("В исходном тенанте нет бекендов для копирования")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        print(f"Найдено {len(backends_list)} бекендов для копирования")
        
        # Подтверждение
        confirm_msg = f"Вы уверены, что хотите скопировать {len(backends_list)} бекендов из '{source_tenant_name}' в '{target_tenant_name}'?"
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
        
        # Копируем каждый бекенд
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_backends = len(backends_list)
        
        for backend in backends_list:
            backend_data = backend.copy()
            
            # Проверяем, не существует ли уже такой бекенд в целевом тенанте
            if backends_manager.check_backend_exists(backend_data):
                print(f"Бекенд уже существует в целевом тенанте, пропускаем: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                skipped_count += 1
                continue
            
            # Создаем бекенд в целевом тенанте
            response = backends_manager.create_backend(backend_data)
            if response and response.status_code == 201:
                print(f"Успешно скопирован бекенд: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                success_count += 1
            elif response and response.status_code == 422:
                print(f"Ошибка 422 при копировании бекенда {backend_data.get('address')}: конфликт уникальности")
                error_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при копировании бекенда {backend_data.get('address')}: {error_msg}")
                error_count += 1
        
        # Восстанавливаем оригинальный тенант
        self.api_client.auth_manager.tenant_id = original_tenant_id
        self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
        
        print(f"\nИтог копирования:")
        print(f"Успешно скопировано: {success_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")
        print(f"Ошибок: {error_count}")
        print(f"Всего бекендов: {total_backends}")
        
        return success_count > 0
    
    def copy_custom_actions_to_another_tenant(self):
        """Копирует пользовательские действия из одного тенанта в другой"""
        print("\nКопирование пользовательских действий между тенантами")
        
        # Получаем список доступных тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        source_tenant = self._select_item_from_list(tenants, "Выберите исходный тенант")
        if not source_tenant:
            return False
        
        source_tenant_id = source_tenant['id']
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Выбор целевого тенанта
        print(f"\nВыберите целевой тенант (куда копировать):")
        target_tenant = self._select_item_from_list(tenants, "Выберите целевой тенант")
        if not target_tenant:
            return False
        
        target_tenant_id = target_tenant['id']
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return False
        
        print(f"\nКопирование пользовательских действий из '{source_tenant_name}' в '{target_tenant_name}'")
        
        # Получаем пользовательские действия из исходного тенанта
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Переключаемся на исходный тенант
        self.api_client.auth_manager.tenant_id = source_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            return False
        
        from actions_backup_manager import ActionsBackupManager
        actions_manager = ActionsBackupManager(self.api_client)
        custom_actions = actions_manager.get_custom_actions()
        if not custom_actions:
            print("Не найдено пользовательских действий для копирования")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        print(f"\nНайдено {len(custom_actions)} пользовательских действий:")
        for i, action in enumerate(custom_actions, 1):
            print(f"{i}. {action.get('name')} (Тип: {action.get('type_id')})")
        
        # Выбор действий для копирования
        print("\nВыберите действия для копирования:")
        print("1. Скопировать все пользовательские действия")
        print("2. Выбрать конкретные действия")
        print("3. Отмена")
        
        choice = input("\nВаш выбор (1-3): ").strip()
        
        actions_to_copy = []
        if choice == '1':
            actions_to_copy = "all"
            print("Будут скопированы все пользовательские действия")
        elif choice == '2':
            # Выбор конкретных действий
            action_indices = self._select_multiple_indices(custom_actions, "Выберите номера действий для копирования (через запятую): ")
            if not action_indices:
                print("Не выбрано ни одного действия")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            actions_to_copy = [custom_actions[i].get('name') for i in action_indices]
            print(f"Выбрано {len(actions_to_copy)} действий для копирования")
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
        
        # Подтверждение
        action_count = len(custom_actions) if actions_to_copy == "all" else len(actions_to_copy)
        confirm_msg = f"Вы уверены, что хотите скопировать {action_count} действий из '{source_tenant_name}' в '{target_tenant_name}'?"
        if not self._confirm_action(confirm_msg):
            print("Копирование отменено")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        # Выполняем копирование
        success, success_count, skipped_count, total_actions = actions_manager.copy_custom_actions_to_another_tenant(
            source_tenant_id, target_tenant_id, actions_to_copy
        )
        
        if success:
            print(f"\nИтог копирования действий:")
            print(f"Успешно скопировано: {success_count}")
            print(f"Пропущено (уже существуют): {skipped_count}")
            print(f"Ошибок: {total_actions - success_count - skipped_count}")
            print(f"Всего действий: {total_actions}")
        else:
            print("Произошла ошибка при копировании действий")
        
        return success_count > 0