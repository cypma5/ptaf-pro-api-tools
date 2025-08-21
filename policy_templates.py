# policy_templates.py
import json
from urllib.parse import urljoin

class PolicyTemplatesManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_vendor_templates(self):
        """Получает список системных шаблонов политик"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/vendor")
        
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
            print(f"Ошибка при получении системных шаблонов. Код: {response.status_code}, Ответ: {response.text}")
            return None

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

    def create_user_template(self, name, vendor_template_ids):
        """Создает новый пользовательский шаблон политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user")
        payload = {
            "name": name,
            "has_user_rules": True,
            "templates": vendor_template_ids
        }
        
        response = self.make_request("POST", url, json=payload)
        if not response:
            return None
            
        if response.status_code == 201:
            print("Шаблон политики успешно создан")
            return response.json()
        else:
            print(f"Ошибка при создании шаблона политики. Код: {response.status_code}, Ответ: {response.text}")
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

    def get_template_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила шаблона"""
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

    def update_template_rule(self, template_id, rule_id, update_data):
        """Обновляет правило шаблона политики"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        return self.make_request("PATCH", url, json=update_data)

    def manage_policy_templates(self):
        """Интерактивное управление шаблонами политик"""
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
                    print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')}, Тип: {template.get('type')})")
            
            elif choice == '2':
                templates = self.get_user_templates()
                if not templates:
                    print("Не удалось получить список пользовательских шаблонов или список пуст")
                    continue
                
                vendor_templates = self.get_vendor_templates() or []
                vendor_templates_map = {t['id']: t.get('name', 'Без названия') for t in vendor_templates}
                
                print("\nПользовательские шаблоны политик:")
                for i, template in enumerate(templates, 1):
                    template_names = []
                    for t_id in template.get('templates', []):
                        template_names.append(vendor_templates_map.get(t_id, f"Неизвестный шаблон ({t_id})"))
                    
                    print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')}, Тип: {template.get('type')})")
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
                    print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
                
                while True:
                    choice = input(
                        "\nВыберите номер системного шаблона для включения: "
                    ).strip()
                    
                    if not choice:
                        print("Необходимо выбрать шаблон")
                        continue
                    
                    try:
                        selected_index = int(choice) - 1
                        if 0 <= selected_index < len(vendor_templates):
                            selected_template = vendor_templates[selected_index]['id']
                            break
                        else:
                            print("Некорректный номер шаблона")
                    except ValueError:
                        print("Пожалуйста, введите номер шаблона")
                
                result = self.create_user_template(name, [selected_template])
                if result:
                    print(f"Шаблон '{name}' успешно создан с ID: {result.get('id')}")
            
            elif choice == '4':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")