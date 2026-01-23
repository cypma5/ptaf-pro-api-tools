# global_lists_manager.py
import os
import json
import datetime
from urllib.parse import urljoin
import requests

class GlobalListsManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_global_lists(self):
        """Получает список всех глобальных списков"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/global_lists")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении глобальных списков")
            return None
        
        lists_data = response.json()
        if isinstance(lists_data, dict) and 'items' in lists_data:
            return lists_data['items']
        elif isinstance(lists_data, list):
            return lists_data
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_global_list_details(self, list_id):
        """Получает детали конкретного глобального списка"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/global_lists/{list_id}")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении деталей списка {list_id}")
            return None
        
        return response.json()

    def create_dynamic_global_list(self, name, description=""):
        """Создает новый динамический глобальный список"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/global_lists")
        
        files = {
            'name': (None, name),
            'description': (None, description),
            'type': (None, 'DYNAMIC')
        }
        
        headers = self._get_auth_headers()
        response = requests.post(
            url,
            files=files,
            headers=headers,
            verify=self.auth_manager.ssl_verify,
            timeout=30
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Ошибка при создании динамического списка: {response.status_code}")
            return None

    def create_static_global_list(self, name, description="", items=None):
        """Создает новый статический глобальный список"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/global_lists")
        
        files = {
            'name': (None, name),
            'description': (None, description),
            'type': (None, 'STATIC')
        }
        
        if items:
            files['data'] = (None, json.dumps(items), 'application/json')
        
        headers = self._get_auth_headers()
        response = requests.post(
            url,
            files=files,
            headers=headers,
            verify=self.auth_manager.ssl_verify,
            timeout=30
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Ошибка при создании статического списка: {response.status_code}")
            return None

    def _get_auth_headers(self):
        """Получает заголовки авторизации для прямых requests"""
        headers = {
            "User-Agent": "PTAF-API-Client/1.0",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.auth_manager.access_token}" if self.auth_manager.access_token else "",
        }
        return headers

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
                "tenant_id": self.auth_manager.tenant_id,
                "api_path": self.auth_manager.api_path,
                "base_url": self.auth_manager.base_url,
                "lists_count": len(non_system_lists)
            }
        }
        
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"global_lists_{timestamp}.json"
        filepath = os.path.join(export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Глобальные списки успешно экспортированы в файл: {filepath}")
            return filepath
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
        
        original_tenant_id = self.auth_manager.tenant_id
        
        if target_tenant_id and target_tenant_id != original_tenant_id:
            print(f"\n🔀 Переключаемся на тенант: {target_tenant_id}")
            self.auth_manager.tenant_id = target_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
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
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)

    def copy_global_lists_to_another_tenant(self, source_tenant_id, target_tenant_id):
        """Копирует глобальные списки из одного тенанта в другой"""
        print(f"\nКопирование глобальных списков из тенанта {source_tenant_id} в {target_tenant_id}...")
        
        original_tenant_id = self.auth_manager.tenant_id
        
        try:
            self.auth_manager.tenant_id = source_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
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
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)