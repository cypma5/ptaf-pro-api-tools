# actions_manager.py (оптимизированный с APIClient и BaseManager)
import json
from base_manager import BaseManager

class ActionsManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
    
    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================
    
    def get_user_templates(self):
        """Получает список пользовательских шаблонов политик"""
        response = self.api_client.get_user_templates()
        return self._parse_response_items(response)
    
    def get_template_rules(self, template_id):
        """Получает список правил для шаблона политики"""
        response = self.api_client.get_template_rules(template_id)
        return self._parse_response_items(response)
    
    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        response = self.api_client.get_template_rule_details(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def update_rule_actions_only(self, template_id, rule_id, new_actions):
        """Обновляет только действия в правиле (оптимизированный PATCH)"""
        update_data = {"actions": new_actions}
        return self.api_client.update_template_rule(template_id, rule_id, update_data)
    
    def get_available_actions(self):
        """Получает список доступных действий"""
        response = self.api_client.get_actions()
        return self._parse_response_items(response)
    
    def get_action_types(self):
        """Получает список типов действий"""
        response = self.api_client.get_action_types()
        return self._parse_response_items(response)
    
    def get_web_app_policies(self):
        """Получает список политик веб приложений"""
        response = self.api_client.get_policies()
        return self._parse_response_items(response)
    
    def get_policy_system_rules(self, policy_id):
        """Получает список системных правил для политики веб приложения"""
        response = self.api_client.get_policy_system_rules(policy_id)
        rules = self._parse_response_items(response)
        if rules:
            for rule in rules:
                rule['is_user_rule'] = False
        return rules
    
    def get_policy_user_rules(self, policy_id):
        """Получает список пользовательских правил для политики веб приложения"""
        response = self.api_client.get_policy_user_rules(policy_id)
        rules = self._parse_response_items(response)
        if rules:
            for rule in rules:
                rule['is_user_rule'] = True
        return rules
    
    def get_policy_system_rule_details(self, policy_id, rule_id):
        """Получает детали конкретного системного правила политики"""
        response = self.api_client.get_policy_system_rule_details(policy_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_policy_user_rule_details(self, policy_id, rule_id):
        """Получает детали конкретного пользовательского правила политики"""
        response = self.api_client.get_policy_user_rule_details(policy_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def update_policy_system_rule_actions_only(self, policy_id, rule_id, new_actions):
        """Обновляет только действия в системном правиле политики"""
        update_data = {"actions": new_actions}
        return self.api_client.update_policy_system_rule(policy_id, rule_id, update_data)
    
    def update_policy_user_rule_actions_only(self, policy_id, rule_id, new_actions):
        """Обновляет только действия в пользовательском правиле политики"""
        update_data = {"actions": new_actions}
        return self.api_client.update_policy_user_rule(policy_id, rule_id, update_data)
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
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
        return self._select_item_from_list(templates, "Доступные шаблоны политик")
    
    def _select_action_with_prompt(self, actions, prompt):
        """Выбор действия из списка с кастомным промптом"""
        return self._select_item_from_list(actions, prompt)
    
    def _select_policy(self):
        """Выбор политики из списка"""
        policies = self.get_web_app_policies()
        return self._select_item_from_list(policies, "Доступные политики веб приложений")
    
    # ==================== ОПЕРАЦИИ С ДЕЙСТВИЯМИ ====================
    
    def add_syslog_action_to_template(self, template_id, syslog_action_id):
        """Добавляет действие send_to_syslog в правила шаблона"""
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return 0, 0
        
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
            
            # Обновляем только действия
            response = self.update_rule_actions_only(template_id, rule_id, new_actions)
            if self._check_response(response):
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
            
            # Обновляем только действия
            if is_user_rule:
                response = self.update_policy_user_rule_actions_only(policy_id, rule_id, new_actions)
            else:
                response = self.update_policy_system_rule_actions_only(policy_id, rule_id, new_actions)
                
            if self._check_response(response):
                rule_type = 'пользовательское' if is_user_rule else 'системное'
                print(f"Успешно добавлено действие в правило '{rule_name}' ({rule_type})")
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
            
            # Обновляем только действия
            response = self.update_rule_actions_only(template_id, rule_id, new_actions)
            if self._check_response(response):
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
            
            # Обновляем только действия
            if is_user_rule:
                response = self.update_policy_user_rule_actions_only(policy_id, rule_id, new_actions)
            else:
                response = self.update_policy_system_rule_actions_only(policy_id, rule_id, new_actions)
                
            if self._check_response(response):
                rule_type = 'пользовательское' if is_user_rule else 'системное'
                print(f"Успешно заменено действие в правиле '{rule_name}' ({rule_type})")
                total_replaced += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        return total_replaced, total_rules
    
    # ==================== ИНТЕРАКТИВНОЕ УПРАВЛЕНИЕ ====================
    
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
        
        # Шаг 2: Выбор тенанта (уже должен быть выбран)
        if not self.api_client.auth_manager.tenant_id:
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
            
            if not self._confirm_action(confirm_msg):
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
            policy = self._select_policy()
            if not policy:
                return
            
            policy_id = policy['id']
            policy_name = policy.get('name', 'Без названия')
            
            # Подтверждение
            if action_type['type'] == 'add':
                confirm_msg = f"Вы уверены, что хотите добавить действие '{action_data['new_action_name']}' во все правила политики '{policy_name}'?"
            else:
                confirm_msg = f"Вы уверены, что хотите заменить действие '{action_data['old_action_name']}' на '{action_data['new_action_name']}' в политике '{policy_name}'?"
            
            if not self._confirm_action(confirm_msg):
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