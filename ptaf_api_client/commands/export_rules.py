import os
import json
from typing import List, Optional
from ..base import BaseCommand
from ...models import Tenant

class ExportRulesCommand(BaseCommand):
    def __init__(self, config, http_client, auth_manager):
        super().__init__(config, http_client, auth_manager)
        self.exported_files = []
    
    def get_policy_template_id(self) -> Optional[str]:
        """Получает ID первого доступного шаблона политики"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/with_user_rules"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            templates = response.json()
            items = templates.get('items', []) if isinstance(templates, dict) else templates
            
            if items:
                return items[0].get('id')
        
        return None
    
    def get_existing_rules(self, template_id: str) -> Optional[List[dict]]:
        """Получает список существующих правил для шаблона"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/with_user_rules/{template_id}/rules"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            rules = response.json()
            return rules.get('items', []) if isinstance(rules, dict) else rules
        
        return None
    
    def export_single_rule(self, template_id: str, rule: dict, export_dir: str) -> bool:
        """Экспортирует одно правило в файл"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'unnamed_rule')
        
        # Получаем детали правила
        url = f"{self.config.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}"
        response = self.http_client.get(url)
        
        if not response or response.status_code != 200:
            print(f"Не удалось получить детали правила {rule_name}")
            return False
        
        rule_details = response.json()
        
        # Удаляем ID из экспортируемых данных
        if 'id' in rule_details:
            del rule_details['id']
        
        # Формируем имя файла
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in rule_name)
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.ptafpro"
        filepath = os.path.join(export_dir, filename)
        
        # Сохраняем правило в файл
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule_details, f, ensure_ascii=False, indent=2)
            print(f"Правило '{rule_name}' экспортировано в {filepath}")
            self.exported_files.append(filepath)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении правила '{rule_name}': {e}")
            return False
    
    def execute(self, export_dir: str = "exported_rules", tenant: Optional[Tenant] = None):
        """Основной метод экспорта правил"""
        if tenant:
            if not self.auth_manager.update_jwt_with_tenant(tenant.id):
                print(f"Не удалось переключиться на тенанта {tenant.name}")
                return False
        else:
            tenant = self.select_tenant_interactive()
            if not tenant:
                return False
        
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print("Не удалось получить ID шаблона политики")
            return False
        
        # Получаем список всех правил
        rules = self.get_existing_rules(template_id)
        if not rules:
            print("Не удалось получить список правил")
            return False
        
        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]
        
        if not user_rules:
            print("Нет пользовательских правил для экспорта")
            return False
        
        # Создаем директорию для экспорта
        tenant_dir = os.path.join(export_dir, tenant.name.replace(' ', '_'))
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Экспортируем все правила
        success_count = 0
        for rule in user_rules:
            if self.export_single_rule(template_id, rule, tenant_dir):
                success_count += 1
        
        print(f"\nЭкспортировано {success_count} из {len(user_rules)} правил")
        return success_count > 0