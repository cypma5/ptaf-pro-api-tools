# backup_manager.py (обновленный)
import os
import json
import datetime
from urllib.parse import urljoin

class BackupManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func
        from backends_manager import BackendsManager
        from roles_manager import RolesManager
        from actions_backup_manager import ActionsBackupManager
        self.backends_manager = BackendsManager(auth_manager, make_request_func)
        self.roles_manager = RolesManager(auth_manager, make_request_func)
        self.actions_backup_manager = ActionsBackupManager(auth_manager, make_request_func)

    def save_snapshot_to_file(self, snapshot, tenant_id, base_dir="snapshot"):
        """Сохраняет конфигурацию в файл"""
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-snapshot.json"
        filepath = os.path.join(tenant_dir, filename)
        
        # Получаем абсолютный путь
        absolute_filepath = os.path.abspath(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            print(f"Конфигурация сохранена в файл:")
            print(f"📁 Полный путь: {absolute_filepath}")
            return absolute_filepath
        except Exception as e:
            print(f"Ошибка при сохранении конфигурации: {e}")
            return None

def save_backends_to_file(self, backends, tenant_id, base_dir="snapshot"):
    """Сохраняет бекенды в файл"""
    # Создаем директорию для тенанта
    tenant_dir = os.path.join(base_dir, tenant_id)
    os.makedirs(tenant_dir, exist_ok=True)
    
    # Формируем имя файла с датой и временем
    current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{current_time}-backends.json"
    filepath = os.path.join(tenant_dir, filename)
    
    # Получаем абсолютный путь
    absolute_filepath = os.path.abspath(filepath)
    
    try:
        # Удаляем ключ traffic_profiles из каждого бекенда
        cleaned_backends = self.backends_manager._clean_backends_data(backends)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_backends, f, ensure_ascii=False, indent=2)
        print(f"Бекенды сохранены в файл:")
        print(f"📁 Полный путь: {absolute_filepath}")
        return absolute_filepath
    except Exception as e:
        print(f"Ошибка при сохранении бекендов: {e}")
        return None

    def save_backends_to_file(self, backends, tenant_id, base_dir="snapshot"):
        """Сохраняет бекенды в файл"""
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-backends.json"
        filepath = os.path.join(tenant_dir, filename)
        
        try:
            # Удаляем ключ traffic_profiles из каждого бекенда
            cleaned_backends = self.backends_manager._clean_backends_data(backends)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_backends, f, ensure_ascii=False, indent=2)
            print(f"Бекенды сохранены в файл: {filepath}")
            return filepath
        except Exception as e:
            print(f"Ошибка при сохранении бекендов: {e}")
            return None

    def save_roles_to_file(self, roles, tenant_id, base_dir="snapshot"):
        """Сохраняет роли в файл"""
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-roles.json"
        filepath = os.path.join(tenant_dir, filename)
        
        try:
            # Очищаем данные ролей (удаляем ID и другие системные поля)
            cleaned_roles = self._clean_roles_data(roles)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_roles, f, ensure_ascii=False, indent=2)
            print(f"Роли сохранены в файл: {filepath}")
            return filepath
        except Exception as e:
            print(f"Ошибка при сохранении ролей: {e}")
            return None

    def save_custom_actions_to_file(self, actions, tenant_id, base_dir="snapshot"):
        """Сохраняет пользовательские действия в файл"""
        return self.actions_backup_manager.save_custom_actions_to_file(actions, tenant_id, base_dir)

    def _clean_roles_data(self, roles_data):
        """Очищает данные ролей - удаляет id и is_default"""
        if isinstance(roles_data, dict) and 'items' in roles_data:
            items = roles_data['items']
            cleaned_items = []
            for role in items:
                cleaned_role = role.copy()
                # Удаляем системные поля
                cleaned_role.pop('id', None)
                cleaned_role.pop('is_default', None)
                cleaned_items.append(cleaned_role)
            return {'items': cleaned_items}
        elif isinstance(roles_data, list):
            cleaned_items = []
            for role in roles_data:
                cleaned_role = role.copy()
                # Удаляем системные поля
                cleaned_role.pop('id', None)
                cleaned_role.pop('is_default', None)
                cleaned_items.append(cleaned_role)
            return cleaned_items
        else:
            return roles_data

    def _find_available_snapshots(self, tenant_id):
        """Находит все доступные файлы снапшотов для указанного тенанта"""
        if not tenant_id:
            return []
        
        tenant_dir = os.path.join("snapshot", tenant_id)
        if not os.path.exists(tenant_dir):
            return []
        
        # Ищем все файлы снапшотов
        snapshot_files = []
        for filename in os.listdir(tenant_dir):
            if filename.endswith('-snapshot.json'):
                filepath = os.path.join(tenant_dir, filename)
                # Извлекаем timestamp из имени файла
                timestamp = filename.split('-snapshot.json')[0]
                snapshot_files.append((filepath, timestamp))
        
        # Сортируем по времени (последний первый)
        snapshot_files.sort(key=lambda x: x[1], reverse=True)
        return snapshot_files

    def _find_latest_backends_file(self, tenant_id):
        """Находит последний файл с бекендами для указанного тенанта"""
        if not tenant_id:
            return None
        
        tenant_dir = os.path.join("snapshot", tenant_id)
        if not os.path.exists(tenant_dir):
            return None
        
        # Ищем все файлы бекендов
        backends_files = []
        for filename in os.listdir(tenant_dir):
            if filename.endswith('-backends.json'):
                filepath = os.path.join(tenant_dir, filename)
                backends_files.append((filepath, os.path.getmtime(filepath)))
        
        if not backends_files:
            return None
        
        # Сортируем по времени изменения (последний первый)
        backends_files.sort(key=lambda x: x[1], reverse=True)
        return backends_files[0][0]

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