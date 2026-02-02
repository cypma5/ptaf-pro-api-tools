# backup_manager.py (обновленный)
import os
import json
import datetime
from base_manager import BaseManager

class BackupManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
        # Инициализируем другие менеджеры
        from backends_manager import BackendsManager
        from roles_manager import RolesManager
        # Используем ActionsManager вместо ActionsBackupManager
        from actions_manager import ActionsManager
        
        self.backends_manager = BackendsManager(api_client)
        self.roles_manager = RolesManager(api_client)
        self.actions_manager = ActionsManager(api_client)

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
            # Очищаем данные ролей
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
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-custom_actions.json"
        filepath = os.path.join(tenant_dir, filename)
        
        try:
            # Очищаем данные действий
            cleaned_actions = self._clean_actions_data(actions)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_actions, f, ensure_ascii=False, indent=2)
            print(f"Пользовательские действия сохранены в файл: {filepath}")
            return filepath
        except Exception as e:
            print(f"Ошибка при сохранении пользовательских действий: {e}")
            return None
    
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
    
    def _clean_actions_data(self, actions_data):
        """Очищает данные действий - удаляет id и is_system"""
        if isinstance(actions_data, dict) and 'items' in actions_data:
            items = actions_data['items']
            cleaned_items = []
            for action in items:
                if not action.get('is_system', True):
                    cleaned_action = action.copy()
                    cleaned_action.pop('id', None)
                    cleaned_action.pop('is_system', None)
                    cleaned_items.append(cleaned_action)
            return {'items': cleaned_items}
        elif isinstance(actions_data, list):
            cleaned_items = []
            for action in actions_data:
                if not action.get('is_system', True):
                    cleaned_action = action.copy()
                    cleaned_action.pop('id', None)
                    cleaned_action.pop('is_system', None)
                    cleaned_items.append(cleaned_action)
            return cleaned_items
        else:
            return actions_data

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
        """Выбор индекса из списка (переопределяем для совместимости)"""
        return super()._select_index(items, prompt)

    def _select_multiple_indices(self, items, prompt):
        """Выбор нескольких индексов из списка (переопределяем для совместимости)"""
        return super()._select_multiple_indices(items, prompt)