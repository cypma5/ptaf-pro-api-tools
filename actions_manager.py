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

    def _select_action_with_prompt(self, actions, prompt):
        """Выбор действия из списка с кастомным промптом"""
        if not actions:
            return None
        
        print(f"\n{prompt}")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        action_index = self._select_index(actions, "Ваш выбор (или 'q' для отмены): ")
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

    def _select_policy(self, policies):
        """Выбор политики из списка"""
        if not policies:
            print("Не найдено политик веб приложений")
            return None
        
        print("\nДоступные политики веб приложений:")
        for i, policy in enumerate(policies, 1):
            print(f"{i}. {policy.get('name', 'Без названия')} (ID: {policy.get('id')})")
        
        policy_index = self._select_index(policies, "Выберите номер политики (или 'q' для отмены): ")
        if policy_index is None:
            return None
        
        return policies[policy_index]

    def get_web_app_policies(self):
        """Получает список политик веб приложений"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            policies = response.json()
            if isinstance(policies, dict) and 'items' in policies:
                return policies['items']
            elif isinstance(policies, list):
                return policies
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(policies)}")
                return None
        else:
            print(f"Ошибка при получении политик веб приложений. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_policy_system_rules(self, policy_id):
        """Получает список системных правил для политики веб приложения"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/rules")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            rules = response.json()
            if isinstance(rules, dict) and 'items' in rules:
                rules_data = rules['items']
                # Помечаем системные правила
                for rule in rules_data:
                    rule['is_user_rule'] = False
                return rules_data
            elif isinstance(rules, list):
                # Помечаем системные правила
                for rule in rules:
                    rule['is_user_rule'] = False
                return rules
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(rules)}")
                return None
        else:
            print(f"Ошибка при получении системных правил политики. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_policy_user_rules(self, policy_id):
        """Получает список пользовательских правил для политики веб приложения"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/user_rules")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            rules = response.json()
            if isinstance(rules, dict) and 'items' in rules:
                rules_data = rules['items']
                # Помечаем пользовательские правила
                for rule in rules_data:
                    rule['is_user_rule'] = True
                return rules_data
            elif isinstance(rules, list):
                # Помечаем пользовательские правила
                for rule in rules:
                    rule['is_user_rule'] = True
                return rules
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(rules)}")
                return None
        else:
            print(f"Ошибка при получении пользовательских правил политики. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_policy_system_rule_details(self, policy_id, rule_id):
        """Получает детали конкретного системного правила политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def get_policy_user_rule_details(self, policy_id, rule_id):
        """Получает детали конкретного пользовательского правила политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/user_rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def update_policy_system_rule_actions(self, policy_id, rule_id, new_actions):
        """Обновляет действия в системном правиле политики"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/rules/{rule_id}")
        
        update_data = {
            "actions": new_actions
        }
        
        response = self.make_request("PATCH", url, json=update_data)
        return response

    def update_policy_user_rule_actions(self, policy_id, rule_id, new_actions):
        """Обновляет действия в пользовательском правиле политики"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/{policy_id}/user_rules/{rule_id}")
        
        update_data = {
            "actions": new_actions
        }
        
        response = self.make_request("PATCH", url, json=update_data)
        return response

    def add_syslog_action_to_template(self, template_id, syslog_action_id):
        """Добавляет действие send_to_syslog в правила шаблона"""
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
        
        return total_updated, total_rules

    def add_syslog_action_to_policy(self, policy_id, syslog_action_id):
        """Добавляет действие send_to_syslog в правила политики"""
        # Получаем все правила политики (системные и пользовательские)
        system_rules = self.get_policy_system_rules(policy_id)
        user_rules = self.get_policy_user_rules(policy_id)
        
        all_rules = []
        if system_rules:
            all_rules.extend(system_rules)
        if user_rules:
            all_rules.extend(user_rules)
        
        if not all_rules:
            print("Не найдено правил в указанной политике")
            return 0, 0
        
        total_updated = 0
        total_rules = len(all_rules)
        
        for rule in all_rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            is_user_rule = rule.get('is_user_rule', False)
            
            # Получаем детали правила
            if is_user_rule:
                rule_details = self.get_policy_user_rule_details(policy_id, rule_id)
            else:
                rule_details = self.get_policy_system_rule_details(policy_id, rule_id)
                
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
            if is_user_rule:
                response = self.update_policy_user_rule_actions(policy_id, rule_id, new_actions)
            else:
                response = self.update_policy_system_rule_actions(policy_id, rule_id, new_actions)
                
            if response and response.status_code == 200:
                print(f"Успешно добавлено действие в правило '{rule_name}' ({'пользовательское' if is_user_rule else 'системное'})")
                total_updated += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        return total_updated, total_rules

    def replace_actions_in_template(self, template_id, old_action_id, new_action_id):
        """Заменяет действие в указанном шаблоне политики"""
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return 0, 0
        
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
        
        return total_replaced, total_rules

    def replace_actions_in_policy(self, policy_id, old_action_id, new_action_id):
        """Заменяет действие в указанной политике веб приложения"""
        # Получаем все правила политики (системные и пользовательские)
        system_rules = self.get_policy_system_rules(policy_id)
        user_rules = self.get_policy_user_rules(policy_id)
        
        all_rules = []
        if system_rules:
            all_rules.extend(system_rules)
        if user_rules:
            all_rules.extend(user_rules)
        
        if not all_rules:
            print("Не найдено правил в указанной политике")
            return 0, 0
        
        total_replaced = 0
        total_rules = len(all_rules)
        
        for rule in all_rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            is_user_rule = rule.get('is_user_rule', False)
            
            # Получаем детали правила
            if is_user_rule:
                rule_details = self.get_policy_user_rule_details(policy_id, rule_id)
            else:
                rule_details = self.get_policy_system_rule_details(policy_id, rule_id)
                
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
            if is_user_rule:
                response = self.update_policy_user_rule_actions(policy_id, rule_id, new_actions)
            else:
                response = self.update_policy_system_rule_actions(policy_id, rule_id, new_actions)
                
            if response and response.status_code == 200:
                print(f"Успешно заменено действие в правиле '{rule_name}' ({'пользовательское' if is_user_rule else 'системное'})")
                total_replaced += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        return total_replaced, total_rules

    def manage_actions_operations(self):
        """Основное управление операциями с действиями"""
        while True:
            print("\n=== Управление действиями в правилах ===")
            print("1. Замена или добавление действий")
            print("2. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-2): ")
            
            if choice == '1':
                self._perform_actions_operation()
            elif choice == '2':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _perform_actions_operation(self):
        """Выполнение операции с действиями"""
        # Шаг 1: Выбор типа действия
        action_type = self._select_action_type()
        if not action_type:
            return
        
        # Шаг 2: Выбор тенанта
        if not self.auth_manager.tenant_id:
            print("Сначала необходимо выбрать тенант")
            return
        
        # Шаг 3: Выбор конкретного действия
        action_data = self._select_specific_action(action_type)
        if not action_data:
            return
        
        # Шаг 4: Выбор объекта для применения (шаблон или политика)
        object_type = self._select_object_type()
        if not object_type:
            return
        
        # Шаг 5: Выполнение операции
        self._execute_operation(action_type, action_data, object_type)

    def _select_action_type(self):
        """Выбор типа действия"""
        print("\n=== Выберите тип действия ===")
        print("1. Замена действия \"Записывать событие в базу данных\" (Log to DB)")
        print("2. Замена действия \"Отправлять свой ответ\" (Custom Response)")
        print("3. Добавить действие \"Отправить событие по протоколу Syslog\" (send_to_syslog)")
        print("4. Заменить действие \"Отправить событие по протоколу Syslog\" (send_to_syslog)")
        print("5. Отмена")
        
        while True:
            choice = input("\nВаш выбор (1-5): ").strip()
            
            if choice == '1':
                return {'type': 'replace', 'action_key': 'log', 'name': 'Log to DB'}
            elif choice == '2':
                return {'type': 'replace', 'action_key': 'custom_response', 'name': 'Custom Response'}
            elif choice == '3':
                return {'type': 'add', 'action_key': 'send_to_syslog', 'name': 'send_to_syslog'}
            elif choice == '4':
                return {'type': 'replace', 'action_key': 'send_to_syslog', 'name': 'send_to_syslog'}
            elif choice == '5':
                return None
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _select_specific_action(self, action_type):
        """Выбор конкретного действия"""
        if action_type['type'] == 'add':
            # Для добавления нужен только одно действие
            actions = self._get_actions_by_type(action_type['action_key'])
            if not actions:
                print(f"Не найдено действий типа '{action_type['name']}'")
                return None
            
            selected_action = self._select_action_with_prompt(
                actions, 
                f"Выберите действие {action_type['name']} для добавления:"
            )
            if not selected_action:
                return None
            
            return {
                'new_action_id': selected_action['id'],
                'new_action_name': selected_action.get('name')
            }
        
        else:  # replace
            # Для замены нужны два действия - старое и новое
            actions = self._get_actions_by_type(action_type['action_key'])
            if not actions:
                print(f"Не найдено действий типа '{action_type['name']}'")
                return None
            
            # Выбор старого действия
            old_action = self._select_action_with_prompt(
                actions, 
                "Выберите существующее действие для замены (исходное действие):"
            )
            if not old_action:
                return None
            
            # Выбор нового действия
            new_action = self._select_action_with_prompt(
                actions, 
                "Выберите новое действие для замены (целевое действие):"
            )
            if not new_action:
                return None
            
            if old_action['id'] == new_action['id']:
                print("Старое и новое действие совпадают")
                return None
            
            return {
                'old_action_id': old_action['id'],
                'old_action_name': old_action.get('name'),
                'new_action_id': new_action['id'],
                'new_action_name': new_action.get('name')
            }

    def _select_object_type(self):
        """Выбор объекта для применения действий"""
        print("\n=== Выберите объект для применения ===")
        print("1. Замена действий в шаблоне политики")
        print("2. Замена действий в политике веб приложения")
        print("3. Отмена")
        
        while True:
            choice = input("\nВаш выбор (1-3): ").strip()
            
            if choice == '1':
                return 'template'
            elif choice == '2':
                return 'policy'
            elif choice == '3':
                return None
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _execute_operation(self, action_type, action_data, object_type):
        """Выполнение выбранной операции"""
        if object_type == 'template':
            # Выбор шаблона
            template = self._select_template()
            if not template:
                return
            
            template_id = template['id']
            template_name = template.get('name', 'Без названия')
            
            # Подтверждение
            if action_type['type'] == 'add':
                confirm_msg = f"Вы уверены, что хотите добавить действие '{action_data['new_action_name']}' во все правила шаблона '{template_name}'?"
            else:
                confirm_msg = f"Вы уверены, что хотите заменить действие '{action_data['old_action_name']}' на '{action_data['new_action_name']}' в шаблоне '{template_name}'?"
            
            confirm = input(f"\n{confirm_msg} (y/n): ").lower()
            if confirm != 'y':
                print("Отмена операции")
                return
            
            # Выполнение операции для шаблона
            if action_type['type'] == 'add':
                total_updated, total_rules = self.add_syslog_action_to_template(
                    template_id, action_data['new_action_id']
                )
                print(f"\nИтог: добавлено действий в {total_updated} из {total_rules} правил")
            else:
                total_replaced, total_rules = self.replace_actions_in_template(
                    template_id, action_data['old_action_id'], action_data['new_action_id']
                )
                print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")
        
        else:  # policy
            # Выбор политики
            policies = self.get_web_app_policies()
            if not policies:
                print("Не найдено политик веб приложений")
                return
            
            policy = self._select_policy(policies)
            if not policy:
                return
            
            policy_id = policy['id']
            policy_name = policy.get('name', 'Без названия')
            
            # Подтверждение
            if action_type['type'] == 'add':
                confirm_msg = f"Вы уверены, что хотите добавить действие '{action_data['new_action_name']}' во все правила политики '{policy_name}'?"
            else:
                confirm_msg = f"Вы уверены, что хотите заменить действие '{action_data['old_action_name']}' на '{action_data['new_action_name']}' в политике '{policy_name}'?"
            
            confirm = input(f"\n{confirm_msg} (y/n): ").lower()
            if confirm != 'y':
                print("Отмена операции")
                return
            
            # Выполнение операции для политики
            if action_type['type'] == 'add':
                total_updated, total_rules = self.add_syslog_action_to_policy(
                    policy_id, action_data['new_action_id']
                )
                print(f"\nИтог: добавлено действий в {total_updated} из {total_rules} правил")
            else:
                total_replaced, total_rules = self.replace_actions_in_policy(
                    policy_id, action_data['old_action_id'], action_data['new_action_id']
                )
                print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")