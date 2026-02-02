# policies_manager.py
import json
from urllib.parse import urljoin

class PoliciesManager:
    def __init__(self, api_client):
        self.api_client = api_client
    
    def get_security_policies(self):
        """Получает список политик безопасности"""
        response = self.api_client.get_policies()
        return self.api_client._parse_response_items(response)
    
    def get_policy_details(self, policy_id):
        """Получает детали политики"""
        response = self.api_client.get_policy_details(policy_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def create_policy_from_template(self, name, template_id):
        """Создает политику на основе шаблона"""
        payload = {
            "name": name,
            "template_id": template_id
        }
        response = self.api_client.create_policy(payload)
        if response and response.status_code == 201:
            return response.json()
        return None
    
    def get_policy_system_rules(self, policy_id):
        """Получает системные правила политики"""
        response = self.api_client.get_policy_system_rules(policy_id)
        rules = self.api_client._parse_response_items(response)
        
        # Помечаем системные правила
        if rules:
            for rule in rules:
                rule['is_user_rule'] = False
        return rules
    
    def get_policy_user_rules(self, policy_id):
        """Получает пользовательские правила политики"""
        response = self.api_client.get_policy_user_rules(policy_id)
        rules = self.api_client._parse_response_items(response)
        
        # Помечаем пользовательские правила
        if rules:
            for rule in rules:
                rule['is_user_rule'] = True
        return rules
    
    def get_all_policy_rules(self, policy_id):
        """Получает все правила политики (системные + пользовательские)"""
        system_rules = self.get_policy_system_rules(policy_id) or []
        user_rules = self.get_policy_user_rules(policy_id) or []
        return system_rules + user_rules
    
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
    
    def add_syslog_action_to_policy(self, policy_id, syslog_action_id):
        """Добавляет действие send_to_syslog в правила политики"""
        all_rules = self.get_all_policy_rules(policy_id)
        
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
                
            if response and response.status_code == 200:
                print(f"Успешно добавлено действие в правило '{rule_name}' ({'пользовательское' if is_user_rule else 'системное'})")
                total_updated += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        return total_updated, total_rules
    
    def replace_actions_in_policy(self, policy_id, old_action_id, new_action_id):
        """Заменяет действие в указанной политике веб приложения"""
        all_rules = self.get_all_policy_rules(policy_id)
        
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
                
            if response and response.status_code == 200:
                print(f"Успешно заменено действие в правиле '{rule_name}' ({'пользовательское' if is_user_rule else 'системное'})")
                total_replaced += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при обновлении правила '{rule_name}': {error_msg}")
        
        return total_replaced, total_rules
    
    def _select_policy_interactive(self):
        """Интерактивный выбор политики"""
        policies = self.get_security_policies()
        if not policies:
            print("Не найдено политик безопасности")
            return None
        
        print("\nДоступные политики безопасности:")
        for i, policy in enumerate(policies, 1):
            print(f"{i}. {policy.get('name', 'Без названия')} (ID: {policy.get('id')})")
        
        while True:
            try:
                choice = input("\nВыберите номер политики (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(policies):
                    return policies[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")