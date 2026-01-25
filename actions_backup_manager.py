# actions_backup_manager.py (оптимизированный с BaseManager)
import os
import json
import datetime
from base_manager import BaseManager

class ActionsBackupManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
    
    def get_custom_actions(self):
        """Получает список пользовательских действий"""
        response = self.api_client.get_actions()
        all_actions = self._parse_response_items(response)
        
        if all_actions:
            # Фильтруем только пользовательские действия (is_system = False)
            custom_actions = [action for action in all_actions if not action.get('is_system', True)]
            print(f"Успешно получены пользовательские действия: {len(custom_actions)} шт.")
            return custom_actions
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
    
    def create_custom_action(self, action_data):
        """Создает новое пользовательское действие"""
        # Очищаем данные перед отправкой
        cleaned_action_data = self._clean_action_for_creation(action_data)
        response = self.api_client.create_action(cleaned_action_data)
        return response
    
    def _clean_action_for_creation(self, action_data):
        """Очищает данные действия для создания"""
        cleaned_action = action_data.copy()
        cleaned_action.pop('id', None)
        cleaned_action.pop('is_system', None)
        return cleaned_action
    
    def check_action_exists(self, action_name, tenant_id=None):
        """Проверяет, существует ли действие с таким именем"""
        if tenant_id and tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return False
        
        existing_actions = self.get_custom_actions()
        if not existing_actions:
            return False
        
        for action in existing_actions:
            if action.get('name') == action_name:
                return True
        
        return False
    
    def copy_custom_actions_to_another_tenant(self, source_tenant_id, target_tenant_id, actions_to_copy):
        """Копирует пользовательские действия из одного тенанта в другой"""
        print(f"\nКопирование пользовательских действий из тенанта {source_tenant_id} в {target_tenant_id}")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Переключаемся на исходный тенант
        self.api_client.auth_manager.tenant_id = source_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            return False, 0, 0, 0
        
        # Получаем пользовательские действия из исходного тенанта
        custom_actions = self.get_custom_actions()
        if not custom_actions:
            print("Не найдено пользовательских действий для копирования")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False, 0, 0, 0
        
        # Фильтруем действия по выбранному списку
        if actions_to_copy != "all":
            custom_actions = [action for action in custom_actions if action.get('name') in actions_to_copy]
        
        if not custom_actions:
            print("После фильтрации не осталось действий для копирования")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False, 0, 0, 0
        
        print(f"Найдено {len(custom_actions)} пользовательских действий для копирования")
        
        # Переключаемся на целевой тенант
        self.api_client.auth_manager.tenant_id = target_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False, 0, 0, 0
        
        # Копируем каждое действие
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_actions = len(custom_actions)
        
        for action in custom_actions:
            action_name = action.get('name')
            action_data = action.copy()
            
            # Проверяем, не существует ли уже такое действие в целевом тенанте
            if self.check_action_exists(action_name):
                print(f"Действие '{action_name}' уже существует в целевом тенанте, пропускаем")
                skipped_count += 1
                continue
            
            # Очищаем данные действия перед созданием
            cleaned_action_data = self._clean_action_for_creation(action_data)
            
            # Создаем действие в целевом тенанте
            response = self.create_custom_action(cleaned_action_data)
            if response and response.status_code == 201:
                print(f"Успешно скопировано действие: '{action_name}'")
                success_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при копировании действия '{action_name}': {error_msg}")
                error_count += 1
        
        # Восстанавливаем оригинальный тенант
        self.api_client.auth_manager.tenant_id = original_tenant_id
        self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
        
        return True, success_count, skipped_count, total_actions