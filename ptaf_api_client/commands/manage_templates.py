from typing import Optional, List
from ..base import BaseCommand
from ...models import Tenant, PolicyTemplate

class ManageTemplatesCommand(BaseCommand):
    def get_vendor_templates(self) -> Optional[List[PolicyTemplate]]:
        """Получает список системных шаблонов политик"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/vendor"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            templates_data = response.json()
            items = templates_data.get('items', []) if isinstance(templates_data, dict) else templates_data
            
            templates = []
            for template_data in items:
                templates.append(PolicyTemplate(
                    id=template_data.get('id'),
                    name=template_data.get('name', 'Без названия'),
                    type=template_data.get('type', 'unknown'),
                    has_user_rules=template_data.get('has_user_rules', False),
                    templates=template_data.get('templates', [])
                ))
            
            return templates
        
        return None
    
    def get_user_templates(self) -> Optional[List[PolicyTemplate]]:
        """Получает список пользовательских шаблонов политик"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/user"
        response = self.http_client.get(url)
        
        if response and response.status_code == 200:
            templates_data = response.json()
            items = templates_data.get('items', []) if isinstance(templates_data, dict) else templates_data
            
            templates = []
            for template_data in items:
                templates.append(PolicyTemplate(
                    id=template_data.get('id'),
                    name=template_data.get('name', 'Без названия'),
                    type=template_data.get('type', 'unknown'),
                    has_user_rules=template_data.get('has_user_rules', False),
                    templates=template_data.get('templates', [])
                ))
            
            return templates
        
        return None
    
    def create_user_template(self, name: str, vendor_template_ids: List[str]) -> Optional[PolicyTemplate]:
        """Создает новый пользовательский шаблон политики"""
        if not self.ensure_auth():
            return None
        
        url = f"{self.config.api_path}/config/policies/templates/user"
        payload = {
            "name": name,
            "has_user_rules": True,
            "templates": vendor_template_ids
        }
        
        response = self.http_client.post(url, json=payload)
        if response and response.status_code == 201:
            template_data = response.json()
            return PolicyTemplate(
                id=template_data.get('id'),
                name=template_data.get('name'),
                type=template_data.get('type', 'user'),
                has_user_rules=template_data.get('has_user_rules', True),
                templates=template_data.get('templates', [])
            )
        
        return None
    
    def execute(self, tenant: Optional[Tenant] = None):
        """Основной метод управления шаблонами"""
        if tenant:
            if not self.auth_manager.update_jwt_with_tenant(tenant.id):
                print(f"Не удалось переключиться на тенанта {tenant.name}")
                return False
        else:
            tenant = self.select_tenant_interactive()
            if not tenant:
                return False
        
        while True:
            print("\nУправление шаблонами политик:")
            print("1. Показать список системных шаблонов")
            print("2. Показать список пользовательских шаблонов")
            print("3. Создать новый шаблон политики")
            print("4. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == '1':
                templates = self.get_vendor_templates()
                if not templates:
                    print("Не удалось получить список системных шаблонов или список пуст")
                    continue
                
                print("\nСистемные шаблоны политик:")
                for i, template in enumerate(templates, 1):
                    print(f"{i}. {template.name} (ID: {template.id}, Тип: {template.type})")
            
            elif choice == '2':
                templates = self.get_user_templates()
                if not templates:
                    print("Не удалось получить список пользовательских шаблонов или список пуст")
                    continue
                
                vendor_templates = self.get_vendor_templates() or []
                vendor_templates_map = {t.id: t.name for t in vendor_templates}
                
                print("\nПользовательские шаблоны политик:")
                for i, template in enumerate(templates, 1):
                    template_names = []
                    for t_id in template.templates:
                        template_names.append(vendor_templates_map.get(t_id, f"Неизвестный шаблон ({t_id})"))
                    
                    print(f"{i}. {template.name} (ID: {template.id}, Тип: {template.type})")
                    print(f"   Основан на: {', '.join(template_names)}")
            
            elif choice == '3':
                print("\nСоздание нового шаблона политики")
                
                vendor_templates = self.get_vendor_templates()
                if not vendor_templates:
                    print("Не удалось получить список системных шаблонов для создания")
                    continue
                
                name = input("Введите имя нового шаблона: ").strip()
                if not name:
                    print("Имя шаблона не может быть пустым")
                    continue
                
                print("\nДоступные системные шаблоны:")
                for i, template in enumerate(vendor_templates, 1):
                    print(f"{i}. {template.name} (ID: {template.id})")
                
                while True:
                    choice = input("\nВыберите номер системного шаблона для включения: ").strip()
                    
                    if not choice:
                        print("Необходимо выбрать шаблон")
                        continue
                    
                    try:
                        selected_index = int(choice) - 1
                        if 0 <= selected_index < len(vendor_templates):
                            selected_template_id = vendor_templates[selected_index].id
                            break
                        else:
                            print("Некорректный номер шаблона")
                    except ValueError:
                        print("Пожалуйста, введите номер шаблона")
                
                result = self.create_user_template(name, [selected_template_id])
                if result:
                    print(f"Шаблон '{result.name}' успешно создан с ID: {result.id}")
                else:
                    print("Не удалось создать шаблон")
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")