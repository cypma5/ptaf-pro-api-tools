# actions_manager.py
import json
from urllib.parse import urljoin

class ActionsManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_user_templates(self):
        """Получает список пользовательских шаблонов политик"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            templates = response.json()
            if isinstance(templates, dict) and 'items' in templates:
                return templates['items']
            elif isinstance(templates, list):
                return templates
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(templates)}")
                return None
        else:
            print(f"Ошибка при получении пользовательских шаблонов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_template_rules(self, template_id):
        """Получает список правил для шаблона политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            rules = response.json()
            if isinstance(rules, dict) and 'items' in rules:
                return rules['items']
            elif isinstance(rules, list):
                return rules
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(rules)}")
                return None
        else:
            print(f"Ошибка при получении правил шаблона. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def update_rule_actions(self, template_id, rule_id, new_actions):
        """Обновляет действия в правиле"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        update_data = {
            "actions": new_actions
        }
        
        response = self.make_request("PATCH", url, json=update_data)
        return response

    def get_available_actions(self):
        """Получает список доступных действий"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/actions")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            actions = response.json()
            if isinstance(actions, dict) and 'items' in actions:
                return actions['items']
            elif isinstance(actions, list):
                return actions
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(actions)}")
                return None
        else:
            print(f"Ошибка при получении списка действий. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_action_types(self):
        """Получает список типов действий"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/action_types")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            action_types = response.json()
            if isinstance(action_types, dict) and 'items' in action_types:
                return action_types['items']
            elif isinstance(action_types, list):
                return action_types
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(action_types)}")
                return None
        else:
            print(f"Ошибка при получении типов действий. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def replace_actions_in_template(self):
        """Заменяет действие в указанном шаблоне политики"""
        print("\nЗамена действий в шаблоне политики")
        
        # Получаем список шаблонов
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено пользовательских шаблонов политик")
            return False
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        # Выбор шаблона
        template_index = self._select_template_index(templates)
        if template_index is None:
            return False
        
        template_id = templates[template_index]['id']
        template_name = templates[template_index].get('name', 'Без названия')
        
        # Получаем доступные действия
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return False
        
        # Получаем типы действий
        action_types = self.get_action_types()
        if not action_types:
            print("Не удалось получить типы действий")
            return False
        
        # Создаем mapping для быстрого поиска типа действия по ID
        action_type_map = {at['id']: at for at in action_types}
        
        # Фильтруем действия только типа log и custom_response
        filtered_actions = []
        for action in actions:
            action_type = action_type_map.get(action.get('type_id'))
            if action_type and action_type.get('key') in ['log', 'custom_response']:
                filtered_actions.append(action)
        
        if not filtered_actions:
            print("Не найдено действий типа 'log' или 'custom_response'")
            return False
        
        # Группируем действия по типу
        log_actions = []
        custom_response_actions = []
        
        for action in filtered_actions:
            action_type = action_type_map.get(action.get('type_id'))
            if action_type:
                if action_type.get('key') == 'log':
                    log_actions.append(action)
                elif action_type.get('key') == 'custom_response':
                    custom_response_actions.append(action)
        
        print("\nВыберите тип действия для замены:")
        print("1. log действия")
        print("2. custom_response действия")
        
        action_type_choice = input("Ваш выбор (1-2): ").strip()
        
        if action_type_choice == '1':
            if not log_actions:
                print("Не найдено действий типа 'log'")
                return False
            selected_actions = log_actions
            action_key = 'log'
        elif action_type_choice == '2':
            if not custom_response_actions:
                print("Не найдено действий типа 'custom_response'")
                return False
            selected_actions = custom_response_actions
            action_key = 'custom_response'
        else:
            print("Некорректный выбор")
            return False
        
        print(f"\nДоступные действия типа '{action_key}':")
        for i, action in enumerate(selected_actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        # Выбор старого действия
        old_action_index = self._select_action_index(selected_actions, "Выберите действие для замены: ")
        if old_action_index is None:
            return False
        
        old_action_id = selected_actions[old_action_index]['id']
        old_action_name = selected_actions[old_action_index].get('name')
        
        # Выбор нового действия
        new_action_index = self._select_action_index(selected_actions, "Выберите новое действие: ")
        if new_action_index is None:
            return False
        
        new_action_id = selected_actions[new_action_index]['id']
        new_action_name = selected_actions[new_action_index].get('name')
        
        if old_action_id == new_action_id:
            print("Старое и новое действие совпадают")
            return False
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите заменить действие '{old_action_name}' на '{new_action_name}' в шаблоне '{template_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Отмена операции")
            return False
        
        # Получаем правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return False
        
        total_replaced = 0
        total_rules = len(rules)
        
        for rule in rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            
            # Получаем детали правила
            rule_details = self.get_rule_details(template_id, rule_id)
            if not rule_details:
                print(f"Не удалось получить детали правила '{rule_name}'")
                continue
            
            current_actions = rule_details.get('actions', [])
            
            # Проверяем, есть ли старое действие в правиле
            if old_action_id not in current_actions:
                continue
            
            # Заменяем действие
            new_actions = [new_action_id if action_id == old_action_id else action_id for action_id in current_actions]
            
            # Обновляем правило
            response = self.update_rule_actions(template_id, rule_id, new_actions)
            if response and response.status_code == 200:
                print(f"Успешно заменено действие в правиле '{rule_name}'")
                total_replaced += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")
        return total_replaced > 0

    def _select_template_index(self, templates):
        """Выбор шаблона из списка"""
        while True:
            try:
                choice = input("Выберите номер шаблона (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    return index
                else:
                    print("Некорректный номер шаблона")
            except ValueError:
                print("Пожалуйста, введите число")

    def _select_action_index(self, actions, prompt):
        """Выбор действия из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if not choice:
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(actions):
                    return index
                else:
                    print("Некорректный номер действия")
            except ValueError:
                print("Пожалуйста, введите число")

    def manage_actions_replacement(self):
        """Управление заменой действий"""
        return self.replace_actions_in_template()