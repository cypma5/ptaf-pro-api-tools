# global_lists_manager.py (обновленный с APIClient)
import os
import json
import datetime
import requests

class GlobalListsManager:
    def __init__(self, api_client):
        self.api_client = api_client
    
    def get_global_lists(self):
        """Получает список всех глобальных списков"""
        response = self.api_client.get_global_lists()
        return self.api_client._parse_response_items(response)
    
    def get_global_list_details(self, list_id):
        """Получает детали конкретного глобального списка"""
        response = self.api_client.get_global_list_details(list_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def create_dynamic_global_list(self, name, description=""):
        """Создает новый динамический глобальный список"""
        files = {
            'name': (None, name),
            'description': (None, description),
            'type': (None, 'DYNAMIC')
        }
        response = self.api_client.create_global_list(files)
        if response and response.status_code == 201:
            return response.json()
        return None
    
    def create_static_global_list(self, name, description="", items=None):
        """Создает новый статический глобальный список"""
        files = {
            'name': (None, name),
            'description': (None, description),
            'type': (None, 'STATIC')
        }
        
        if items:
            files['data'] = (None, json.dumps(items), 'application/json')
        
        response = self.api_client.create_global_list(files)
        if response and response.status_code == 201:
            return response.json()
        return None
    
    def get_non_system_lists(self):
        """Получает только пользовательские (не системные) списки"""
        all_lists = self.get_global_lists()
        if not all_lists:
            return []
        
        non_system_lists = [lst for lst in all_lists if not lst.get('is_system', True)]
        
        detailed_lists = []
        for lst in non_system_lists:
            list_id = lst.get('id')
            if list_id:
                details = self.get_global_list_details(list_id)
                if details:
                    detailed_lists.append(details)
        
        return detailed_lists
    
    def find_list_by_name_and_type(self, name, list_type):
        """Ищет список по имени и типу"""
        all_lists = self.get_global_lists()
        if not all_lists:
            return None
        
        for lst in all_lists:
            if (lst.get('name') == name and 
                lst.get('type') == list_type and
                not lst.get('is_system', True)):
                return lst
        
        return None
    
    def check_list_exists(self, list_data):
        """Проверяет, существует ли список с такими же параметрами"""
        name = list_data.get('name')
        list_type = list_data.get('type')
        
        if not name or not list_type:
            return False
        
        return self.find_list_by_name_and_type(name, list_type) is not None
    
    def create_list_from_data(self, list_data):
        """Создает список из данных импорта"""
        name = list_data.get('name')
        list_type = list_data.get('type')
        description = list_data.get('description', '')
        
        if not name or not list_type:
            print(f"❌ Неверные данные списка")
            return None
        
        existing_list = self.find_list_by_name_and_type(name, list_type)
        if existing_list:
            print(f"  ✓ Список '{name}' уже существует")
            return existing_list
        
        if list_type == 'DYNAMIC':
            result = self.create_dynamic_global_list(name, description)
        elif list_type == 'STATIC':
            result = self.create_static_global_list(name, description)
        else:
            print(f"❌ Неподдерживаемый тип списка: {list_type}")
            return None
        
        if result:
            print(f"  ✓ Список '{name}' создан")
        else:
            print(f"  ✗ Ошибка при создании списка '{name}'")
        
        return result
    
    def export_global_lists(self, export_dir="global_lists_export"):
        """Экспортирует пользовательские глобальные списки"""
        print("\nЭкспорт пользовательских глобальных списков...")
        
        non_system_lists = self.get_non_system_lists()
        
        if not non_system_lists:
            print("⚠️ Нет пользовательских глобальных списков для экспорта")
            return None
        
        print(f"Найдено {len(non_system_lists)} пользовательских списков")
        
        export_data = {
            "global_lists": non_system_lists,
            "export_info": {
                "export_time": datetime.datetime.now().isoformat(),
                "tenant_id": self.api_client.auth_manager.tenant_id,
                "api_path": self.api_client.auth_manager.api_path,
                "base_url": self.api_client.auth_manager.base_url,
                "lists_count": len(non_system_lists)
            }
        }
        
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"global_lists_{timestamp}.json"
        filepath = os.path.join(export_dir, filename)
        
        # Получаем абсолютный путь
        absolute_filepath = os.path.abspath(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Глобальные списки успешно экспортированы в файл:")
            print(f"📁 Полный путь: {absolute_filepath}")
            return absolute_filepath
        except Exception as e:
            print(f"❌ Ошибка при сохранении списков: {e}")
            return None
    
    def import_global_lists(self, file_path, target_tenant_id=None):
        """Импортирует глобальные списки из JSON файла"""
        print(f"\nИмпорт глобальных списков из файла: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка при чтении файла: {e}")
            return False
        
        if 'global_lists' not in import_data:
            print("❌ Некорректный формат файла")
            return False
        
        global_lists_data = import_data.get('global_lists', [])
        
        if not global_lists_data:
            print("⚠️ В файле нет данных о глобальных списках")
            return True
        
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        if target_tenant_id and target_tenant_id != original_tenant_id:
            print(f"\n🔀 Переключаемся на тенант: {target_tenant_id}")
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return False
        
        try:
            print(f"Импорт {len(global_lists_data)} глобальных списков...")
            
            list_mapping = {}
            created_count = 0
            skipped_count = 0
            failed_count = 0
            
            for i, list_data in enumerate(global_lists_data, 1):
                original_list_id = list_data.get('id')
                list_name = list_data.get('name')
                list_type = list_data.get('type')
                
                print(f"\n  [{i}/{len(global_lists_data)}] Список: {list_name} ({list_type})")
                
                if list_data.get('is_system', True):
                    print(f"    ⚠️ Системный список, пропускаем")
                    skipped_count += 1
                    continue
                
                existing_list = self.find_list_by_name_and_type(list_name, list_type)
                
                if existing_list:
                    print(f"    ✓ Список уже существует")
                    list_mapping[original_list_id] = existing_list.get('id')
                    skipped_count += 1
                else:
                    create_data = list_data.copy()
                    for field in ['id', 'is_system', 'size', 'updated', 'is_applied', 'is_marked_to_delete']:
                        if field in create_data:
                            del create_data[field]
                    
                    result = self.create_list_from_data(create_data)
                    
                    if result:
                        new_list_id = result.get('id')
                        list_mapping[original_list_id] = new_list_id
                        created_count += 1
                    else:
                        print(f"    ✗ Ошибка при создании списка")
                        failed_count += 1
            
            print(f"\n✅ Импорт глобальных списков завершен!")
            print(f"📊 Результаты:")
            print(f"  - Создано новых списков: {created_count}")
            print(f"  - Уже существовало: {skipped_count}")
            print(f"  - Ошибок: {failed_count}")
            
            return list_mapping
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
    def manage_global_lists(self):
        """Основное меню управления глобальными списками"""
        while True:
            print("\n=== УПРАВЛЕНИЕ ГЛОБАЛЬНЫМИ СПИСКАМИ ===")
            print("1. Экспортировать пользовательские глобальные списки")
            print("2. Импортировать глобальные списки из JSON")
            print("3. Копировать глобальные списки в другой тенант")
            print("4. Показать список глобальных списков")
            print("5. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-5): ")
            
            if choice == '1':
                if not self._select_tenant_for_operation("ЭКСПОРТ ГЛОБАЛЬНЫХ СПИСКОВ"):
                    continue
                self._export_global_lists_menu()
            
            elif choice == '2':
                # Для импорта не выбираем тенант заранее
                self._import_global_lists_menu()
            
            elif choice == '3':
                # Для копирования между тенантами тоже не нужно выбирать текущий
                self._copy_global_lists_menu()
            
            elif choice == '4':
                if not self._select_tenant_for_operation("ПОКАЗАТЬ ГЛОБАЛЬНЫЕ СПИСКИ"):
                    continue
                self._show_global_lists_menu()
            
            elif choice == '5':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def _select_tenant_for_operation(self, operation_name):
        """Выбирает тенант для операции"""
        print(f"\n=== {operation_name} ===")
        print("Выберите тенант для выполнения операции:")
        
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("❌ Не удалось выбрать тенант")
            return False
        return True
    
    def _export_global_lists_menu(self):
        """Меню экспорта глобальных списков"""
        export_dir = input("Введите путь для экспорта [global_lists_export]: ").strip()
        if not export_dir:
            export_dir = "global_lists_export"
        
        print(f"\nЭкспорт глобальных списков...")
        export_file = self.export_global_lists(export_dir)
        
        if export_file:
            print(f"✅ Глобальные списки успешно экспортированы: {export_file}")
    
    def _import_global_lists_menu(self):
        """Меню импорта глобальных списков"""
        file_path = input("Введите путь к JSON файлу глобальных списков: ").strip()
        if not file_path or not os.path.exists(file_path):
            print("Файл не найден")
            return
        
        # Используем TenantManager для выбора тенанта
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        
        target_tenant = tenant_manager.select_single_tenant("Выберите целевой тенант для импорта:")
        if not target_tenant:
            print("Импорт отменен")
            return
        
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        print(f"\nИмпорт глобальных списков в тенант '{target_tenant_name}'...")
        result = self.import_global_lists(file_path, target_tenant_id)
        
        if result:
            print("✅ Импорт завершен успешно!")
        else:
            print("❌ Импорт не удался")

    def _copy_global_lists_menu(self):
        """Меню копирования глобальных списков"""
        print("\nКопирование глобальных списков между тенантами")
        
        # Используем TenantManager для выбора тенантов
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        
        source_tenant, target_tenant = tenant_manager.select_source_and_target_tenants()
        if not source_tenant or not target_tenant:
            print("Копирование отменено")
            return
        
        source_tenant_id = source_tenant.get('id')
        source_tenant_name = source_tenant.get('name', 'Без названия')
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return
        
        confirm = input(f"\nВы уверены, что хотите скопировать глобальные списки из '{source_tenant_name}' в '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            return
        
        print(f"\nКопирование глобальных списков...")
        result = self.copy_global_lists_to_another_tenant(source_tenant_id, target_tenant_id)
        
        if result:
            print("✅ Копирование завершено успешно!")
        else:
            print("❌ Копирование не удалось")

    def copy_global_lists_to_another_tenant(self, source_tenant_id, target_tenant_id):
        """Копирует глобальные списки из одного тенанта в другой"""
        print(f"\nКопирование глобальных списков из тенанта {source_tenant_id} в {target_tenant_id}...")
        
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            self.api_client.auth_manager.tenant_id = source_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("❌ Не удалось переключиться на исходный тенант")
                return False
            
            export_dir = "temp_global_lists_export"
            export_file = self.export_global_lists(export_dir)
            
            if not export_file:
                print("❌ Не удалось экспортировать глобальные списки")
                return False
            
            result = self.import_global_lists(export_file, target_tenant_id)
            
            try:
                os.remove(export_file)
                os.rmdir(export_dir)
            except:
                pass
            
            return result
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
    def _show_global_lists_menu(self):
        """Меню показа списка глобальных списков"""
        lists = self.get_global_lists()
        if lists:
            print("\nГлобальные списки:")
            for i, lst in enumerate(lists, 1):
                print(f"{i}. {lst.get('name', 'Без названия')}")
                print(f"   ID: {lst.get('id')}")
                print(f"   Тип: {lst.get('type')}")
                print(f"   Системный: {'Да' if lst.get('is_system', True) else 'Нет'}")
                print(f"   Размер: {lst.get('size', 0)}")
                print(f"   Описание: {lst.get('description', 'Нет описания')}")
                print()
        else:
            print("Не найдено глобальных списков")