import os
import json
import datetime
import tempfile
import shutil
from base_manager import BaseManager

class PolicyTemplateManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
    
    # ==================== ПОЛУЧЕНИЕ ДАННЫХ ====================
    
    def get_vendor_templates(self):
        """Получает список системных шаблонов"""
        response = self.api_client.get_vendor_templates()
        return self._parse_response_items(response)
    
    def get_user_templates(self):
        """Получает список пользовательских шаблонов (обычных)"""
        response = self.api_client.get_user_templates()
        return self._parse_response_items(response)
    
    def get_templates_with_user_rules(self):
        """Получает список наборов пользовательских правил"""
        response = self.api_client.get_templates_with_user_rules()
        return self._parse_response_items(response)
    
    def get_template_details(self, template_id, is_user_rules_template=False):
        """Получает детали шаблона"""
        if is_user_rules_template:
            # Для набора пользовательских правил - нужно использовать другой endpoint
            # В текущем API может не быть отдельного метода, используем базовый
            print(f"⚠️ Получение деталей набора пользовательских правил может потребовать отдельного метода")
            return None
        else:
            response = self.api_client.get_template_details(template_id)
            if response and response.status_code == 200:
                return response.json()
        return None
    
    def get_template_rules(self, template_id, template_type='user'):
        """Получает список ВСЕХ правил шаблона"""
        if template_type == 'with_user_rules':
            # Это набор пользовательских правил
            return self.get_user_rules_template_rules(template_id)
        else:
            # Это обычный шаблон
            return self.get_regular_template_rules(template_id)
    
    def get_regular_template_rules(self, template_id):
        """Получает все правила обычного шаблона (системные + пользовательские внутри)"""
        # Получаем системные правила
        system_rules_response = self.api_client.get_template_rules(template_id)
        system_rules = self._parse_response_items(system_rules_response) or []
        
        # Проверяем, есть ли у шаблона пользовательские правила
        template_details = self.get_template_details(template_id)
        user_rules = []
        
        if template_details and template_details.get('has_user_rules', False):
            # Получаем пользовательские правила внутри шаблона
            user_rules_response = self.api_client.get_policy_user_rules_in_template(template_id)
            user_rules = self._parse_response_items(user_rules_response) or []
            
            # Помечаем пользовательские правила
            for rule in user_rules:
                rule['is_user_rule'] = True
                rule['template_type'] = 'user'  # Обычный шаблон с user_rules
        
        # Объединяем правила
        all_rules = system_rules + user_rules
        return all_rules
    
    def get_user_rules_template_rules(self, template_id):
        """Получает правила из набора пользовательских правил"""
        response = self.api_client.get_user_rules(template_id)
        rules = self._parse_response_items(response) or []
        
        # Помечаем как пользовательские правила из набора
        for rule in rules:
            rule['is_user_rule'] = True
            rule['template_type'] = 'with_user_rules'  # Набор пользовательских правил
            rule['is_user_rules_template'] = True
        
        return rules
    
    def get_rule_details(self, template_id, rule_id, template_type='user', is_user_rule=False):
        """Получает детали конкретного правила"""
        if template_type == 'with_user_rules':
            # Это набор пользовательских правил
            response = self.api_client.get_user_rule_details(template_id, rule_id)
        elif is_user_rule:
            # Это пользовательское правило внутри обычного шаблона
            response = self.api_client.get_policy_user_rule_details_in_template(template_id, rule_id)
        else:
            # Это системное правило внутри обычного шаблона
            response = self.api_client.get_template_rule_details(template_id, rule_id)
        
        if response and response.status_code == 200:
            rule_data = response.json()
            # Добавляем метаданные о типе
            rule_data['template_type'] = template_type
            rule_data['is_user_rule'] = is_user_rule
            return rule_data
        
        return None
    
    def get_rule_aggregation(self, template_id, rule_id, template_type='user', is_user_rule=False):
        """Получает настройки агрегации правила"""
        # Агрегация обычно только для системных правил
        if template_type == 'user' and not is_user_rule:
            response = self.api_client.get_template_rule_aggregation(template_id, rule_id)
            if response and response.status_code == 200:
                return response.json()
        return None
    
    def get_available_actions(self):
        """Получает список доступных действий"""
        response = self.api_client.get_actions()
        return self._parse_response_items(response)
    
    # ==================== СОЗДАНИЕ И ОБНОВЛЕНИЕ ====================
    
    def create_template(self, name, vendor_template_ids, has_user_rules=False, template_type='user'):
        """Создает новый шаблон"""
        if template_type == 'with_user_rules':
            # Создание набора пользовательских правил
            print("⚠️ Создание набора пользовательских правил не поддерживается в текущем API")
            return None
        
        payload = {
            "name": name,
            "has_user_rules": has_user_rules,
            "templates": vendor_template_ids
        }
        response = self.api_client.create_template(payload)
        if response and response.status_code == 201:
            return response.json()
        return None
    
    def update_rule(self, template_id, rule_id, update_data, template_type='user', is_user_rule=False):
        """Обновляет правило"""
        if template_type == 'with_user_rules':
            # Это набор пользовательских правил
            return self.api_client.update_user_rule(template_id, rule_id, update_data)
        elif is_user_rule:
            # Это пользовательское правило внутри обычного шаблона
            return self.api_client.update_policy_user_rule_in_template(template_id, rule_id, update_data)
        else:
            # Это системное правило внутри обычного шаблона
            return self.api_client.update_template_rule(template_id, rule_id, update_data)
    
    def update_rule_aggregation(self, template_id, rule_id, aggregation_data, template_type='user', is_user_rule=False):
        """Обновляет настройки агрегации правила"""
        # Агрегация обычно только для системных правил
        if template_type == 'user' and not is_user_rule:
            return self.api_client.update_template_rule_aggregation(template_id, rule_id, aggregation_data)
        return None
    
    # ==================== ЭКСПОРТ/ИМПОРТ ====================
    
    def _get_filtered_rules_with_details(self, template_id, template_type='user'):
        """Получает только измененные правила"""
        print("Получение правил шаблона...")
        rules = self.get_template_rules(template_id, template_type)
        if rules is None:
            return []
        
        modified_rules = []
        for rule in rules:
            # Проверяем, есть ли изменения в правиле
            has_overrides = rule.get('has_overrides', False)
            is_user_rule = rule.get('is_user_rule', False)
            is_user_rules_template = rule.get('is_user_rules_template', False)
            
            # Для пользовательских правил всегда считаем их измененными
            if is_user_rule or has_overrides:
                modified_rules.append(rule)
        
        print(f"Найдено {len(modified_rules)} измененных правил из {len(rules)} всего")
        
        full_rules_data = []
        for i, rule in enumerate(modified_rules, 1):
            rule_id = rule.get('id')
            rule_name = rule.get('name', f'Правило {i}')
            is_user_rule = rule.get('is_user_rule', False)
            template_type = rule.get('template_type', 'user')
            
            rule_type = "пользовательское" if is_user_rule else "системное"
            if template_type == 'with_user_rules':
                rule_type += " (из набора пользовательских правил)"
            
            print(f"  [{i}/{len(modified_rules)}] Получение деталей: {rule_name} ({rule_type})")
            
            rule_details = self.get_rule_details(template_id, rule_id, template_type, is_user_rule)
            if rule_details:
                # Сохраняем информацию о типе правила
                rule_details['is_user_rule'] = is_user_rule
                rule_details['template_type'] = template_type
                rule_details['original_rule_id'] = rule.get('rule_id')  # Это system rule_id для системных правил
                rule_details['original_rule_name'] = rule_name
                
                # Для системных правил получаем агрегацию
                if template_type == 'user' and not is_user_rule:
                    aggregation_data = self.get_rule_aggregation(template_id, rule_id, template_type, is_user_rule)
                    if aggregation_data:
                        rule_details['aggregation'] = aggregation_data
                
                full_rules_data.append(rule_details)
        
        return full_rules_data
    
    def export_template(self, template_id, export_dir="templates_export", template_type='user'):
        """Экспортирует шаблон"""
        print(f"\nЭкспорт шаблона политики ID: {template_id}")
        
        # Получаем информацию о шаблоне
        template_info = None
        if template_type == 'user':
            template_info = self.get_template_details(template_id)
        else:
            # Для набора пользовательских правил получаем базовую информацию
            templates = self.get_templates_with_user_rules()
            if templates:
                for tmpl in templates:
                    if tmpl.get('id') == template_id:
                        template_info = tmpl
                        break
        
        if not template_info:
            print("Не удалось получить информацию о шаблоне")
            return None
        
        modified_rules_data = self._get_filtered_rules_with_details(template_id, template_type)
        
        if not modified_rules_data:
            print("⚠️ В шаблоне нет измененных правил")
            print("Экспортируется только информация о шаблоне")
        
        # Собираем все связанные объекты
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
                for action in all_actions:
                    if action.get('id') in action_ids:
                        related_actions.append(action)
                print(f"Найдено {len(related_actions)} действий")
        
        related_global_lists = []
        if global_list_ids:
            print(f"Получение связанных глобальных списков ({len(global_list_ids)})...")
            from global_lists_manager import GlobalListsManager
            lists_manager = GlobalListsManager(self.api_client)
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
            "template": template_info,
            "template_type": template_type,
            "modified_rules": modified_rules_data,
            "related_actions": related_actions,
            "related_global_lists": related_global_lists,
            "export_info": {
                "export_time": datetime.datetime.now().isoformat(),
                "tenant_id": self.api_client.auth_manager.tenant_id,
                "api_path": self.api_client.auth_manager.api_path,
                "base_url": self.api_client.auth_manager.base_url,
                "export_type": "modified_rules_only",
                "rules_count": len(modified_rules_data),
                "actions_count": len(related_actions),
                "global_lists_count": len(related_global_lists)
            }
        }
        
        os.makedirs(export_dir, exist_ok=True)
        
        template_name = template_info.get('name', 'unnamed_template')
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in template_name)
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{safe_name}_{timestamp}.template.json"
        filepath = os.path.join(export_dir, filename)
        
        absolute_filepath = os.path.abspath(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Шаблон успешно экспортирован в файл:")
            print(f"📁 Полный путь: {absolute_filepath}")
            return absolute_filepath
        except Exception as e:
            print(f"❌ Ошибка при сохранении шаблона: {e}")
            return None
    
    def _find_rule_in_template(self, template_id, rule_identifier, rule_name, is_user_rule=False):
        """Находит правило в шаблоне"""
        if is_user_rule:
            # Для пользовательских правил ищем по имени
            rules = self.get_template_user_rules(template_id)
        else:
            # Для системных правил
            rules = self.get_template_system_rules(template_id)
        
        if not rules:
            return None
        
        # Для пользовательских правил ищем только по имени
        if is_user_rule:
            for rule in rules:
                if rule.get('name') == rule_name:
                    return rule
            
            # Ищем по частичному совпадению имени
            for rule in rules:
                if rule_name in rule.get('name', ''):
                    return rule
        else:
            # Для системных правил сначала ищем по rule_id
            for rule in rules:
                if rule.get('rule_id') == rule_identifier:
                    return rule
            
            # Если не нашли по rule_id, ищем по имени
            for rule in rules:
                if rule.get('name') == rule_name:
                    return rule
        
        return None
    
    def _create_action_mapping(self, source_actions, target_tenant_id):
        """Создает маппинг ID действий между тенантами"""
        from actions_manager import ActionsManager
        actions_manager = ActionsManager(self.api_client)
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # Переключаемся на целевой тенант
            if target_tenant_id and target_tenant_id != original_tenant_id:
                self.api_client.auth_manager.tenant_id = target_tenant_id
                if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                    print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
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
                target_action = actions_manager.find_or_create_action(action)
                if target_action:
                    action_mapping[original_action_id] = target_action.get('id')
            
            return action_mapping
            
        finally:
            # Восстанавливаем оригинальный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
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
        
        export_info = import_data.get('export_info', {})
        export_type = export_info.get('export_type', 'full')
        
        if export_type == 'modified_rules_only':
            print("📋 Тип экспорта: только измененные правила")
        
        print(f"📊 Данные для импорта:")
        print(f"  - Всего правил: {len(modified_rules_data)}")
        print(f"  - Пользовательских правил: {len([r for r in modified_rules_data if r.get('is_user_rule')])}")
        print(f"  - Системных правил: {len([r for r in modified_rules_data if not r.get('is_user_rule')])}")
        print(f"  - Связанных действий: {len(related_actions)}")
        
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        if target_tenant_id and target_tenant_id != original_tenant_id:
            print(f"\n🔀 Переключаемся на тенант: {target_tenant_id}")
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"❌ Не удалось переключиться на тенант")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                return False
        
        try:
            print("\n1. Создаем маппинг действий...")
            action_mapping = self._create_action_mapping(related_actions, target_tenant_id)
            print(f"  ✓ Создан маппинг для {len(action_mapping)} действий")
            
            print("\n2. Проверяем шаблон политики...")
            template_name = template_data.get('name')
            has_user_rules = template_data.get('has_user_rules', False)
            
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
                
                # Проверяем, поддерживает ли существующий шаблон пользовательские правила
                existing_template_details = self.get_template_details(target_template_id)
                if existing_template_details and has_user_rules and not existing_template_details.get('has_user_rules'):
                    print(f"  ⚠️ Исходный шаблон имеет пользовательские правила, но целевой - нет")
            else:
                create_data = {
                    "name": template_data.get('name'),
                    "has_user_rules": has_user_rules,
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
            
            print(f"\n3. Импортируем измененные правила (всего: {len(modified_rules_data)})...")
            
            if not modified_rules_data:
                print("  ⚠️ Нет измененных правил для импорта")
                print(f"\n✅ Импорт завершен! (только шаблон)")
                return True
            
            imported_rules = 0
            failed_rules = 0
            skipped_rules = 0
            
            for i, rule_data in enumerate(modified_rules_data, 1):
                rule_name = rule_data.get('name', f'Правило {i}')
                is_user_rule = rule_data.get('is_user_rule', False)
                original_rule_id = rule_data.get('original_rule_id')
                original_rule_name = rule_data.get('original_rule_name', rule_name)
                
                print(f"\n  [{i}/{len(modified_rules_data)}] Правило: {rule_name} ({'пользовательское' if is_user_rule else 'системное'})")
                
                # Ищем правило в целевом шаблоне
                target_rule = self._find_rule_in_template(
                    target_template_id, 
                    original_rule_id, 
                    original_rule_name,
                    is_user_rule
                )
                
                if not target_rule:
                    print(f"    ⚠️ Правило '{rule_name}' не найдено в целевом шаблоне")
                    
                    # Для пользовательских правил можно было бы создать, но это сложно
                    # так как нужно знать структуру правила
                    if is_user_rule:
                        print(f"    ⚠️ Пользовательское правило нельзя автоматически создать, пропускаем")
                    
                    skipped_rules += 1
                    continue
                
                target_rule_id = target_rule.get('id')
                print(f"    ✓ Найдено правило в целевом шаблоне (ID: {target_rule_id})")
                
                # Подготавливаем данные для обновления
                update_data = {}
                
                # Обновляем действия с использованием маппинга
                original_actions = rule_data.get('actions', [])
                if original_actions:
                    mapped_actions = []
                    for action_id in original_actions:
                        if str(action_id) in action_mapping:
                            mapped_actions.append(action_mapping[str(action_id)])
                        else:
                            mapped_actions.append(action_id)  # Оставляем как есть для системных действий
                    
                    update_data['actions'] = mapped_actions
                    print(f"    Обновлено {len(mapped_actions)} действий")
                
                # Обновляем состояние правила
                if 'enabled' in rule_data:
                    update_data['enabled'] = rule_data['enabled']
                    print(f"    Состояние: {'включено' if rule_data['enabled'] else 'выключено'}")
                
                # Обновляем переменные
                if 'variables' in rule_data and rule_data['variables']:
                    update_data['variables'] = rule_data['variables'].copy()
                    print(f"    Обновлены переменные")
                
                # Обновляем код для пользовательских правил
                if is_user_rule and 'configuration' in rule_data:
                    if 'code' in rule_data['configuration']:
                        update_data['code'] = rule_data['configuration']['code']
                        print(f"    Обновлен код правила")
                
                if not update_data:
                    print(f"    ⚠️ Нет данных для обновления, пропускаем")
                    skipped_rules += 1
                    continue
                
                print(f"    Обновление правила...")
                response = self.update_rule(target_template_id, target_rule_id, update_data, is_user_rule)
                
                if response and response.status_code == 200:
                    print(f"    ✓ Правило успешно обновлено")
                    
                    # Обновляем настройки агрегации если есть (только для системных правил)
                    if not is_user_rule and 'aggregation' in rule_data and rule_data['aggregation']:
                        aggregation_data = rule_data['aggregation'].copy()
                        
                        print(f"    Обновление настроек агрегации...")
                        agg_response = self.update_rule_aggregation(target_template_id, target_rule_id, aggregation_data, is_user_rule)
                        
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
            print(f"  - Пропущено (не найдены в целевом шаблоне): {skipped_rules}")
            print(f"  - Не удалось импортировать: {failed_rules}")
            print(f"  - Всего обработано: {len(modified_rules_data)}")
            
            return imported_rules > 0
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
    def copy_template_to_another_tenant(self, source_template_id, target_tenant_id):
        """Копирует шаблон в другой тенант"""
        print(f"\nКопирование шаблона в другой тенант...")
        
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # Получаем детали шаблона для проверки наличия пользовательских правил
            self.api_client.auth_manager.tenant_id = original_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("❌ Не удалось переключиться на исходный тенант")
                return False
            
            template_details = self.get_template_details(source_template_id)
            if not template_details:
                print("❌ Не удалось получить детали шаблона")
                return False
            
            has_user_rules = template_details.get('has_user_rules', False)
            if has_user_rules:
                print(f"⚠️ Шаблон содержит пользовательские правила")
                print(f"⚠️ Пользовательские правила будут импортированы только если они уже существуют в целевом шаблоне")
            
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            
            # Экспортируем шаблон
            export_file = self.export_template(source_template_id, temp_dir)
            
            if not export_file:
                print("❌ Не удалось экспортировать шаблон")
                # Очищаем временную директорию
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            # Импортируем в целевой тенант
            result = self.import_template(export_file, target_tenant_id)
            
            # Очищаем временные файлы
            try:
                os.remove(export_file)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"⚠️ Не удалось удалить временные файлы: {e}")
            
            return result
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
    # ==================== ИНТЕРАКТИВНЫЕ МЕТОДЫ ====================
    
    def _select_template_interactive(self):
        """Интерактивный выбор шаблона"""
        templates = self.get_user_templates()
        if not templates:
            print("Не найдено шаблонов")
            return None
        
        print("\nДоступные шаблоны политик:")
        for i, template in enumerate(templates, 1):
            name = template.get('name', 'Без названия')
            template_id = template.get('id')
            has_user_rules = template.get('has_user_rules', False)
            user_rules_marker = " (с пользовательскими правилами)" if has_user_rules else ""
            print(f"{i}. {name}{user_rules_marker} (ID: {template_id})")
        
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
    
    def _select_tenant_for_operation(self, operation_name):
        """Выбирает тенант для операции"""
        print(f"\n=== {operation_name} ===")
        print("Выберите тенант для выполнения операции:")
        
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("❌ Не удалось выбрать тенант")
            return False
        return True
    
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
                if not self._select_tenant_for_operation("ПОКАЗАТЬ СПИСОК СИСТЕМНЫХ ШАБЛОНОВ"):
                    continue
                self._show_vendor_templates()
            
            elif choice == '2':
                if not self._select_tenant_for_operation("СОЗДАТЬ НОВЫЙ ШАБЛОН"):
                    continue
                self._create_new_template()
            
            elif choice == '3':
                if not self._select_tenant_for_operation("ВЫГРУЗИТЬ ШАБЛОН"):
                    continue
                self._export_template()
            
            elif choice == '4':
                self._import_template()
            
            elif choice == '5':
                self._copy_template_to_another_tenant_menu()
            
            elif choice == '6':
                if not self._select_tenant_for_operation("КОПИРОВАТЬ ШАБЛОН В ЭТОМ ТЕНАНТЕ"):
                    continue
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
                if not self._select_tenant_for_operation("ПОКАЗАТЬ СПИСОК ПОЛИТИК"):
                    continue
                self._show_security_policies()
            
            elif choice == '2':
                if not self._select_tenant_for_operation("СОЗДАТЬ ШАБЛОН НА ОСНОВЕ ПОЛИТИКИ"):
                    continue
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
        from policies_manager import PoliciesManager
        policies_manager = PoliciesManager(self.api_client)
        policies = policies_manager.get_security_policies()
        
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
            print(f"\n✅ Шаблон успешно экспортирован:")
            print(f"📁 Расположение: {export_file}")
    
    def _import_template(self):
        """Импортировать шаблон из JSON"""
        file_path = input("Введите путь к JSON файлу шаблона: ").strip()
        if not file_path or not os.path.exists(file_path):
            print("Файл не найден")
            return
        
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        
        target_tenant = tenant_manager.select_single_tenant("Выберите тенант для импорта шаблона:")
        if not target_tenant:
            print("Импорт отменен")
            return
        
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        print(f"\nИмпорт шаблона в тенант '{target_tenant_name}'...")
        result = self.import_template(file_path, target_tenant_id)
        
        if result:
            print("✅ Импорт завершен успешно!")
        else:
            print("❌ Импорт не удался")

    def _copy_template_to_another_tenant_menu(self):
        """Меню копирования шаблона в другой тенант"""
        print("\nКопирование шаблона в другой тенант")
        
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        
        # Выбираем исходный тенант и шаблон
        source_tenant = tenant_manager.select_single_tenant("Выберите исходный тенант (откуда копировать):")
        if not source_tenant:
            print("Копирование отменено")
            return
        
        source_tenant_id = source_tenant.get('id')
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Переключаемся на исходный тенант
        self.api_client.auth_manager.tenant_id = source_tenant_id
        if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
            print(f"❌ Не удалось переключиться на тенант {source_tenant_name}")
            return
        
        template = self._select_template_interactive()
        if not template:
            print("Копирование отменено")
            return
        
        template_id = template.get('id')
        template_name = template.get('name', 'Без названия')
        
        # Выбираем целевой тенант
        target_tenant = tenant_manager.select_single_tenant("Выберите целевой тенант (куда копировать):")
        if not target_tenant:
            print("Копирование отменено")
            return
        
        target_tenant_id = target_tenant.get('id')
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return
        
        confirm = input(f"\nВы уверены, что хотите скопировать шаблон '{template_name}' из тенанта '{source_tenant_name}' в тенант '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            return
        
        print(f"\nКопирование шаблона '{template_name}' из '{source_tenant_name}' в '{target_tenant_name}'...")
        result = self.copy_template_to_another_tenant(template_id, target_tenant_id)
        
        if result:
            print("✅ Копирование завершено успешно!")
        else:
            print("❌ Копирование не удалось")

    def _duplicate_template_in_tenant(self):
        """Копировать шаблон в текущем тенанте"""
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
        
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Экспортируем шаблон
            export_file = self.export_template(template_id, temp_dir)
            if not export_file:
                print("❌ Не удалось экспортировать шаблон")
                return False
            
            # Создаем новый шаблон
            template_details = self.get_template_details(template_id)
            if not template_details:
                print("❌ Не удалось получить детали шаблона")
                return False
            
            new_template_name = new_name or f"{template_name} (копия)"
            vendor_template_ids = template_details.get('templates', [])
            has_user_rules = template_details.get('has_user_rules', False)
            
            new_template = self.create_template(new_template_name, vendor_template_ids, has_user_rules)
            if not new_template:
                print("❌ Не удалось создать новый шаблон")
                return False
            
            new_template_id = new_template.get('id')
            print(f"✅ Новый шаблон создан с ID: {new_template_id}")
            
            # Модифицируем экспортированные данные для использования нового ID
            with open(export_file, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
            
            export_data['template']['id'] = new_template_id
            export_data['template']['name'] = new_template_name
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # Импортируем правила в новый шаблон
            result = self.import_template(export_file, self.api_client.auth_manager.tenant_id)
            
            if result:
                print("✅ Правила успешно скопированы в новый шаблон")
            else:
                print("⚠️ Шаблон создан, но правила не скопированы")
            
            return result
            
        finally:
            # Очищаем временные файлы
            try:
                if 'export_file' in locals() and os.path.exists(export_file):
                    os.remove(export_file)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
    
    def _create_template_from_policy(self):
        """Создать шаблон на основе политики"""
        from policies_manager import PoliciesManager
        policies_manager = PoliciesManager(self.api_client)
        
        print("\nВыберите политику безопасности для создания шаблона:")
        policies = policies_manager.get_security_policies()
        if not policies:
            print("Не найдено политик безопасности")
            return
        
        print("\nДоступные политики безопасности:")
        for i, policy in enumerate(policies, 1):
            print(f"{i}. {policy.get('name', 'Без названия')} (ID: {policy.get('id')})")
        
        while True:
            try:
                choice = input("\nВыберите номер политики (или 'q' для отмены): ").strip()
                if choice.lower() == 'q':
                    return
                
                index = int(choice) - 1
                if 0 <= index < len(policies):
                    policy = policies[index]
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        policy_id = policy.get('id')
        policy_name = policy.get('name', 'Без названия')
        
        policy_details = policies_manager.get_policy_details(policy_id)
        if not policy_details:
            print("Не удалось получить информацию о политике")
            return
        
        template_info = policy_details.get('template', {})
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
        
        # Копируем правила из исходного шаблона
        temp_dir = tempfile.mkdtemp()
        
        try:
            export_file = self.export_template(template_id, temp_dir)
            if export_file:
                # Модифицируем экспортированные данные для нового шаблона
                with open(export_file, 'r', encoding='utf-8') as f:
                    export_data = json.load(f)
                
                export_data['template']['id'] = new_template_id
                export_data['template']['name'] = new_name
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                result = self.import_template(export_file, self.api_client.auth_manager.tenant_id)
                if result:
                    print("✅ Правила успешно скопированы в новый шаблон")
                else:
                    print("⚠️ Шаблон создан, но правила не скопированы")
            else:
                print("✅ Шаблон создан, но без правил")
            
        finally:
            # Очищаем временные файлы
            try:
                if 'export_file' in locals() and os.path.exists(export_file):
                    os.remove(export_file)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass