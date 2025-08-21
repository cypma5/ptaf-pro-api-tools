from typing import Optional
from ..base import BaseCommand
from ...models import Tenant

class DeleteRulesCommand(BaseCommand):
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
    
    def get_existing_rules(self, template_id: str) -> Optional[list]:
        """Получает список существующих правил для шаблона"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/with_user_rules/{template_id}/rules"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            rules = response.json()
            return rules.get('items', []) if isinstance(rules, dict) else rules
        
        return None
    
    def delete_rule(self, template_id: str, rule_id: str) -> bool:
        """Удаляет правило"""
        url = f"{self.config.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}"
        response = self.http_client.delete(url)
        return response is not None and response.status_code == 204
    
    def execute(self, tenant: Optional[Tenant] = None):
        """Основной метод удаления правил"""
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

        print(f"\nИспользуется шаблон политики с ID: {template_id}")

        # Получаем список всех правил
        rules = self.get_existing_rules(template_id)
        if rules is None:
            return False

        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]

        if not user_rules:
            print("Нет пользовательских правил для удаления")
            return False

        # Подтверждение от пользователя
        print("\nВНИМАНИЕ: Будут удалены следующие правила:")
        for rule in user_rules:
            print(f"- {rule.get('name', 'Без названия')} (ID: {rule.get('id', 'Без ID')})")

        confirm = input(f"\nВы уверены, что хотите удалить {len(user_rules)} правил? (y/n): ").lower()
        if confirm != 'y':
            print("Удаление отменено")
            return False

        # Удаляем правила
        deleted_count = 0
        for rule in user_rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            
            if not rule_id:
                print(f"Правило '{rule_name}' не имеет ID, пропускаем")
                continue

            if self.delete_rule(template_id, rule_id):
                print(f"Правило '{rule_name}' успешно удалено")
                deleted_count += 1
            else:
                print(f"Ошибка при удалении правила '{rule_name}'")

        print(f"\nУдалено {deleted_count} из {len(user_rules)} правил")
        return deleted_count > 0