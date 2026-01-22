import os
import json
import datetime
from urllib.parse import urljoin

class PolicyTemplateManager:
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
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при получении шаблонов, обновляем токен...")
            if self._handle_404_error():
                return self.get_user_templates()
            return None
        else:
            print(f"Ошибка при получении пользовательских шаблонов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_template_details(self, template_id):
        """Получает детали шаблона политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при получении деталей шаблона, обновляем токен...")
            if self._handle_404_error():
                return self.get_template_details(template_id)
            return None
        else:
            print(f"Ошибка при получении деталей шаблона. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_template_rules(self, template_id):
        """Получает список правил шаблона политики"""
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
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при получении правил шаблона, обновляем токен...")
            if self._handle_404_error():
                return self.get_template_rules(template_id)
            return None
        else:
            print(f"Ошибка при получении правил шаблона. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила шаблона"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"⚠️ Ошибка 404 при получении деталей правила {rule_id}, обновляем токен...")
            if self._handle_404_error():
                return self.get_rule_details(template_id, rule_id)
            return None
        else:
            print(f"Ошибка при получении деталей правила. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_rule_aggregation(self, template_id, rule_id):
        """Получает настройки агрегации правила"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"⚠️ Ошибка 404 при получении агрегации правила {rule_id}, обновляем токен...")
            if self._handle_404_error():
                return self.get_rule_aggregation(template_id, rule_id)
            return None
        else:
            print(f"Ошибка при получении настроек агрегации. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def create_template(self, name, vendor_template_ids, has_user_rules=False):
        """Создает новый шаблон политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user")
        
        payload = {
            "name": name,
            "has_user_rules": has_user_rules,
            "templates": vendor_template_ids
        }
        
        response = self.make_request("POST", url, json=payload)
        if not response:
            return None
            
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при создании шаблона, обновляем токен...")
            if self._handle_404_error():
                return self.create_template(name, vendor_template_ids, has_user_rules)
            return None
        else:
            print(f"Ошибка при создании шаблона. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет правило шаблона"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self.make_request("PATCH", url, json=update_data)
        if not response:
            return None
        
        if response.status_code == 404:
            print(f"⚠️ Ошибка 404 при обновлении правила {rule_id}, обновляем токен...")
            if self._handle_404_error():
                return self.update_rule(template_id, rule_id, update_data)
            return response
        
        return response

    def update_rule_aggregation(self, template_id, rule_id, aggregation_data):
        """Обновляет настройки агрегации правила"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation")
        
        response = self.make_request("PATCH", url, json=aggregation_data)
        if not response:
            return None
        
        if response.status_code == 404:
            print(f"⚠️ Ошибка 404 при обновлении агрегации правила {rule_id}, обновляем токен...")
            if self._handle_404_error():
                return self.update_rule_aggregation(template_id, rule_id, aggregation_data)
            return response
        
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
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при получении действий, обновляем токен...")
            if self._handle_404_error():
                return self.get_available_actions()
            return None
        else:
            print(f"Ошибка при получении списка действий. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_available_lists(self):
        """Получает список доступных списков (для агрегации)"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/lists")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            lists = response.json()
            if isinstance(lists, dict) and 'items' in lists:
                return lists['items']
            elif isinstance(lists, list):
                return lists
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(lists)}")
                return None
        elif response.status_code == 404:
            print("⚠️ Ошибка 404 при получении списков, обновляем токен...")
            if self._handle_404_error():
                return self.get_available_lists()
            return None
        else:
            print(f"Ошибка при получении списков. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def _handle_404_error(self):
        """Обрабатывает ошибку 404 - обновляет токен"""
        print("Обновляем токен для текущего тенанта...")
        
        # Сохраняем текущий тенант
        current_tenant_id = self.auth_manager.tenant_id
        
        # Получаем новые токены
        if not self.auth_manager.get_jwt_tokens(self.make_request):
            print("❌ Не удалось получить новые JWT токены")
            return False
        
        # Обновляем токен для текущего тенанта
        if current_tenant_id:
            self.auth_manager.tenant_id = current_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print("❌ Не удалось обновить токен для тенанта")
                return False
        
        print("✅ Токен успешно обновлен")
        return True

    def _get_filtered_rules_with_details(self, template_id):
        """Получает только измененные правила с полными деталями"""
        print("Получение правил шаблона...")
        rules = self.get_template_rules(template_id)
        if rules is None:
            return []
        
        # Фильтруем только измененные правила (has_overrides: true)
        modified_rules = []
        for rule in rules:
            if rule.get('has_overrides') == True:
                modified_rules.append(rule)
        
        print(f"Найдено {len(modified_rules)} измененных правил из {len(rules)} всего")
        
        # Получаем полные детали для измененных правил
        full_rules_data = []
        for i, rule in enumerate(modified_rules, 1):
            rule_id = rule.get('id')
            rule_name = rule.get('name', f'Правило {i}')
            
            print(f"  [{i}/{len(modified_rules)}] Получение деталей: {rule_name}")
            
            rule_details = self.get_rule_details(template_id, rule_id)
            if rule_details:
                # Получаем настройки агрегации для правила
                aggregation_data = self.get_rule_aggregation(template_id, rule_id)
                if aggregation_data:
                    rule_details['aggregation'] = aggregation_data
                full_rules_data.append(rule_details)
        
        return full_rules_data

    def export_template(self, template_id, export_dir="templates_export"):
        """Экспортирует шаблон политики со всеми измененными правилами и связанными объектами"""
        print(f"\nЭкспорт шаблона политики ID: {template_id}")
        
        # Получаем детали шаблона
        template_details = self.get_template_details(template_id)
        if not template_details:
            print("Не удалось получить детали шаблона")
            return None
        
        # Получаем только измененные правила с деталями
        modified_rules_data = self._get_filtered_rules_with_details(template_id)
        
        if not modified_rules_data:
            print("⚠️ В шаблоне нет измененных правил (has_overrides: true)")
            print("Экспортируется только информация о шаблоне")
        
        # Собираем все ID действий из измененных правил
        action_ids = set()
        # Собираем все ID глобальных списков из правил
        global_list_ids = set()
        
        for rule_data in modified_rules_data:
            # Действия
            if 'actions' in rule_data and rule_data['actions']:
                action_ids.update(rule_data['actions'])
            
            # Глобальные списки из variables
            if 'variables' in rule_data and rule_data['variables']:
                variables = rule_data['variables']
                if 'dynamic_global_lists' in variables:
                    dgl = variables['dynamic_global_lists']
                    if 'value' in dgl and isinstance(dgl['value'], list):
                        global_list_ids.update(dgl['value'])
            
            # Глобальные списки из агрегации
            if 'aggregation' in rule_data and rule_data['aggregation']:
                global_list_id = rule_data['aggregation'].get('global_list_id')
                if global_list_id:
                    global_list_ids.add(global_list_id)
        
        # Получаем связанные действия
        related_actions = []
        if action_ids:
            print(f"Получение связанных действий ({len(action_ids)})...")
            all_actions = self.get_available_actions()
            if all_actions:
                related_actions = [action for action in all_actions if action.get('id') in action_ids]
                print(f"Найдено {len(related_actions)} действий")
        
        # Получаем связанные глобальные списки
        related_global_lists = []
        if global_list_ids:
            print(f"Получение связанных глобальных списков ({len(global_list_ids)})...")
            # Используем новый менеджер глобальных списков
            from global_lists_manager import GlobalListsManager
            lists_manager = GlobalListsManager(self.auth_manager, self.make_request)
            all_lists = lists_manager.get_global_lists()
            
            if all_lists:
                # Фильтруем только списки из нашего набора ID
                filtered_lists = [lst for lst in all_lists if lst.get('id') in global_list_ids]
                
                # Получаем полные детали для каждого списка
                for lst in filtered_lists:
                    list_id = lst.get('id')
                    list_details = lists_manager.get_global_list_details(list_id)
                    if list_details:
                        related_global_lists.append(list_details)
                
                print(f"Найдено {len(related_global_lists)} глобальных списков")
        
        # Формируем полный экспорт
        export_data = {
            "template": template_details,
            "modified_rules": modified_rules_data,
            "related_actions": related_actions,
            "related_global_lists": related_global_lists,  # Новое поле вместо related_lists
            "export_info": {
                "export_time": datetime.datetime.now().isoformat(),
                "tenant_id": self.auth_manager.tenant_id,
                "api_path": self.auth_manager.api_path,
                "base_url": self.auth_manager.base_url,
                "export_type": "modified_rules_only",
                "rules_count": len(modified_rules_data),
                "actions_count": len(related_actions),
                "global_lists_count": len(related_global_lists)
            }
        }
        
        # Создаем директорию для экспорта
        os.makedirs(export_dir, exist_ok=True)
        
        # Формируем имя файла
        template_name = template_details.get('name', 'unnamed_template')
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in template_name)
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{safe_name}_{timestamp}.template.json"
        filepath = os.path.join(export_dir, filename)
        
        # Сохраняем в файл
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Шаблон успешно экспортирован в файл: {filepath}")
            print(f"📊 Экспортировано:")
            print(f"  - Измененных правил: {len(modified_rules_data)}")
            print(f"  - Связанных действий: {len(related_actions)}")
            print(f"  - Связанных глобальных списков: {len(related_global_lists)}")
            return filepath
        except Exception as e:
            print(f"❌ Ошибка при сохранении шаблона: {e}")
            return None

    def import_template(self, file_path, target_tenant_id=None):
        """Импортирует шаблон политики из JSON файла, обновляя только измененные правила"""
        print(f"\nИмпорт шаблона из файла: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка при чтении файла: {e}")
            return False
        
        # Проверяем структуру данных
        if 'template' not in import_data:
            print("❌ Некорректный формат файла: отсутствует секция 'template'")
            return False
        
        template_data = import_data['template']
        # Используем modified_rules вместо rules
        modified_rules_data = import_data.get('modified_rules', [])
        related_actions = import_data.get('related_actions', [])
        related_global_lists = import_data.get('related_global_lists', [])  # Новое поле вместо related_lists
        
        # Проверяем тип экспорта
        export_info = import_data.get('export_info', {})
        export_type = export_info.get('export_type', 'full')
        
        if export_type == 'modified_rules_only':
            print("📋 Тип экспорта: только измененные правила")
        else:
            print(f"⚠️ Тип экспорта: {export_type} (ожидается 'modified_rules_only')")
        
        print(f"📊 Данные для импорта:")
        print(f"  - Измененных правил: {len(modified_rules_data)}")
        print(f"  - Связанных действий: {len(related_actions)}")
        print(f"  - Связанных глобальных списков: {len(related_global_lists)}")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.auth_manager.tenant_id
        
        # Если указан целевой тенант, переключаемся на него
        if target_tenant_id and target_tenant_id != original_tenant_id:
            print(f"\n🔀 Переключаемся на тенант: {target_tenant_id}")
            self.auth_manager.tenant_id = target_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return False
        
        try:
            # Шаг 1: Импортируем глобальные списки (если есть)
            print("\n1. Импортируем глобальные списки...")
            global_list_mapping = {}
            
            if related_global_lists:
                # Создаем временный файл для импорта глобальных списков
                temp_lists_file = os.path.join(os.path.dirname(file_path), "temp_global_lists.json")
                try:
                    lists_export_data = {
                        "global_lists": related_global_lists,
                        "export_info": export_info
                    }
                    
                    with open(temp_lists_file, 'w', encoding='utf-8') as f:
                        json.dump(lists_export_data, f, ensure_ascii=False, indent=2)
                    
                    from global_lists_manager import GlobalListsManager
                    lists_manager = GlobalListsManager(self.auth_manager, self.make_request)
                    
                    # Импортируем списки
                    import_result = lists_manager.import_global_lists(temp_lists_file, target_tenant_id)
                    
                    if isinstance(import_result, dict):
                        global_list_mapping = import_result
                        print(f"  ✓ Импортировано глобальных списков: {len(global_list_mapping)}")
                    else:
                        print("  ⚠️ Не удалось получить маппинг глобальных списков")
                
                except Exception as e:
                    print(f"  ⚠️ Ошибка при импорте глобальных списков: {e}")
                finally:
                    # Удаляем временный файл
                    try:
                        os.remove(temp_lists_file)
                    except:
                        pass
            else:
                print("  ℹ️ Нет глобальных списков для импорта")
            
            # Шаг 2: Проверяем и создаем связанные действия
            print("\n2. Проверяем и создаем связанные действия...")
            action_mapping = {}  # Маппинг ID действий из исходного в целевой
            
            for action in related_actions:
                original_action_id = action.get('id')
                action_name = action.get('name')
                action_type_id = action.get('type_id')
                
                # Проверяем, существует ли такое действие в целевом тенанте
                existing_actions = self.get_available_actions()
                existing_action = None
                
                if existing_actions:
                    for existing in existing_actions:
                        if (existing.get('name') == action_name and 
                            existing.get('type_id') == action_type_id):
                            existing_action = existing
                            break
                
                if existing_action:
                    print(f"  ✓ Действие '{action_name}' уже существует (ID: {existing_action.get('id')})")
                    action_mapping[original_action_id] = existing_action.get('id')
                else:
                    # Создаем новое действие
                    # Удаляем ID при создании
                    action_data = action.copy()
                    if 'id' in action_data:
                        del action_data['id']
                    
                    # Создаем действие
                    from actions_backup_manager import ActionsBackupManager
                    actions_manager = ActionsBackupManager(self.auth_manager, self.make_request)
                    response = actions_manager.create_custom_action(action_data)
                    
                    if response and response.status_code == 201:
                        new_action = response.json()
                        new_action_id = new_action.get('id')
                        action_mapping[original_action_id] = new_action_id
                        print(f"  ✓ Действие '{action_name}' создано (ID: {new_action_id})")
                    else:
                        error_msg = response.text if response else "Неизвестная ошибка"
                        print(f"  ✗ Ошибка при создании действия '{action_name}': {error_msg}")
                        # Можно продолжить без этого действия
            
            # Шаг 3: Проверяем/создаем шаблон политики
            print("\n3. Проверяем шаблон политики...")
            template_name = template_data.get('name')
            
            # Проверяем, не существует ли уже шаблон с таким именем
            existing_templates = self.get_user_templates()
            existing_template = None
            
            if existing_templates:
                for existing in existing_templates:
                    if existing.get('name') == template_name:
                        existing_template = existing
                        break
            
            if existing_template:
                print(f"  ✓ Шаблон '{template_name}' уже существует (ID: {existing_template.get('id')})")
                target_template_id = existing_template.get('id')
            else:
                # Создаем новый шаблон
                create_data = {
                    "name": template_data.get('name'),
                    "has_user_rules": template_data.get('has_user_rules', False),
                    "templates": template_data.get('templates', [])
                }
                
                new_template = self.create_template(
                    create_data['name'],
                    create_data['templates'],
                    create_data['has_user_rules']
                )
                
                if not new_template:
                    print(f"  ✗ Ошибка при создании шаблона '{template_name}'")
                    return False
                
                target_template_id = new_template.get('id')
                print(f"  ✓ Шаблон '{template_name}' создан (ID: {target_template_id})")
            
            # Шаг 4: Импортируем только измененные правила
            print(f"\n4. Импортируем измененные правила (всего: {len(modified_rules_data)})...")
            
            if not modified_rules_data:
                print("  ⚠️ Нет измененных правил для импорта")
                print(f"\n✅ Импорт завершен! (только шаблон)")
                print(f"Шаблон: '{template_name}' (ID: {target_template_id})")
                return True
            
            imported_rules = 0
            failed_rules = 0
            
            for i, rule_data in enumerate(modified_rules_data, 1):
                rule_name = rule_data.get('name', f'Правило {i}')
                original_rule_id = rule_data.get('id')
                
                print(f"\n  [{i}/{len(modified_rules_data)}] Правило: {rule_name}")
                
                # Проверяем, что правило действительно измененное
                if not rule_data.get('has_overrides', False):
                    print(f"    ⚠️ Правило не помечено как измененное (has_overrides: false), пропускаем")
                    continue
                
                # Ищем правило в целевом шаблоне
                target_rules = self.get_template_rules(target_template_id)
                target_rule = None
                
                if target_rules:
                    # Ищем по rule_id (уникальный идентификатор правила)
                    rule_identifier = rule_data.get('rule_id')
                    if rule_identifier:
                        for rule in target_rules:
                            if rule.get('rule_id') == rule_identifier:
                                target_rule = rule
                                break
                
                if not target_rule:
                    print(f"    ⚠️ Правило не найдено в целевом шаблоне, пропускаем")
                    failed_rules += 1
                    continue
                
                target_rule_id = target_rule.get('id')
                
                # Подготавливаем данные для обновления
                update_data = {}
                
                # 1. Обновляем actions с учетом маппинга
                original_actions = rule_data.get('actions', [])
                if original_actions:
                    mapped_actions = []
                    for action_id in original_actions:
                        if action_id in action_mapping:
                            mapped_actions.append(action_mapping[action_id])
                        else:
                            # Если действия нет в маппинге, оставляем оригинальный ID
                            # (может быть системным действием)
                            mapped_actions.append(action_id)
                    
                    update_data['actions'] = mapped_actions
                
                # 2. Обновляем enabled статус
                if 'enabled' in rule_data:
                    update_data['enabled'] = rule_data['enabled']
                
                # 3. Обновляем variables если есть
                if 'variables' in rule_data and rule_data['variables']:
                    # Копируем variables
                    variables_data = rule_data['variables'].copy()
                    
                    # Обрабатываем dynamic_global_lists если есть
                    if 'dynamic_global_lists' in variables_data:
                        dgl = variables_data['dynamic_global_lists']
                        if 'value' in dgl and isinstance(dgl['value'], list):
                            # Маппим ID глобальных списков в value
                            mapped_values = []
                            for list_id in dgl['value']:
                                if list_id in global_list_mapping:
                                    mapped_values.append(global_list_mapping[list_id])
                                else:
                                    # Если списка нет в маппинге, возможно это системный список
                                    # Оставляем оригинальный ID
                                    mapped_values.append(list_id)
                            dgl['value'] = mapped_values
                    
                    update_data['variables'] = variables_data
                
                if not update_data:
                    print(f"    ⚠️ Нет данных для обновления, пропускаем")
                    failed_rules += 1
                    continue
                
                # Обновляем правило
                print(f"    Обновление правила...")
                response = self.update_rule(target_template_id, target_rule_id, update_data)
                
                if response and response.status_code == 200:
                    print(f"    ✓ Правило успешно обновлено")
                    
                    # 4. Обновляем настройки агрегации если есть
                    if 'aggregation' in rule_data and rule_data['aggregation']:
                        aggregation_data = rule_data['aggregation'].copy()
                        
                        # Обновляем global_list_id с учетом маппинга
                        original_list_id = aggregation_data.get('global_list_id')
                        if original_list_id and original_list_id in global_list_mapping:
                            aggregation_data['global_list_id'] = global_list_mapping[original_list_id]
                        
                        print(f"    Обновление настроек агрегации...")
                        agg_response = self.update_rule_aggregation(target_template_id, target_rule_id, aggregation_data)
                        
                        if agg_response and agg_response.status_code == 200:
                            print(f"    ✓ Настройки агрегации обновлены")
                        else:
                            error_msg = agg_response.text if agg_response else "Неизвестная ошибка"
                            print(f"    ⚠️ Ошибка при обновлении агрегации: {error_msg}")
                    
                    imported_rules += 1
                else:
                    error_msg = response.text if response else "Неизвестная ошибка"
                    print(f"    ✗ Ошибка при обновлении правила: {error_msg}")
                    failed_rules += 1
            
            print(f"\n✅ Импорт завершен!")
            print(f"📊 Результаты:")
            print(f"  - Успешно импортировано правил: {imported_rules}")
            print(f"  - Не удалось импортировать: {failed_rules}")
            print(f"  - Всего обработано: {len(modified_rules_data)}")
            print(f"  - Создано/использовано действий: {len(action_mapping)}")
            print(f"  - Создано/использовано глобальных списков: {len(global_list_mapping)}")
            print(f"  - Шаблон: '{template_name}' (ID: {target_template_id})")
            
            return imported_rules > 0
            
        finally:
            # Восстанавливаем исходный тенант
            if original_tenant_id:
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)

    def copy_template_to_another_tenant(self, source_template_id, target_tenant_id):
        """Копирует шаблон в другой тенант"""
        print(f"\nКопирование шаблона в другой тенант...")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.auth_manager.tenant_id
        
        try:
            # Переключаемся на исходный тенант для экспорта
            self.auth_manager.tenant_id = original_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print("❌ Не удалось переключиться на исходный тенант")
                return False
            
            # Сначала экспортируем шаблон
            export_dir = "temp_export"
            os.makedirs(export_dir, exist_ok=True)  # Создаем директорию, если не существует
            
            export_file = self.export_template(source_template_id, export_dir)
            
            if not export_file:
                print("❌ Не удалось экспортировать шаблон для копирования")
                return False
            
            # Затем импортируем в целевой тенант
            result = self.import_template(export_file, target_tenant_id)
            
            # Удаляем временный файл
            try:
                os.remove(export_file)
                # Пытаемся удалить директорию, если она пуста
                if os.path.exists(export_dir) and not os.listdir(export_dir):
                    os.rmdir(export_dir)
            except Exception as e:
                print(f"⚠️ Не удалось удалить временные файлы: {e}")
            
            return result
            
        finally:
            # Восстанавливаем исходный тенант
            if original_tenant_id:
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)

    def _select_template_interactive(self):
        """Интерактивный выбор шаблона"""
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено пользовательских шаблонов политик")
            return None
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        while True:
            try:
                choice = input("\nВыберите номер шаблона (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    return templates[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")

    def _select_tenant_interactive(self):
        """Интерактивный выбор тенанта"""
        from snapshot_manager import SnapshotManager
        snapshot_manager = SnapshotManager(self.auth_manager, self.make_request)
        tenants = snapshot_manager.get_available_tenants()
        
        if not tenants:
            print("Не удалось получить список тенантов")
            return None
        
        print("\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(tenants):
                    return tenants[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")

    def manage_policy_templates_extended(self):
        """Расширенное управление шаблонами политик"""
        while True:
            print("\n=== УПРАВЛЕНИЕ ШАБЛОНАМИ ПОЛИТИК БЕЗОПАСНОСТИ ===")
            print("1. Выгрузить шаблон политики безопасности (JSON со всеми объектами)")
            print("2. Копировать шаблон в другой тенант")
            print("3. Загрузить шаблон из JSON файла")
            print("4. Показать список шаблонов")
            print("5. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-5): ")
            
            if choice == '1':
                # Экспорт шаблона
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                
                template = self._select_template_interactive()
                if not template:
                    continue
                
                template_id = template.get('id')
                template_name = template.get('name', 'Без названия')
                
                export_dir = input(f"Введите путь для экспорта [templates_export]: ").strip()
                if not export_dir:
                    export_dir = "templates_export"
                
                print(f"\nЭкспорт шаблона '{template_name}'...")
                export_file = self.export_template(template_id, export_dir)
                
                if export_file:
                    print(f"✅ Шаблон успешно экспортирован: {export_file}")
            
            elif choice == '2':
                # Копирование шаблона в другой тенант
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                
                # Выбор шаблона для копирования
                print("\nВыберите шаблон для копирования:")
                template = self._select_template_interactive()
                if not template:
                    continue
                
                template_id = template.get('id')
                template_name = template.get('name', 'Без названия')
                
                # Выбор целевого тенанта
                print("\nВыберите целевой тенант:")
                target_tenant = self._select_tenant_interactive()
                if not target_tenant:
                    continue
                
                target_tenant_id = target_tenant.get('id')
                target_tenant_name = target_tenant.get('name', 'Без названия')
                
                if target_tenant_id == self.auth_manager.tenant_id:
                    print("Исходный и целевой тенанты совпадают")
                    continue
                
                # Подтверждение
                confirm = input(f"\nВы уверены, что хотите скопировать шаблон '{template_name}' в тенант '{target_tenant_name}'? (y/n): ").lower()
                if confirm != 'y':
                    print("Копирование отменено")
                    continue
                
                # Выполнение копирования
                print(f"\nКопирование шаблона '{template_name}' в тенант '{target_tenant_name}'...")
                result = self.copy_template_to_another_tenant(template_id, target_tenant_id)
                
                if result:
                    print("✅ Копирование завершено успешно!")
                else:
                    print("❌ Копирование не удалось")
            
            elif choice == '3':
                # Импорт шаблона из JSON
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                
                file_path = input("Введите путь к JSON файлу шаблона: ").strip()
                if not file_path or not os.path.exists(file_path):
                    print("Файл не найден")
                    continue
                
                # Спросить, импортировать в текущий или другой тенант
                print("\nИмпортировать в:")
                print("1. Текущий тенант")
                print("2. Другой тенант")
                
                import_choice = input("Ваш выбор (1-2): ").strip()
                
                target_tenant_id = None
                if import_choice == '2':
                    target_tenant = self._select_tenant_interactive()
                    if not target_tenant:
                        continue
                    target_tenant_id = target_tenant.get('id')
                
                print("\nИмпорт шаблона...")
                result = self.import_template(file_path, target_tenant_id)
                
                if result:
                    print("✅ Импорт завершен успешно!")
                else:
                    print("❌ Импорт не удался")
            
            elif choice == '4':
                # Показать список шаблонов
                templates = self.get_user_templates()
                if templates:
                    print("\nПользовательские шаблоны политик:")
                    for i, template in enumerate(templates, 1):
                        print(f"{i}. {template.get('name', 'Без названия')}")
                        print(f"   ID: {template.get('id')}")
                        print(f"   Тип: {template.get('type')}")
                        print(f"   Правила пользователя: {template.get('has_user_rules', False)}")
                        
                        # Показываем базовые шаблоны
                        vendor_templates = template.get('templates', [])
                        if vendor_templates:
                            print(f"   Основан на: {len(vendor_templates)} базовых шаблонах")
                        print()
                else:
                    print("Не найдено пользовательских шаблонов")
            
            elif choice == '5':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")