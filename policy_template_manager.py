import os
import json
import datetime
from urllib.parse import urljoin

class PolicyTemplateManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_vendor_templates(self):
        """Получает список системных шаблонов"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/vendor")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении системных шаблонов")
            return None
        
        templates = response.json()
        if isinstance(templates, dict) and 'items' in templates:
            return templates['items']
        elif isinstance(templates, list):
            return templates
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_user_templates(self):
        """Получает список пользовательских шаблонов"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении пользовательских шаблонов")
            return None
        
        templates = response.json()
        if isinstance(templates, dict) and 'items' in templates:
            return templates['items']
        elif isinstance(templates, list):
            return templates
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_policies_with_user_rules(self):
        """Получает список шаблонов с пользовательскими правилами"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении шаблонов с пользовательскими правилами")
            return None
        
        templates = response.json()
        if isinstance(templates, dict) and 'items' in templates:
            return templates['items']
        elif isinstance(templates, list):
            return templates
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_security_policies(self):
        """Получает список политик безопасности"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении политик безопасности")
            return None
        
        policies = response.json()
        if isinstance(policies, dict) and 'items' in policies:
            return policies['items']
        elif isinstance(policies, list):
            return policies
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_template_details(self, template_id):
        """Получает детали шаблона"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении деталей шаблона")
            return None
        
        return response.json()

    def get_template_rules(self, template_id):
        """Получает список правил шаблона"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении правил шаблона")
            return None
        
        rules = response.json()
        if isinstance(rules, dict) and 'items' in rules:
            return rules['items']
        elif isinstance(rules, list):
            return rules
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении деталей правила")
            return None
        
        return response.json()

    def get_rule_aggregation(self, template_id, rule_id):
        """Получает настройки агрегации правила"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении настроек агрегации")
            return None
        
        return response.json()

    def create_template(self, name, vendor_template_ids, has_user_rules=False):
        """Создает новый шаблон"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user")
        
        payload = {
            "name": name,
            "has_user_rules": has_user_rules,
            "templates": vendor_template_ids
        }
        
        response = self.make_request("POST", url, json=payload)
        if not response or response.status_code != 201:
            print(f"Ошибка при создании шаблона")
            return None
        
        return response.json()

    def create_policy_from_template(self, policy_name, template_id):
        """Создает политику на основе шаблона"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies")
        
        payload = {
            "name": policy_name,
            "template_id": template_id
        }
        
        response = self.make_request("POST", url, json=payload)
        if not response or response.status_code != 201:
            print(f"Ошибка при создании политики")
            return None
        
        return response.json()

    def duplicate_template_in_tenant(self, source_template_id, new_name):
        """Копирует шаблон в текущем тенанте"""
        print(f"\nКопирование шаблона в текущем тенанте...")
        
        template_details = self.get_template_details(source_template_id)
        if not template_details:
            print("Не удалось получить детали шаблона")
            return None
        
        template_name = new_name or f"{template_details.get('name', 'Шаблон')} (копия)"
        vendor_template_ids = template_details.get('templates', [])
        has_user_rules = template_details.get('has_user_rules', False)
        
        print(f"Создание нового шаблона: {template_name}")
        
        new_template = self.create_template(template_name, vendor_template_ids, has_user_rules)
        if not new_template:
            print("Не удалось создать шаблон")
            return None
        
        new_template_id = new_template.get('id')
        print(f"Новый шаблон создан с ID: {new_template_id}")
        
        export_file = self.export_template(source_template_id, "temp_export")
        if export_file:
            result = self.import_template(export_file, self.auth_manager.tenant_id)
            if result:
                print("✅ Шаблон успешно скопирован")
            else:
                print("⚠️ Шаблон создан, но правила не скопированы")
            
            try:
                os.remove(export_file)
                if os.path.exists("temp_export") and not os.listdir("temp_export"):
                    os.rmdir("temp_export")
            except:
                pass
        else:
            print("✅ Шаблон создан, но без правил")
        
        return new_template

    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет правило"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self.make_request("PATCH", url, json=update_data)
        return response

    def update_rule_aggregation(self, template_id, rule_id, aggregation_data):
        """Обновляет настройки агрегации"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation")
        
        response = self.make_request("PATCH", url, json=aggregation_data)
        return response

    def get_available_actions(self):
        """Получает список доступных действий"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/actions")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении действий")
            return None
        
        actions = response.json()
        if isinstance(actions, dict) and 'items' in actions:
            return actions['items']
        elif isinstance(actions, list):
            return actions
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def get_available_lists(self):
        """Получает список доступных списков"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/lists")
        
        response = self.make_request("GET", url)
        if not response or response.status_code != 200:
            print(f"Ошибка при получении списков")
            return None
        
        lists = response.json()
        if isinstance(lists, dict) and 'items' in lists:
            return lists['items']
        elif isinstance(lists, list):
            return lists
        else:
            print(f"Неподдерживаемый формат ответа")
            return None

    def _get_filtered_rules_with_details(self, template_id):
        """Получает только измененные правила"""
        print("Получение правил шаблона...")
        rules = self.get_template_rules(template_id)
        if rules is None:
            return []
        
        modified_rules = []
        for rule in rules:
            if rule.get('has_overrides') == True:
                modified_rules.append(rule)
        
        print(f"Найдено {len(modified_rules)} измененных правил из {len(rules)} всего")
        
        full_rules_data = []
        for i, rule in enumerate(modified_rules, 1):
            rule_id = rule.get('id')
            rule_name = rule.get('name', f'Правило {i}')
            
            print(f"  [{i}/{len(modified_rules)}] Получение деталей: {rule_name}")
            
            rule_details = self.get_rule_details(template_id, rule_id)
            if rule_details:
                aggregation_data = self.get_rule_aggregation(template_id, rule_id)
                if aggregation_data:
                    rule_details['aggregation'] = aggregation_data
                full_rules_data.append(rule_details)
        
        return full_rules_data

    def export_template(self, template_id, export_dir="templates_export"):
        """Экспортирует шаблон"""
        print(f"\nЭкспорт шаблона политики ID: {template_id}")
        
        template_details = self.get_template_details(template_id)
        if not template_details:
            print("Не удалось получить детали шаблона")
            return None
        
        modified_rules_data = self._get_filtered_rules_with_details(template_id)
        
        if not modified_rules_data:
            print("⚠️ В шаблоне нет измененных правил")
            print("Экспортируется только информация о шаблоне")
        
        action_ids = set()
        global_list_ids = set()
        
        for rule_data in modified_rules_data:
            if 'actions' in rule_data and rule_data['actions']:
                action_ids.update(rule_data['actions'])
            
            if 'variables' in rule_data and rule_data['variables']:
                variables = rule_data['variables']
                if 'dynamic_global_lists' in variables:
                    dgl = variables['dynamic_global_lists']
                    if 'value' in dgl and isinstance(dgl['value'], list):
                        global_list_ids.update(dgl['value'])
            
            if 'aggregation' in rule_data and rule_data['aggregation']:
                global_list_id = rule_data['aggregation'].get('global_list_id')
                if global_list_id:
                    global_list_ids.add(global_list_id)
        
        related_actions = []
        if action_ids:
            print(f"Получение связанных действий ({len(action_ids)})...")
            all_actions = self.get_available_actions()
            if all_actions:
                related_actions = [action for action in all_actions if action.get('id') in action_ids]
                print(f"Найдено {len(related_actions)} действий")
        
        related_global_lists = []
        if global_list_ids:
            print(f"Получение связанных глобальных списков ({len(global_list_ids)})...")
            from global_lists_manager import GlobalListsManager
            lists_manager = GlobalListsManager(self.auth_manager, self.make_request)
            all_lists = lists_manager.get_global_lists()
            
            if all_lists:
                filtered_lists = [lst for lst in all_lists if lst.get('id') in global_list_ids]
                
                for lst in filtered_lists:
                    list_id = lst.get('id')
                    list_details = lists_manager.get_global_list_details(list_id)
                    if list_details:
                        related_global_lists.append(list_details)
                
                print(f"Найдено {len(related_global_lists)} глобальных списков")
        
        export_data = {
            "template": template_details,
            "modified_rules": modified_rules_data,
            "related_actions": related_actions,
            "related_global_lists": related_global_lists,
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
        
        os.makedirs(export_dir, exist_ok=True)
        
        template_name = template_details.get('name', 'unnamed_template')
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in template_name)
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{safe_name}_{timestamp}.template.json"
        filepath = os.path.join(export_dir, filename)
        
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
        """Импортирует шаблон"""
        print(f"\nИмпорт шаблона из файла: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка при чтении файла: {e}")
            return False
        
        if 'template' not in import_data:
            print("❌ Некорректный формат файла")
            return False
        
        template_data = import_data['template']
        modified_rules_data = import_data.get('modified_rules', [])
        related_actions = import_data.get('related_actions', [])
        related_global_lists = import_data.get('related_global_lists', [])
        
        export_info = import_data.get('export_info', {})
        export_type = export_info.get('export_type', 'full')
        
        if export_type == 'modified_rules_only':
            print("📋 Тип экспорта: только измененные правила")
        
        print(f"📊 Данные для импорта:")
        print(f"  - Измененных правил: {len(modified_rules_data)}")
        print(f"  - Связанных действий: {len(related_actions)}")
        print(f"  - Связанных глобальных списков: {len(related_global_lists)}")
        
        original_tenant_id = self.auth_manager.tenant_id
        
        if target_tenant_id and target_tenant_id != original_tenant_id:
            print(f"\n🔀 Переключаемся на тенант: {target_tenant_id}")
            self.auth_manager.tenant_id = target_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"❌ Не удалось переключиться на тенант")
                self.auth_manager.tenant_id = original_tenant_id
                return False
        
        try:
            print("\n1. Импортируем глобальные списки...")
            global_list_mapping = {}
            
            if related_global_lists:
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
                    
                    import_result = lists_manager.import_global_lists(temp_lists_file, target_tenant_id)
                    
                    if isinstance(import_result, dict):
                        global_list_mapping = import_result
                        print(f"  ✓ Импортировано глобальных списков: {len(global_list_mapping)}")
                    else:
                        print("  ⚠️ Не удалось получить маппинг")
                
                except Exception as e:
                    print(f"  ⚠️ Ошибка при импорте глобальных списков: {e}")
                finally:
                    try:
                        os.remove(temp_lists_file)
                    except:
                        pass
            else:
                print("  ℹ️ Нет глобальных списков для импорта")
            
            print("\n2. Проверяем и создаем связанные действия...")
            action_mapping = {}
            
            for action in related_actions:
                original_action_id = action.get('id')
                action_name = action.get('name')
                action_type_id = action.get('type_id')
                
                existing_actions = self.get_available_actions()
                existing_action = None
                
                if existing_actions:
                    for existing in existing_actions:
                        if (existing.get('name') == action_name and 
                            existing.get('type_id') == action_type_id):
                            existing_action = existing
                            break
                
                if existing_action:
                    print(f"  ✓ Действие '{action_name}' уже существует")
                    action_mapping[original_action_id] = existing_action.get('id')
                else:
                    action_data = action.copy()
                    if 'id' in action_data:
                        del action_data['id']
                    
                    from actions_backup_manager import ActionsBackupManager
                    actions_manager = ActionsBackupManager(self.auth_manager, self.make_request)
                    response = actions_manager.create_custom_action(action_data)
                    
                    if response and response.status_code == 201:
                        new_action = response.json()
                        new_action_id = new_action.get('id')
                        action_mapping[original_action_id] = new_action_id
                        print(f"  ✓ Действие '{action_name}' создано")
                    else:
                        error_msg = response.text if response else "Неизвестная ошибка"
                        print(f"  ✗ Ошибка при создании действия '{action_name}': {error_msg}")
            
            print("\n3. Проверяем шаблон политики...")
            template_name = template_data.get('name')
            
            existing_templates = self.get_user_templates()
            existing_template = None
            
            if existing_templates:
                for existing in existing_templates:
                    if existing.get('name') == template_name:
                        existing_template = existing
                        break
            
            if existing_template:
                print(f"  ✓ Шаблон '{template_name}' уже существует")
                target_template_id = existing_template.get('id')
            else:
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
                print(f"  ✓ Шаблон '{template_name}' создан")
            
            print(f"\n4. Импортируем измененные правила (всего: {len(modified_rules_data)})...")
            
            if not modified_rules_data:
                print("  ⚠️ Нет измененных правил для импорта")
                print(f"\n✅ Импорт завершен! (только шаблон)")
                return True
            
            imported_rules = 0
            failed_rules = 0
            
            for i, rule_data in enumerate(modified_rules_data, 1):
                rule_name = rule_data.get('name', f'Правило {i}')
                original_rule_id = rule_data.get('id')
                
                print(f"\n  [{i}/{len(modified_rules_data)}] Правило: {rule_name}")
                
                if not rule_data.get('has_overrides', False):
                    print(f"    ⚠️ Правило не помечено как измененное, пропускаем")
                    continue
                
                target_rules = self.get_template_rules(target_template_id)
                target_rule = None
                
                if target_rules:
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
                
                update_data = {}
                
                original_actions = rule_data.get('actions', [])
                if original_actions:
                    mapped_actions = []
                    for action_id in original_actions:
                        if action_id in action_mapping:
                            mapped_actions.append(action_mapping[action_id])
                        else:
                            mapped_actions.append(action_id)
                    
                    update_data['actions'] = mapped_actions
                
                if 'enabled' in rule_data:
                    update_data['enabled'] = rule_data['enabled']
                
                if 'variables' in rule_data and rule_data['variables']:
                    variables_data = rule_data['variables'].copy()
                    
                    if 'dynamic_global_lists' in variables_data:
                        dgl = variables_data['dynamic_global_lists']
                        if 'value' in dgl and isinstance(dgl['value'], list):
                            mapped_values = []
                            for list_id in dgl['value']:
                                if list_id in global_list_mapping:
                                    mapped_values.append(global_list_mapping[list_id])
                                else:
                                    mapped_values.append(list_id)
                            dgl['value'] = mapped_values
                    
                    update_data['variables'] = variables_data
                
                if not update_data:
                    print(f"    ⚠️ Нет данных для обновления, пропскаем")
                    failed_rules += 1
                    continue
                
                print(f"    Обновление правила...")
                response = self.update_rule(target_template_id, target_rule_id, update_data)
                
                if response and response.status_code == 200:
                    print(f"    ✓ Правило успешно обновлено")
                    
                    if 'aggregation' in rule_data and rule_data['aggregation']:
                        aggregation_data = rule_data['aggregation'].copy()
                        
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
            
            return imported_rules > 0
            
        finally:
            if original_tenant_id:
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)

    def copy_template_to_another_tenant(self, source_template_id, target_tenant_id):
        """Копирует шаблон в другой тенант"""
        print(f"\nКопирование шаблона в другой тенант...")
        
        original_tenant_id = self.auth_manager.tenant_id
        
        try:
            self.auth_manager.tenant_id = original_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print("❌ Не удалось переключиться на исходный тенант")
                return False
            
            export_dir = "temp_export"
            os.makedirs(export_dir, exist_ok=True)
            
            export_file = self.export_template(source_template_id, export_dir)
            
            if not export_file:
                print("❌ Не удалось экспортировать шаблон")
                return False
            
            result = self.import_template(export_file, target_tenant_id)
            
            try:
                os.remove(export_file)
                if os.path.exists(export_dir) and not os.listdir(export_dir):
                    os.rmdir(export_dir)
            except Exception as e:
                print(f"⚠️ Не удалось удалить временные файлы: {e}")
            
            return result
            
        finally:
            if original_tenant_id:
                self.auth_manager.tenant_id = original_tenant_id
                self.auth_manager.update_jwt_with_tenant(self.make_request)

    def _select_template_interactive(self):
        """Интерактивный выбор шаблона"""
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено шаблонов")
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

    def manage_policy_templates_extended(self):
        """Расширенное управление шаблонами политик и политиками безопасности"""
        while True:
            print("\n=== УПРАВЛЕНИЕ ШАБЛОНАМИ И ПОЛИТИКАМИ БЕЗОПАСНОСТИ ===")
            print("1. Работа с шаблонами политик")
            print("2. Работа с политиками безопасности")
            print("3. Вернуться в главное меню")
            
            choice = input("\nВыберите раздел (1-3): ")
            
            if choice == '1':
                self._manage_policy_templates_section()
            elif choice == '2':
                self._manage_security_policies_section()
            elif choice == '3':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _manage_policy_templates_section(self):
        """Раздел управления шаблонами политик"""
        while True:
            print("\n=== РАБОТА С ШАБЛОНАМИ ПОЛИТИК ===")
            print("1. Показать список системных шаблонов (наборов правил)")
            print("2. Создать новый шаблон политики")
            print("3. Выгрузить шаблон политики безопасности (JSON со всеми объектами)")
            print("4. Загрузить шаблон из JSON файла")
            print("5. Копировать шаблон в другой тенант")
            print("6. Копировать шаблон в этом тенанте")
            print("7. Вернуться назад")
            
            choice = input("\nВыберите действие (1-7): ")
            
            if choice == '1':
                self._show_vendor_templates()
            elif choice == '2':
                self._create_new_template()
            elif choice == '3':
                self._export_template()
            elif choice == '4':
                self._import_template()
            elif choice == '5':
                self._copy_template_to_another_tenant()
            elif choice == '6':
                self._duplicate_template_in_tenant()
            elif choice == '7':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _manage_security_policies_section(self):
        """Раздел управления политиками безопасности"""
        while True:
            print("\n=== РАБОТА С ПОЛИТИКАМИ БЕЗОПАСНОСТИ ===")
            print("1. Посмотреть список политик")
            print("2. Создать шаблон политики безопасности на основе выбранной политики")
            print("3. Вернуться назад")
            
            choice = input("\nВыберите действие (1-3): ")
            
            if choice == '1':
                self._show_security_policies()
            elif choice == '2':
                self._create_template_from_policy()
            elif choice == '3':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _show_vendor_templates(self):
        """Показать список системных шаблонов"""
        templates = self.get_vendor_templates()
        if templates:
            print("\nСистемные шаблоны (наборы правил):")
            for i, template in enumerate(templates, 1):
                print(f"{i}. {template.get('name', 'Без названия')}")
                print(f"   ID: {template.get('id')}")
                print(f"   Тип: {template.get('type')}")
                print(f"   Описание: {template.get('description', 'Нет описания')}")
                print()
        else:
            print("Не найдено системных шаблонов")

    def _show_security_policies(self):
        """Показать список политик безопасности"""
        policies = self.get_security_policies()
        if policies:
            print("\nПолитики безопасности:")
            for i, policy in enumerate(policies, 1):
                print(f"{i}. {policy.get('name', 'Без названия')}")
                print(f"   ID: {policy.get('id')}")
                print(f"   Статус: {policy.get('status', 'Неизвестно')}")
                print(f"   Создан: {policy.get('created', 'Неизвестно')}")
                
                template_info = policy.get('template', {})
                if template_info:
                    print(f"   Шаблон: {template_info.get('name', 'Без названия')} (ID: {template_info.get('id')})")
                print()
        else:
            print("Не найдено политик безопасности")

    def _create_new_template(self):
        """Создать новый шаблон политики"""
        print("\nСоздание нового шаблона политики")
        
        vendor_templates = self.get_vendor_templates()
        if not vendor_templates:
            print("Не удалось получить список системных шаблонов")
            return
        
        name = input("Введите имя нового шаблона: ").strip()
        if not name:
            print("Имя шаблона не может быть пустым")
            return
        
        print("\nВыберите системные шаблоны для включения:")
        for i, template in enumerate(vendor_templates, 1):
            print(f"{i}. {template.get('name')}")
        
        selected_indices = []
        while True:
            choice = input("Введите номера шаблонов через запятую (например: 1,2,3) или 'q' для отмены: ").strip()
            if choice.lower() == 'q':
                return
            
            try:
                indices = [int(num.strip()) - 1 for num in choice.split(',')]
                valid_indices = [i for i in indices if 0 <= i < len(vendor_templates)]
                
                if valid_indices:
                    selected_indices = valid_indices
                    break
                else:
                    print("Некорректные номера")
            except ValueError:
                print("Пожалуйста, введите номера через запятую")
        
        vendor_template_ids = [vendor_templates[i]['id'] for i in selected_indices]
        
        result = self.create_template(name, vendor_template_ids, has_user_rules=True)
        if result:
            print(f"✅ Шаблон '{name}' успешно создан (ID: {result.get('id')})")
        else:
            print("❌ Ошибка при создании шаблона")

    def _export_template(self):
        """Экспортировать шаблон"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return
        
        template = self._select_template_interactive()
        if not template:
            return
        
        template_id = template.get('id')
        template_name = template.get('name', 'Без названия')
        
        export_dir = input(f"Введите путь для экспорта [templates_export]: ").strip()
        if not export_dir:
            export_dir = "templates_export"
        
        print(f"\nЭкспорт шаблона '{template_name}'...")
        export_file = self.export_template(template_id, export_dir)
        
        if export_file:
            print(f"✅ Шаблон успешно экспортирован: {export_file}")

    def _import_template(self):
        """Импортировать шаблон из JSON"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return
        
        file_path = input("Введите путь к JSON файлу шаблона: ").strip()
        if not file_path or not os.path.exists(file_path):
            print("Файл не найден")
            return
        
        # Используем метод выбора тенанта из SnapshotManager
        from snapshot_manager import SnapshotManager
        snapshot_manager = SnapshotManager(self.auth_manager, self.make_request)
        
        print("\nИмпортировать в:")
        print("1. Текущий тенант")
        print("2. Другой тенант")
        
        import_choice = input("Ваш выбор (1-2): ").strip()
        
        target_tenant_id = None
        if import_choice == '2':
            tenants = snapshot_manager.get_available_tenants()
            
            if tenants:
                print("\nВыберите целевой тенант:")
                for i, tenant in enumerate(tenants, 1):
                    print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
                
                while True:
                    try:
                        tenant_choice = input("Выберите номер тенанта: ").strip()
                        if tenant_choice.lower() == 'q':
                            return
                        
                        index = int(tenant_choice) - 1
                        if 0 <= index < len(tenants):
                            target_tenant_id = tenants[index].get('id')
                            break
                        else:
                            print("Некорректный номер")
                    except ValueError:
                        print("Пожалуйста, введите число")
        
        print("\nИмпорт шаблона...")
        result = self.import_template(file_path, target_tenant_id)
        
        if result:
            print("✅ Импорт завершен успешно!")
        else:
            print("❌ Импорт не удался")

    def _copy_template_to_another_tenant(self):
        """Копировать шаблон в другой тенант"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return
        
        print("\nВыберите шаблон для копирования:")
        template = self._select_template_interactive()
        if not template:
            return
        
        template_id = template.get('id')
        template_name = template.get('name', 'Без названия')
        
        # Используем SnapshotManager для выбора тенанта
        from snapshot_manager import SnapshotManager
        snapshot_manager = SnapshotManager(self.auth_manager, self.make_request)
        tenants = snapshot_manager.get_available_tenants()
        
        if not tenants:
            print("Не удалось получить список тенантов")
            return
        
        print("\nВыберите целевой тенант:")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        while True:
            try:
                choice = input("Выберите номер целевого тенанта (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return
                
                index = int(choice) - 1
                if 0 <= index < len(tenants):
                    target_tenant = tenants[index]
                    target_tenant_id = target_tenant.get('id')
                    target_tenant_name = target_tenant.get('name', 'Без названия')
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        if target_tenant_id == self.auth_manager.tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return
        
        confirm = input(f"\nВы уверены, что хотите скопировать шаблон '{template_name}' в тенант '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            return
        
        print(f"\nКопирование шаблона '{template_name}' в тенант '{target_tenant_name}'...")
        result = self.copy_template_to_another_tenant(template_id, target_tenant_id)
        
        if result:
            print("✅ Копирование завершено успешно!")
        else:
            print("❌ Копирование не удалось")

    def _duplicate_template_in_tenant(self):
        """Копировать шаблон в текущем тенанте"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return
        
        print("\nВыберите шаблон для копирования:")
        template = self._select_template_interactive()
        if not template:
            return
        
        template_id = template.get('id')
        template_name = template.get('name', 'Без названия')
        
        new_name = input(f"Введите имя для копии шаблона [{template_name} (копия)]: ").strip()
        
        confirm = input(f"\nВы уверены, что хотите создать копию шаблона '{template_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            return
        
        print(f"\nКопирование шаблона '{template_name}'...")
        result = self.duplicate_template_in_tenant(template_id, new_name)
        
        if result:
            print("✅ Копирование завершено успешно!")
        else:
            print("❌ Копирование не удалось")

    def _create_template_from_policy(self):
        """Создать шаблон на основе политики"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return
        
        print("\nВыберите политику безопасности для создания шаблона:")
        policy = self._select_security_policy_interactive()
        if not policy:
            return
        
        policy_id = policy.get('id')
        policy_name = policy.get('name', 'Без названия')
        
        template_info = policy.get('template', {})
        template_id = template_info.get('id')
        
        if not template_id:
            print("У выбранной политики нет связанного шаблона")
            return
        
        template_details = self.get_template_details(template_id)
        if not template_details:
            print("Не удалось получить информацию о шаблоне политики")
            return
        
        new_name = input(f"Введите имя для нового шаблона [На основе {policy_name}]: ").strip()
        if not new_name:
            new_name = f"На основе {policy_name}"
        
        vendor_template_ids = template_details.get('templates', [])
        has_user_rules = template_details.get('has_user_rules', False)
        
        print(f"\nСоздание шаблона на основе политики '{policy_name}'")
        print(f"Исходный шаблон: {template_details.get('name')}")
        print(f"Системные шаблоны: {len(vendor_template_ids)}")
        print(f"Пользовательские правила: {'Да' if has_user_rules else 'Нет'}")
        
        confirm = input(f"\nВы уверены, что хотите создать шаблон '{new_name}' на основе политики? (y/n): ").lower()
        if confirm != 'y':
            print("Создание отменено")
            return
        
        new_template = self.create_template(new_name, vendor_template_ids, has_user_rules)
        if not new_template:
            print("Ошибка при создании шаблона")
            return
        
        new_template_id = new_template.get('id')
        print(f"✅ Шаблон '{new_name}' создан с ID: {new_template_id}")
        
        export_file = self.export_template(template_id, "temp_export")
        if export_file:
            try:
                with open(export_file, 'r', encoding='utf-8') as f:
                    export_data = json.load(f)
                
                export_data['template']['id'] = new_template_id
                export_data['template']['name'] = new_name
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                result = self.import_template(export_file)
                if result:
                    print("✅ Правила успешно скопированы в новый шаблон")
                else:
                    print("⚠️ Шаблон создан, но правила не скопированы")
            except Exception as e:
                print(f"❌ Ошибка при копировании правил: {e}")
            finally:
                try:
                    os.remove(export_file)
                    if os.path.exists("temp_export") and not os.listdir("temp_export"):
                        os.rmdir("temp_export")
                except:
                    pass
        else:
            print("✅ Шаблон создан, но без правил")

    def _select_template_interactive(self):
        """Интерактивный выбор шаблона"""
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено шаблонов")
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

    def _select_security_policy_interactive(self):
        """Интерактивный выбор политики безопасности"""
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

    def _select_vendor_template_interactive(self):
        """Интерактивный выбор системного шаблона"""
        templates = self.get_vendor_templates()
        if not templates:
            print("Не найдено системных шаблонов")
            return None
        
        print("\nДоступные системные шаблоны (наборы правил):")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
        
        while True:
            try:
                choice = input("\nВыберите номер системного шаблона (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    return templates[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")