# actions_manager.py
import json
from urllib.parse import urljoin

class ActionsManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

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

    def get_policy_templates(self):
        """Получает список шаблонов политик с пользовательскими правилами"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules")
        
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
            print(f"Ошибка при получении шаблонов политик. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_template_rules(self, template_id):
        """Получает список правил для шаблона политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules")
        
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
                print(f"Неподдерживаемый формат ответа. Полчен: {type(rules)}")
                return None
        else:
            print(f"Ошибка при получении правил шаблона. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def update_rule_actions(self, template_id, rule_id, new_actions):
        """Обновляет действия в правиле"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        
        update_data = {
            "configuration": {
                "actions": new_actions
            }
        }
        
        response = self.make_request("PATCH", url, json=update_data)
        return response

    def replace_actions_in_rule(self, template_id, rule, old_action_id, new_action_id, action_types):
        """Заменяет действие в правиле с проверкой уникальности типов"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'Без названия')
        
        # Получаем детали правила
        rule_details = self.get_rule_details(template_id, rule_id)
        if not rule_details:
            print(f"Не удалось получить детали правила '{rule_name}'")
            return False
        
        current_actions = rule_details.get('configuration', {}).get('actions', [])
        
        # Проверяем, есть ли старое действие в правиле
        if old_action_id not in current_actions:
            print(f"Действие {old_action_id} не найдено в правиле '{rule_name}'")
            return False
        
        # Получаем информацию о новом действии
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return False
        
        new_action_info = next((action for action in actions if action['id'] == new_action_id), None)
        if not new_action_info:
            print(f"Действие {new_action_id} не найдено")
            return False
        
        # Получаем тип нового действия
        new_action_type_id = new_action_info.get('type_id')
        new_action_type = next((at for at in action_types if at['id'] == new_action_type_id), None)
        if not new_action_type:
            print(f"Не удалось определить тип действия {new_action_id}")
            return False
        
        new_action_key = new_action_type.get('key')
        
        # Проверяем уникальность типа действия
        if new_action_key in ['log', 'custom_response']:
            # Проверяем, есть ли уже действие такого типа в правиле
            for action_id in current_actions:
                if action_id != old_action_id:  # Пропускаем старое действие
                    action_info = next((a for a in actions if a['id'] == action_id), None)
                    if action_info:
                        action_type_id = action_info.get('type_id')
                        action_type = next((at for at in action_types if at['id'] == action_type_id), None)
                        if action_type and action_type.get('key') == new_action_key:
                            print(f"Правило '{rule_name}' уже содержит действие типа '{new_action_key}'. Замена невозможна.")
                            return False
        
        # Заменяем действие
        new_actions = [new_action_id if action_id == old_action_id else action_id for action_id in current_actions]
        
        # Обновляем правило
        response = self.update_rule_actions(template_id, rule_id, new_actions)
        if response and response.status_code == 200:
            print(f"Успешно заменено действие в правиле '{rule_name}'")
            return True
        else:
            error_msg = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
            return False

    def replace_actions_in_all_rules(self, old_action_id, new_action_id):
        """Заменяет действие во всех правилах во всех политиках тенанта"""
        print(f"Замена действия {old_action_id} -> {new_action_id} во всех правилах...")
        
        # Получаем типы действий для проверки уникальности
        action_types = self.get_action_types()
        if not action_types:
            print("Не удалось получить типы действий")
            return False
        
        # Получаем все шаблоны политик
        templates = self.get_policy_templates()
        if not templates:
            print("Не найдено шаблонов политик")
            return False
        
        total_replaced = 0
        total_rules = 0
        
        for template in templates:
            template_id = template.get('id')
            template_name = template.get('name', 'Без названия')
            
            print(f"\nОбработка шаблона: {template_name}")
            
            # Получаем все правила шаблона
            rules = self.get_template_rules(template_id)
            if not rules:
                continue
            
            # Фильтруем только пользовательские правила
            user_rules = [rule for rule in rules if not rule.get('is_system', True)]
            
            for rule in user_rules:
                total_rules += 1
                if self.replace_actions_in_rule(template_id, rule, old_action_id, new_action_id, action_types):
                    total_replaced += 1
        
        print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")
        return total_replaced > 0

    def replace_actions_in_template_rules(self, template_id, old_action_id, new_action_id):
        """Заменяет действие во всех правилах указанной политики"""
        print(f"Замена действия {old_action_id} -> {new_action_id} в политике {template_id}...")
        
        # Получаем типы действий для проверки уникальности
        action_types = self.get_action_types()
        if not action_types:
            print("Не удалось получить типы действий")
            return False
        
        # Получаем правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанной политике")
            return False
        
        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]
        
        total_replaced = 0
        total_rules = len(user_rules)
        
        for rule in user_rules:
            if self.replace_actions_in_rule(template_id, rule, old_action_id, new_action_id, action_types):
                total_replaced += 1
        
        print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")
        return total_replaced > 0

    def replace_actions_in_specific_rules(self, template_id, rule_ids, old_action_id, new_action_id):
        """Заменяет действие в указанных правилах указанной политики"""
        print(f"Замена действия {old_action_id} -> {new_action_id} в указанных правилах политики {template_id}...")
        
        # Получаем типы действий для проверки уникальности
        action_types = self.get_action_types()
        if not action_types:
            print("Не удалось получить типы действий")
            return False
        
        # Получаем правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанной политике")
            return False
        
        total_replaced = 0
        total_rules = len(rule_ids)
        
        for rule_id in rule_ids:
            rule = next((r for r in rules if r.get('id') == rule_id), None)
            if rule and not rule.get('is_system', True):
                if self.replace_actions_in_rule(template_id, rule, old_action_id, new_action_id, action_types):
                    total_replaced += 1
            else:
                print(f"Правило {rule_id} не найдено или является системным")
        
        print(f"\nИтог: заменено действий в {total_replaced} из {total_rules} правил")
        return total_replaced > 0

    def manage_actions_replacement(self):
        """Интерактивное управление заменой действий"""
        while True:
            print("\nЗамена действий в правилах:")
            print("1. Заменить действие во всех правилах всех политик")
            print("2. Заменить действие в указанной политике")
            print("3. Заменить действие в указанных правилах указанной политики")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                self._replace_actions_all_templates()
            
            elif choice == '2':
                self._replace_actions_single_template()
            
            elif choice == '3':
                self._replace_actions_specific_rules()
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _replace_actions_all_templates(self):
        """Замена действия во всех правилах всех политик"""
        # Получаем список действий
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return
        
        print("\nДоступные действия:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        # Выбор старого действия
        old_action_index = self._select_action_index(actions, "Выберите действие для замены: ")
        if old_action_index is None:
            return
        
        old_action_id = actions[old_action_index]['id']
        
        # Выбор нового действия
        new_action_index = self._select_action_index(actions, "Выберите новое действие: ")
        if new_action_index is None:
            return
        
        new_action_id = actions[new_action_index]['id']
        
        if old_action_id == new_action_id:
            print("Старое и новое действие совпадают")
            return
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите заменить действие {old_action_id} на {new_action_id} во ВСЕХ правилах? (y/n): ").lower()
        if confirm != 'y':
            print("Отмена операции")
            return
        
        self.replace_actions_in_all_rules(old_action_id, new_action_id)

    def _replace_actions_single_template(self):
        """Замена действия в указанной политике"""
        # Получаем список шаблонов политик
        templates = self.get_policy_templates()
        if not templates:
            print("Не найдено шаблонов политик")
            return
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        # Выбор шаблона
        template_index = self._select_template_index(templates)
        if template_index is None:
            return
        
        template_id = templates[template_index]['id']
        
        # Получаем список действий
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return
        
        print("\nДоступные действия:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        # Выбор старого действия
        old_action_index = self._select_action_index(actions, "Выберите действие для замены: ")
        if old_action_index is None:
            return
        
        old_action_id = actions[old_action_index]['id']
        
        # Выбор нового действия
        new_action_index = self._select_action_index(actions, "Выберите новое действие: ")
        if new_action_index is None:
            return
        
        new_action_id = actions[new_action_index]['id']
        
        if old_action_id == new_action_id:
            print("Старое и новое действие совпадают")
            return
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите заменить действие {old_action_id} на {new_action_id} в политике {template_id}? (y/n): ").lower()
        if confirm != 'y':
            print("Отмена операции")
            return
        
        self.replace_actions_in_template_rules(template_id, old_action_id, new_action_id)

    def _replace_actions_specific_rules(self):
        """Замена действия в указанных правилах указанной политики"""
        # Получаем список шаблонов политик
        templates = self.get_policy_templates()
        if not templates:
            print("Не найдено шаблонов политик")
            return
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        # Выбор шаблона
        template_index = self._select_template_index(templates)
        if template_index is None:
            return
        
        template_id = templates[template_index]['id']
        
        # Получаем правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанной политике")
            return
        
        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]
        
        print("\nДоступные правила:")
        for i, rule in enumerate(user_rules, 1):
            print(f"{i}. {rule.get('name', 'Без названия')} (ID: {rule.get('id')})")
        
        # Выбор правил
        rule_indices = self._select_rule_indices(user_rules)
        if not rule_indices:
            return
        
        rule_ids = [user_rules[i]['id'] for i in rule_indices]
        
        # Получаем список действий
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return
        
        print("\nДоступные действия:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        # Выбор старого действия
        old_action_index = self._select_action_index(actions, "Выберите действие для замены: ")
        if old_action_index is None:
            return
        
        old_action_id = actions[old_action_index]['id']
        
        # Выбор нового действия
        new_action_index = self._select_action_index(actions, "Выберите новое действие: ")
        if new_action_index is None:
            return
        
        new_action_id = actions[new_action_index]['id']
        
        if old_action_id == new_action_id:
            print("Старое и новое действие совпадают")
            return
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите заменить действие {old_action_id} на {new_action_id} в выбранных правилах? (y/n): ").lower()
        if confirm != 'y':
            print("Отмена операции")
            return
        
        self.replace_actions_in_specific_rules(template_id, rule_ids, old_action_id, new_action_id)

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

    def _select_template_index(self, templates):
        """Выбор шаблона из списка"""
        while True:
            try:
                choice = input("Выберите номер шаблона: ").strip()
                if not choice:
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    return index
                else:
                    print("Некорректный номер шаблона")
            except ValueError:
                print("Пожалуйста, введите число")

    def _select_rule_indices(self, rules):
        """Выбор правил из списка"""
        while True:
            try:
                choice = input("Выберите номера правил (через запятую): ").strip()
                if not choice:
                    return None
                
                indices = [int(num.strip()) - 1 for num in choice.split(',')]
                valid_indices = [i for i in indices if 0 <= i < len(rules)]
                
                if valid_indices:
                    return valid_indices
                else:
                    print("Некорректные номера правил")
            except ValueError:
                print("Пожалуйста, введите числа через запятую")