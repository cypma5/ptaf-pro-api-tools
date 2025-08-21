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

    def _get_actions_by_type(self, action_key):
        """Получает действия определенного типа"""
        actions = self.get_available_actions()
        if not actions:
            return None
        
        action_types = self.get_action_types()
        if not action_types:
            return None
        
        # Создаем mapping для быстрого поиска типа действия по ID
        action_type_map = {at['id']: at for at in action_types}
        
        # Фильтруем действия по типу
        filtered_actions = []
        for action in actions:
            action_type = action_type_map.get(action.get('type_id'))
            if action_type and action_type.get('key') == action_key:
                filtered_actions.append(action)
        
        return filtered_actions

    def _select_template(self):
        """Выбор шаблона из списка"""
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено пользовательских шаблонов политик")
            return None
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        template_index = self._select_index(templates, "Выберите номер шаблона (или 'q' для отмены): ")
        if template_index is None:
            return None
        
        return templates[template_index]

    def _select_action(self, actions, prompt):
        """Выбор действия из списка"""
        if not actions:
            return None
        
        print(f"\nДоступные действия:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        action_index = self._select_index(actions, prompt)
        if action_index is None:
            return None
        
        return actions[action_index]

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

    def add_syslog_action(self):
        """Добавляет действие send_to_syslog в правила шаблона"""
        print("\nДобавление действия send_to_syslog")
        
        # Выбор шаблона
        template = self._select_template()
        if not template:
            return False
        
        template_id = template['id']
        template_name = template.get('name', 'Без названия')
        
        # Получаем действия типа send_to_syslog
        syslog_actions = self._get_actions_by_type('send_to_syslog')
        if not syslog_actions:
            print("Не найдено действий типа 'send_to_syslog'")
            return False
        
        # Выбор действия
        syslog_action = self._select_action(syslog_actions, "Выберите действие send_to_syslog для добавления: ")
        if not syslog_action:
            return False
        
        syslog_action_id = syslog_action['id']
        syslog_action_name = syslog_action.get('name')
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите добавить действие '{syslog_action_name}' во все правила шаблона '{template_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Отмена операции")
            return False
        
        # Получаем правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return False
        
        total_updated = 0
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
            
            # Проверяем, есть ли уже это действие в правиле
            if syslog_action_id in current_actions:
                continue
            
            # Добавляем действие
            new_actions = current_actions + [syslog_action_id]
            
            # Обновляем правило
            response = self.update_rule_actions(template_id, rule_id, new_actions)
            if response and response.status_code == 200:
                print(f"Успешно добавлено действие в правило '{rule_name}'")
                total_updated += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        print(f"\nИтог: добавлено действий в {total_updated} из {total_rules} правил")
        return total_updated > 0

    def replace_syslog_actions(self):
        """Заменяет действие send_to_syslog в правилах шаблона"""
        print("\nЗамена действия send_to_syslog")
        
        # Выбор шаблона
        template = self._select_template()
        if not template:
            return False
        
        template_id = template['id']
        template_name = template.get('name', 'Без названия')
        
        # Получаем действия типа send_to_syslog
        syslog_actions = self._get_actions_by_type('send_to_syslog')
        if not syslog_actions:
            print("Не найдено действий типа 'send_to_syslog'")
            return False
        
        # Выбор старого действия
        old_syslog_action = self._select_action(syslog_actions, "Выберите действие send_to_syslog для замены: ")
        if not old_syslog_action:
            return False
        
        old_syslog_action_id = old_syslog_action['id']
        old_syslog_action_name = old_syslog_action.get('name')
        
        # Выбор нового действия
        new_syslog_action = self._select_action(syslog_actions, "Выберите новое действие send_to_syslog: ")
        if not new_syslog_action:
            return False
        
        new_syslog_action_id = new_syslog_action['id']
        new_syslog_action_name = new_syslog_action.get('name')
        
        if old_syslog_action_id == new_syslog_action_id:
            print("Старое и новое действие совпадают")
            return False
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите заменить действие '{old_syslog_action_name}' на '{new_syslog_action_name}' в шаблоне '{template_name}'? (y/n): ").lower()
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
            if old_syslog_action_id not in current_actions:
                continue
            
            # Заменяем действие
            new_actions = [new_syslog_action_id if action_id == old_syslog_action_id else action_id for action_id in current_actions]
            
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

    def replace_actions_in_template(self):
        """Заменяет действие в указанном шаблоне политики"""
        print("\nЗамена действий в шаблоне политики")
        
        # Выбор шаблона
        template = self._select_template()
        if not template:
            return False
        
        template_id = template['id']
        template_name = template.get('name', 'Без названия')
        
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
        
        # Выбор старого действия
        old_action = self._select_action(selected_actions, "Выберите действие для замены: ")
        if not old_action:
            return False
        
        old_action_id = old_action['id']
        old_action_name = old_action.get('name')
        
        # Выбор нового действия
        new_action = self._select_action(selected_actions, "Выберите новое действие: ")
        if not new_action:
            return False
        
        new_action_id = new_action['id']
        new_action_name = new_action.get('name')
        
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

    def manage_actions_replacement(self):
        """Управление заменой действий"""
        while True:
            print("\nУправление действиями в правилах:")
            print("1. Добавить действие send_to_syslog")
            print("2. Заменить действие send_to_syslog")
            print("3. Заменить действие log или custom_response")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    return False
                self.add_syslog_action()
            
            elif choice == '2':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    return False
                self.replace_syslog_actions()
            
            elif choice == '3':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    return False
                self.replace_actions_in_template()
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")