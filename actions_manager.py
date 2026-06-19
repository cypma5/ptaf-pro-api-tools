# actions_manager.py (оптимизированный с APIClient и BaseManager)
import json
from base_manager import BaseManager


def _print_rule_update_error(response, rule_name):
    """Выводит код ответа и тело при ошибке обновления правила (например 422 с причиной)."""
    if response is not None:
        code = getattr(response, 'status_code', None)
        body = response.text if getattr(response, 'text', None) else "(пусто)"
        print(f"Ошибка при обновлении правила '{rule_name}': HTTP {code}")
        print(f"  Тело ответа: {body}")
    else:
        print(f"Ошибка при обновлении правила '{rule_name}': Неизвестная ошибка (нет ответа)")


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
    
    def update_policy_user_rule_actions_only(self, policy_id, rule_id, new_actions, rule_details=None):
        """Обновляет действия в пользовательском правиле политики (configuration.actions)."""
        update_data = self._build_policy_user_rule_actions_update(new_actions, rule_details)
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

    def _get_rule_threat(self, rule):
        """Возвращает уровень критичности правила (event.threat)."""
        event = rule.get('event')
        if not isinstance(event, dict):
            return None
        return event.get('threat')

    def _collect_threat_levels(self, rules):
        """Собирает уникальные уровни threat из списка правил с количеством."""
        counts = {}
        for rule in rules:
            threat = self._get_rule_threat(rule)
            key = threat if threat is not None else '__unset__'
            counts[key] = counts.get(key, 0) + 1

        levels = []
        for threat_key, count in sorted(counts.items(), key=lambda item: (item[0] == '__unset__', str(item[0]))):
            if threat_key == '__unset__':
                display = '(не указан)'
                value = None
            else:
                display = threat_key
                value = threat_key
            levels.append({'value': value, 'display': display, 'count': count})
        return levels

    def _select_replace_scope(self, rules):
        """Выбор области применения замены: все правила или по фильтру threat."""
        if not rules:
            print("Не найдено правил для применения операции")
            return None

        print("\n=== Область применения ===")
        print("1. Применить ко всем правилам")
        print("2. Применить по фильтру")
        print("3. Отмена")

        while True:
            choice = input("\nВаш выбор (1-3): ").strip()
            if choice == '1':
                return {'mode': 'all'}
            if choice == '3':
                return None
            if choice != '2':
                print("Некорректный выбор. Попробуйте снова.")
                continue

            threat_levels = self._collect_threat_levels(rules)
            if not threat_levels:
                print("Не удалось определить уровни критичности в правилах")
                return None

            print("\nФильтр по уровню критичности правил (threat):")
            for index, level in enumerate(threat_levels, 1):
                print(f"{index}. {level['display']} ({level['count']} правил)")

            threat_choice = input(f"Выберите уровень [1-{len(threat_levels)}] или q для отмены: ").strip()
            if threat_choice.lower() == 'q':
                return None

            try:
                selected = threat_levels[int(threat_choice) - 1]
            except (ValueError, IndexError):
                print("Некорректный выбор. Попробуйте снова.")
                continue

            return {'mode': 'threat', 'value': selected['value'], 'display': selected['display']}

    def _rule_matches_threat_filter(self, rule, threat_filter):
        """Проверяет, подходит ли правило под фильтр по threat."""
        if threat_filter is None:
            return True
        return self._get_rule_threat(rule) == threat_filter

    def _get_rules_for_object(self, object_type, object_id):
        """Возвращает список правил для шаблона или политики."""
        if object_type == 'template':
            return self.get_template_rules(object_id) or []

        system_rules = self.get_policy_system_rules(object_id) or []
        user_rules = self.get_policy_user_rules(object_id) or []
        return list(system_rules) + list(user_rules)

    def _build_replace_confirm_message(self, action_data, object_label, object_name, scope):
        """Формирует текст подтверждения замены действия."""
        base = (
            f"Заменить действие '{action_data['old_action_name']}' "
            f"на '{action_data['new_action_name']}'"
        )
        if scope['mode'] == 'all':
            return f"{base} во всех правилах {object_label} '{object_name}'?"
        return (
            f"{base} в правилах {object_label} '{object_name}' "
            f"с уровнем критичности '{scope['display']}'?"
        )

    def _extract_rule_actions(self, rule_data, prefer_configuration=False):
        """Извлекает список действий из ответа API правила."""
        if not isinstance(rule_data, dict):
            return None
        configuration = rule_data.get('configuration')
        config_actions = None
        if isinstance(configuration, dict) and 'actions' in configuration:
            config_actions = configuration['actions']

        if prefer_configuration or rule_data.get('is_system') is False:
            if config_actions is not None:
                return config_actions

        if 'actions' in rule_data:
            return rule_data['actions']
        if config_actions is not None:
            return config_actions
        return None

    def _build_policy_user_rule_actions_update(self, new_actions, rule_details=None):
        """Формирует тело PATCH для пользовательского правила политики."""
        parameters = []
        if rule_details and isinstance(rule_details.get('configuration'), dict):
            parameters = rule_details['configuration'].get('parameters') or []
        return {
            'configuration': {
                'actions': new_actions,
                'parameters': parameters,
            }
        }

    def _has_policy_actions_override(self, rule_details):
        """Проверяет, заданы ли действия на уровне политики (не наследуются из шаблона)."""
        if not isinstance(rule_details, dict):
            return False
        if 'actions' in rule_details:
            return rule_details['actions'] is not None
        configuration = rule_details.get('configuration')
        if isinstance(configuration, dict) and 'actions' in configuration:
            return configuration['actions'] is not None
        return False

    def _get_policy_template_id(self, policy_id):
        """Возвращает template_id политики (см. GET /config/policies/{id} в swagger)."""
        response = self.api_client.get_policy_details(policy_id)
        if response and response.status_code == 200:
            data = response.json()
            if data.get('template_id'):
                return data.get('template_id')
            template = data.get('template')
            if isinstance(template, dict) and template.get('id'):
                return template.get('id')
            user_template = data.get('user_template')
            if isinstance(user_template, dict) and user_template.get('id'):
                return user_template.get('id')
            return data.get('policy_template_id') or data.get('user_template_id')
        return None

    def _is_vendor_template_type(self, template_type):
        return template_type == 'VENDOR_TEMPLATE'

    def _get_template_rules_list(self, template_id, template_type=None, template_rules_cache=None):
        """Возвращает список правил шаблона (user или vendor) с кэшированием."""
        cache = template_rules_cache if template_rules_cache is not None else {}
        cache_key = (template_id, template_type or 'USER')
        if cache_key in cache:
            return cache[cache_key]

        if self._is_vendor_template_type(template_type):
            response = self.api_client.get_vendor_template_rules(template_id)
        else:
            response = self.api_client.get_template_rules(template_id)
        rules = self._parse_response_items(response) or []
        cache[cache_key] = rules
        return rules

    def _get_template_rule_details_by_type(self, template_id, rule_uuid, template_type=None):
        """Возвращает детали правила шаблона по типу (user/vendor)."""
        if self._is_vendor_template_type(template_type):
            response = self.api_client.get_vendor_template_rule_details(template_id, rule_uuid)
        else:
            response = self.api_client.get_template_rule_details(template_id, rule_uuid)
        if response and response.status_code == 200:
            return response.json()
        return None

    def _find_template_rule(self, template_id, rule_name=None, system_rule_id=None, template_type=None, template_rules_cache=None):
        """Находит правило в шаблоне по rule_id или имени."""
        template_rules = self._get_template_rules_list(
            template_id, template_type, template_rules_cache
        )
        if system_rule_id:
            for template_rule in template_rules:
                if template_rule.get('rule_id') == system_rule_id:
                    return template_rule
        if rule_name:
            for template_rule in template_rules:
                if template_rule.get('name') == rule_name:
                    return template_rule
        return None

    def _get_template_rule_actions(self, template_id, rule_name=None, system_rule_id=None, template_type=None, template_rules_cache=None):
        """Возвращает действия правила из шаблона политики."""
        template_rule = self._find_template_rule(
            template_id,
            rule_name=rule_name,
            system_rule_id=system_rule_id,
            template_type=template_type,
            template_rules_cache=template_rules_cache,
        )
        if not template_rule:
            return None
        details = self._get_template_rule_details_by_type(
            template_id, template_rule.get('id'), template_type
        )
        return self._extract_rule_actions(details)

    def _get_effective_policy_rule_actions(
        self,
        policy_id,
        rule,
        rule_details,
        is_user_rule=False,
        policy_template_id=None,
        template_rules_cache=None,
    ):
        """
        Возвращает эффективные действия правила политики.
        Список правил не содержит actions (swagger); для системных правил без оверрайда
        actions наследуются из шаблона (policy_template_id + policy_template_type).
        """
        if is_user_rule:
            return self._extract_rule_actions(rule_details, prefer_configuration=True) or []

        has_overrides = rule.get('has_overrides')
        if has_overrides is None and rule_details:
            has_overrides = rule_details.get('has_overrides')

        if has_overrides is not False and self._has_policy_actions_override(rule_details):
            return self._extract_rule_actions(rule_details) or []

        template_id = (
            rule.get('policy_template_id')
            or (rule_details or {}).get('policy_template_id')
            or policy_template_id
            or self._get_policy_template_id(policy_id)
        )
        template_type = rule.get('policy_template_type') or (rule_details or {}).get('policy_template_type')
        if not template_id:
            return self._extract_rule_actions(rule_details) or []

        inherited_actions = self._get_template_rule_actions(
            template_id,
            rule_name=rule.get('name') or (rule_details or {}).get('name'),
            system_rule_id=rule.get('rule_id') or (rule_details or {}).get('rule_id'),
            template_type=template_type,
            template_rules_cache=template_rules_cache,
        )
        if inherited_actions is not None:
            return inherited_actions
        return self._extract_rule_actions(rule_details) or []
    
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
                _print_rule_update_error(response, rule_name)
        
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
        
        policy_template_id = self._get_policy_template_id(policy_id)
        template_rules_cache = {}
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
            
            current_actions = self._get_effective_policy_rule_actions(
                policy_id, rule, rule_details, is_user_rule, policy_template_id, template_rules_cache
            )
            
            # Проверяем, есть ли уже это действие в правиле
            if syslog_action_id in current_actions:
                continue
            
            # Добавляем действие
            new_actions = current_actions + [syslog_action_id]
            
            # Обновляем только действия
            if is_user_rule:
                response = self.update_policy_user_rule_actions_only(policy_id, rule_id, new_actions, rule_details)
            else:
                response = self.update_policy_system_rule_actions_only(policy_id, rule_id, new_actions)
                
            if self._check_response(response):
                rule_type = 'пользовательское' if is_user_rule else 'системное'
                print(f"Успешно добавлено действие в правило '{rule_name}' ({rule_type})")
                total_updated += 1
            else:
                _print_rule_update_error(response, rule_name)
        
        return total_updated, total_rules
    
    def replace_actions_in_template(self, template_id, old_action_id, new_action_id, threat_filter=None):
        """Заменяет действие в указанном шаблоне политики"""
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return 0, 0

        if threat_filter is not None:
            rules = [rule for rule in rules if self._rule_matches_threat_filter(rule, threat_filter)]
            if not rules:
                print("Не найдено правил, соответствующих выбранному фильтру")
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
                _print_rule_update_error(response, rule_name)
        
        return total_replaced, total_rules
    
    def replace_actions_in_policy(self, policy_id, old_action_id, new_action_id, threat_filter=None):
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

        if threat_filter is not None:
            all_rules = [rule for rule in all_rules if self._rule_matches_threat_filter(rule, threat_filter)]
            if not all_rules:
                print("Не найдено правил, соответствующих выбранному фильтру")
                return 0, 0
        
        policy_template_id = self._get_policy_template_id(policy_id)
        template_rules_cache = {}
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
            
            current_actions = self._get_effective_policy_rule_actions(
                policy_id, rule, rule_details, is_user_rule, policy_template_id, template_rules_cache
            )
            
            # Проверяем, есть ли старое действие в правиле
            if old_action_id not in current_actions:
                continue
            
            # Заменяем действие
            new_actions = [new_action_id if action_id == old_action_id else action_id for action_id in current_actions]
            
            # Обновляем только действия
            if is_user_rule:
                response = self.update_policy_user_rule_actions_only(policy_id, rule_id, new_actions, rule_details)
            else:
                response = self.update_policy_system_rule_actions_only(policy_id, rule_id, new_actions)
                
            if self._check_response(response):
                rule_type = 'пользовательское' if is_user_rule else 'системное'
                print(f"Успешно заменено действие в правиле '{rule_name}' ({rule_type})")
                total_replaced += 1
            else:
                _print_rule_update_error(response, rule_name)
        
        return total_replaced, total_rules
    
    def remove_action_from_template(self, template_id, action_id):
        """Удаляет указанное действие из всех правил шаблона (экспериментально)."""
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не найдено правил в указанном шаблоне")
            return 0, 0
        total_updated = 0
        for rule in rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            rule_details = self.get_rule_details(template_id, rule_id)
            if not rule_details:
                continue
            current_actions = rule_details.get('actions', [])
            if action_id not in current_actions:
                continue
            new_actions = [a for a in current_actions if a != action_id]
            response = self.update_rule_actions_only(template_id, rule_id, new_actions)
            if self._check_response(response):
                print(f"Удалено действие из правила '{rule_name}'")
                total_updated += 1
            else:
                _print_rule_update_error(response, rule_name)
        return total_updated, len(rules)
    
    def remove_action_from_policy(self, policy_id, action_id):
        """Удаляет указанное действие из всех правил политики (экспериментально)."""
        system_rules = self.get_policy_system_rules(policy_id)
        user_rules = self.get_policy_user_rules(policy_id)
        all_rules = list(system_rules or []) + list(user_rules or [])
        if not all_rules:
            print("Не найдено правил в указанной политике")
            return 0, 0
        policy_template_id = self._get_policy_template_id(policy_id)
        template_rules_cache = {}
        total_updated = 0
        for rule in all_rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            is_user_rule = rule.get('is_user_rule', False)
            if is_user_rule:
                rule_details = self.get_policy_user_rule_details(policy_id, rule_id)
            else:
                rule_details = self.get_policy_system_rule_details(policy_id, rule_id)
            if not rule_details:
                continue
            current_actions = self._get_effective_policy_rule_actions(
                policy_id, rule, rule_details, is_user_rule, policy_template_id, template_rules_cache
            )
            if action_id not in current_actions:
                continue
            new_actions = [a for a in current_actions if a != action_id]
            if is_user_rule:
                response = self.update_policy_user_rule_actions_only(policy_id, rule_id, new_actions, rule_details)
            else:
                response = self.update_policy_system_rule_actions_only(policy_id, rule_id, new_actions)
            if self._check_response(response):
                rule_type = 'пользовательское' if is_user_rule else 'системное'
                print(f"Удалено действие из правила '{rule_name}' ({rule_type})")
                total_updated += 1
            else:
                _print_rule_update_error(response, rule_name)
        return total_updated, len(all_rules)
    
    # ==================== ИНТЕРАКТИВНОЕ УПРАВЛЕНИЕ ====================
    
    def manage_actions_operations(self):
        """Управление действиями в правилах — сразу выбор типа действия"""
        ACTION_TYPES = [
            None,
            {'type': 'replace', 'action_key': 'log', 'name': 'Log to DB'},
            {'type': 'replace', 'action_key': 'custom_response', 'name': 'Custom Response'},
            {'type': 'add', 'action_key': 'send_to_syslog', 'name': 'send_to_syslog'},
            {'type': 'replace', 'action_key': 'send_to_syslog', 'name': 'send_to_syslog'},
            {'type': 'add_any', 'name': 'Добавить любое действие'},
            {'type': 'replace_any', 'name': 'Замена любое на любое'},
            {'type': 'remove_any', 'name': 'Удалить любое действие'},
        ]
        while True:
            print("\n=== Управление действиями в правилах ===")
            print("1. Замена действия \"Записывать событие в базу данных\" (Log to DB)")
            print("2. Замена действия \"Отправлять свой ответ\" (Custom Response)")
            print("3. Добавить действие \"Отправить событие по протоколу Syslog\" (send_to_syslog)")
            print("4. Заменить действие \"Отправить событие по протоколу Syslog\" (send_to_syslog)")
            print("5. Добавить действие (Любое) ко всем правилам. (Экспериментальный)")
            print("6. Замена действия (Любое на любое) ко всем правилам. (Экспериментальный)")
            print("7. Удаление действия (Любое) из всех правил. (Экспериментальный)")
            print("8. Вернуться в главное меню")
            choice = input("\nВыберите действие (1-8): ").strip()
            if choice == '8':
                return
            if choice not in ('1', '2', '3', '4', '5', '6', '7'):
                print("Некорректный выбор. Попробуйте снова.")
                continue
            action_type = ACTION_TYPES[int(choice)]
            self._perform_actions_operation(action_type)
    
    def _perform_actions_operation(self, action_type):
        """Выполнение операции с действиями (тенант запрашивается после выбора типа действия)."""
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("Не удалось выбрать тенант")
            return
        if action_type['type'] in ('add_any', 'replace_any', 'remove_any'):
            action_data = self._select_actions_for_experimental(action_type)
            if not action_data:
                return
            object_type = self._select_object_type()
            if not object_type:
                return
            self._execute_experimental_operation(action_type, action_data, object_type)
            return
        action_data = self._select_specific_action(action_type)
        if not action_data:
            return
        object_type = self._select_object_type()
        if not object_type:
            return
        self._execute_operation(action_type, action_data, object_type)
    
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
    
    def _select_actions_for_experimental(self, action_type):
        """Выбор действий для экспериментальных операций (любое действие из списка)."""
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список действий")
            return None
        kind = action_type['type']
        if kind == 'add_any':
            selected = self._select_action_with_prompt(actions, "Выберите действие для добавления ко всем правилам:")
            if not selected:
                return None
            return {'new_action_id': selected['id'], 'new_action_name': selected.get('name')}
        if kind == 'remove_any':
            selected = self._select_action_with_prompt(actions, "Выберите действие для удаления из всех правил:")
            if not selected:
                return None
            return {'action_id': selected['id'], 'action_name': selected.get('name')}
        if kind == 'replace_any':
            old_action = self._select_action_with_prompt(actions, "Выберите действие для замены (исходное):")
            if not old_action:
                return None
            new_action = self._select_action_with_prompt(actions, "Выберите действие для замены (целевое):")
            if not new_action:
                return None
            if old_action['id'] == new_action['id']:
                print("Исходное и целевое действие совпадают")
                return None
            return {
                'old_action_id': old_action['id'],
                'old_action_name': old_action.get('name'),
                'new_action_id': new_action['id'],
                'new_action_name': new_action.get('name'),
            }
        return None

    def _execute_replace_any_operation(self, action_data, object_type):
        """Замена любого действия с выбором области: все правила или по threat."""
        if object_type == 'template':
            selected_object = self._select_template()
            if not selected_object:
                return
            object_label = 'шаблона'
        else:
            selected_object = self._select_policy()
            if not selected_object:
                return
            object_label = 'политики'

        object_id = selected_object['id']
        object_name = selected_object.get('name', 'Без названия')
        rules = self._get_rules_for_object(object_type, object_id)
        scope = self._select_replace_scope(rules)
        if not scope:
            return

        threat_filter = None if scope['mode'] == 'all' else scope['value']
        confirm_msg = self._build_replace_confirm_message(
            action_data, object_label, object_name, scope
        )
        if not self._confirm_action(confirm_msg):
            return

        if object_type == 'template':
            total, total_rules = self.replace_actions_in_template(
                object_id,
                action_data['old_action_id'],
                action_data['new_action_id'],
                threat_filter,
            )
        else:
            total, total_rules = self.replace_actions_in_policy(
                object_id,
                action_data['old_action_id'],
                action_data['new_action_id'],
                threat_filter,
            )
        print(f"\nИтог: заменено в {total} из {total_rules} правил")
    
    def _execute_experimental_operation(self, action_type, action_data, object_type):
        """Выполнение экспериментальных операций (любое действие)."""
        kind = action_type['type']
        if kind == 'replace_any':
            self._execute_replace_any_operation(action_data, object_type)
            return

        if object_type == 'template':
            template = self._select_template()
            if not template:
                return
            template_id = template['id']
            template_name = template.get('name', 'Без названия')
            if kind == 'add_any':
                if not self._confirm_action(f"Добавить действие '{action_data['new_action_name']}' во все правила шаблона '{template_name}'?"):
                    return
                total, total_rules = self.add_syslog_action_to_template(template_id, action_data['new_action_id'])
                print(f"\nИтог: добавлено в {total} из {total_rules} правил")
            elif kind == 'remove_any':
                if not self._confirm_action(f"Удалить действие '{action_data['action_name']}' из всех правил шаблона '{template_name}'?"):
                    return
                total, total_rules = self.remove_action_from_template(template_id, action_data['action_id'])
                print(f"\nИтог: удалено из {total} из {total_rules} правил")
        else:
            policy = self._select_policy()
            if not policy:
                return
            policy_id = policy['id']
            policy_name = policy.get('name', 'Без названия')
            if kind == 'add_any':
                if not self._confirm_action(f"Добавить действие '{action_data['new_action_name']}' во все правила политики '{policy_name}'?"):
                    return
                total, total_rules = self.add_syslog_action_to_policy(policy_id, action_data['new_action_id'])
                print(f"\nИтог: добавлено в {total} из {total_rules} правил")
            elif kind == 'remove_any':
                if not self._confirm_action(f"Удалить действие '{action_data['action_name']}' из всех правил политики '{policy_name}'?"):
                    return
                total, total_rules = self.remove_action_from_policy(policy_id, action_data['action_id'])
                print(f"\nИтог: удалено из {total} из {total_rules} правил")
    
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

    def get_actions_by_name_and_type(self, action_name, action_type_id):
        """Находит действие по имени и типу"""
        actions = self.get_available_actions()
        if not actions:
            return None
        
        for action in actions:
            if (action.get('name') == action_name and 
                action.get('type_id') == action_type_id):
                return action
        return None

    def find_or_create_action(self, action_data):
        """Находит существующее действие или создает новое"""
        action_name = action_data.get('name')
        action_type_id = action_data.get('type_id')
        
        if not action_name or not action_type_id:
            print(f"❌ Неверные данные действия: имя={action_name}, тип={action_type_id}")
            return None
        
        # Ищем существующее действие
        existing_action = self.get_actions_by_name_and_type(action_name, action_type_id)
        if existing_action:
            print(f"  ✓ Действие '{action_name}' уже существует (ID: {existing_action.get('id')})")
            return existing_action
        
        # Создаем новое действие
        print(f"  ✗ Действие '{action_name}' не найдено, создаем...")
        create_data = action_data.copy()
        
        # Удаляем системные поля
        create_data.pop('id', None)
        create_data.pop('is_system', None)
        
        response = self.api_client.create_action(create_data)
        if response and response.status_code == 201:
            new_action = response.json()
            print(f"  ✓ Действие '{action_name}' создано (ID: {new_action.get('id')})")
            return new_action
        else:
            if response is not None:
                code = getattr(response, "status_code", None)
                body = response.text if getattr(response, "text", None) else "(пусто)"
                print(f"  ✗ Ошибка при создании действия '{action_name}': HTTP {code}")
                print(f"    Тело ответа: {body}")
            else:
                print(f"  ✗ Ошибка при создании действия '{action_name}': Неизвестная ошибка (нет ответа)")
            return None

    def create_action_mapping(self, source_actions, target_tenant_id=None):
        """Создает маппинг ID действий между тенантами"""
        if target_tenant_id and target_tenant_id != self.api_client.auth_manager.tenant_id:
            original_tenant_id = self.api_client.auth_manager.tenant_id
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return {}
        
        action_mapping = {}
        
        for action in source_actions:
            original_action_id = action.get('id')
            action_name = action.get('name')
            action_type_id = action.get('type_id')
            
            # Пропускаем системные действия
            if action.get('is_system', True):
                continue
            
            # Ищем или создаем действие в целевом тенанте
            target_action = self.find_or_create_action(action)
            if target_action:
                action_mapping[original_action_id] = target_action.get('id')
        
        return action_mapping

    def copy_actions_between_tenants(self, source_tenant_id, target_tenant_id, actions_to_copy="all"):
        """Копирует действия из одного тенанта в другой"""
        print(f"\nКопирование действий из тенанта {source_tenant_id} в {target_tenant_id}")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # Получаем действия из исходного тенанта
            self.api_client.auth_manager.tenant_id = source_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"❌ Не удалось переключиться на исходный тенант {source_tenant_id}")
                return {}
            
            custom_actions = self.get_custom_actions()
            if not custom_actions:
                print("Не найдено пользовательских действий для копирования")
                return {}
            
            # Фильтруем действия по выбранному списку
            if actions_to_copy != "all":
                custom_actions = [action for action in custom_actions if action.get('name') in actions_to_copy]
            
            if not custom_actions:
                print("После фильтрации не осталось действий для копирования")
                return {}
            
            print(f"Найдено {len(custom_actions)} действий для копирования")
            
            # Создаем маппинг в целевом тенанте
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"❌ Не удалось переключиться на целевой тенант {target_tenant_id}")
                return {}
            
            action_mapping = self.create_action_mapping(custom_actions, target_tenant_id)
            
            print(f"Создано маппинг для {len(action_mapping)} действий")
            return action_mapping
            
        finally:
            # Восстанавливаем оригинальный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)