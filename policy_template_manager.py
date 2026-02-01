# policy_template_manager.py (исправленный с раздельной обработкой)
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
        """Получает список пользовательских шаблонов"""
        response = self.api_client.get_user_templates()
        return self._parse_response_items(response)
    
    def get_templates_with_user_rules(self):
        """Получает список шаблонов с пользовательскими правилами"""
        response = self.api_client.get_templates_with_user_rules()
        return self._parse_response_items(response)
    
    def get_template_details(self, template_id):
        """Получает детали шаблона"""
        response = self.api_client.get_template_details(template_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_template_rules(self, template_id):
        """Получает список правил шаблона"""
        response = self.api_client.get_template_rules(template_id)
        return self._parse_response_items(response)
    
    def get_user_rules(self, template_id):
        """Получает правила из набора пользовательских правил"""
        response = self.api_client.get_user_rules(template_id)
        return self._parse_response_items(response)
    
    def get_user_rule_details(self, template_id, rule_id):
        """Получает детали пользовательского правила"""
        response = self.api_client.get_user_rule_details(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        response = self.api_client.get_template_rule_details(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_rule_aggregation(self, template_id, rule_id):
        """Получает настройки агрегации правила"""
        response = self.api_client.get_template_rule_aggregation(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_available_actions(self):
        """Получает список доступных действий"""
        response = self.api_client.get_actions()
        return self._parse_response_items(response)
    
    # ==================== СОЗДАНИЕ И ОБНОВЛЕНИЕ ====================
    
    def create_template(self, name, vendor_template_ids, has_user_rules=False):
        """Создает новый шаблон"""
        payload = {
            "name": name,
            "has_user_rules": has_user_rules,
            "templates": vendor_template_ids
        }
        response = self.api_client.create_template(payload)
        if response and response.status_code == 201:
            return response.json()
        return None
    
    def create_user_rule(self, template_id, rule_data):
        """Создает пользовательское правило в шаблоне"""
        response = self.api_client.create_user_rule(template_id, rule_data)
        return response
    
    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет правило"""
        return self.api_client.update_template_rule(template_id, rule_id, update_data)
    
    def update_user_rule(self, template_id, rule_id, update_data):
        """Обновляет пользовательское правило"""
        return self.api_client.update_user_rule(template_id, rule_id, update_data)
    
    def update_rule_aggregation(self, template_id, rule_id, aggregation_data):
        """Обновляет настройки агрегации"""
        return self.api_client.update_template_rule_aggregation(template_id, rule_id, aggregation_data)
    
    # ==================== ЭКСПОРТ ШАБЛОНА ====================
    
    def _get_system_rules_with_overrides(self, template_id):
        """Получает системные правила с изменениями (has_overrides: true)"""
        print("Получение системных правил с изменениями...")
        rules = self.get_template_rules(template_id)
        if rules is None:
            return []
        
        system_rules_with_overrides = []
        for rule in rules:
            if rule.get('is_system', False) and rule.get('has_overrides', False):
                system_rules_with_overrides.append(rule)
        
        print(f"Найдено {len(system_rules_with_overrides)} системных правил с изменениями из {len(rules)} всего")
        
        full_rules_data = []
        for i, rule in enumerate(system_rules_with_overrides, 1):
            rule_id = rule.get('id')
            rule_name = rule.get('name', f'Системное правило {i}')
            
            print(f"  [{i}/{len(system_rules_with_overrides)}] Получение деталей: {rule_name}")
            
            rule_details = self.get_rule_details(template_id, rule_id)
            if rule_details:
                # Сохраняем оригинальный ID для поиска в целевом шаблоне
                rule_details['original_rule_id'] = rule.get('rule_id')  # Это system rule_id
                rule_details['original_rule_name'] = rule_name
                rule_details['is_system'] = True
                rule_details['has_overrides'] = True
                
                aggregation_data = self.get_rule_aggregation(template_id, rule_id)
                if aggregation_data:
                    rule_details['aggregation'] = aggregation_data
                full_rules_data.append(rule_details)
        
        return full_rules_data
    
    def _get_user_rules_in_template(self, template_id):
        """Получает пользовательские правила в шаблоне (is_system: false)"""
        print("Получение пользовательских правил в шаблоне...")
        
        # Получаем детали шаблона для определения типа
        template_details = self.get_template_details(template_id)
        if not template_details:
            print("Не удалось получить детали шаблона")
            return []
        
        template_type = template_details.get('type', 'user')
        
        if template_type == 'with_user_rules':
            # Это отдельный набор пользовательских правил
            user_rules = self.get_user_rules(template_id)
        else:
            # Это обычный шаблон с пользовательскими правилами
            user_rules = self.get_policy_user_rules_in_template(template_id)
        
        if not user_rules:
            print("Пользовательских правил не найдено")
            return []
        
        print(f"Найдено {len(user_rules)} пользовательских правил")
        
        full_rules_data = []
        for i, rule in enumerate(user_rules, 1):
            rule_id = rule.get('id')
            rule_name = rule.get('name', f'Пользовательское правило {i}')
            
            print(f"  [{i}/{len(user_rules)}] Получение деталей: {rule_name}")
            
            if template_type == 'with_user_rules':
                rule_details = self.get_user_rule_details(template_id, rule_id)
            else:
                rule_details = self.get_policy_user_rule_details_in_template(template_id, rule_id)
            
            if rule_details:
                # Сохраняем тип шаблона для правильной обработки при импорте
                rule_details['template_type'] = template_type
                rule_details['is_system'] = False
                rule_details['original_id'] = rule_id
                rule_details['original_name'] = rule_name
                full_rules_data.append(rule_details)
        
        return full_rules_data
    
    def get_policy_user_rules_in_template(self, template_id):
        """Получает пользовательские правила внутри обычного шаблона"""
        response = self.api_client.get_policy_user_rules_in_template(template_id)
        return self._parse_response_items(response)
    
    def get_policy_user_rule_details_in_template(self, template_id, rule_id):
        """Получает детали пользовательского правила внутри обычного шаблона"""
        response = self.api_client.get_policy_user_rule_details_in_template(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def export_template(self, template_id, export_dir="templates_export", include_user_rules=True):
        """Экспортирует шаблон с разделением на системные и пользовательские правила"""
        print(f"\nЭкспорт шаблона политики ID: {template_id}")
        
        template_details = self.get_template_details(template_id)
        if not template_details:
            print("Не удалось получить детали шаблона")
            return None
        
        has_user_rules = template_details.get('has_user_rules', False)
        
        # Получаем системные правила с изменениями
        system_rules_data = self._get_system_rules_with_overrides(template_id)
        
        # Получаем пользовательские правила, если шаблон их поддерживает
        user_rules_data = []
        if has_user_rules and include_user_rules:
            user_rules_data = self._get_user_rules_in_template(template_id)
        
        if not system_rules_data and not user_rules_data:
            print("⚠️ В шаблоне нет правил для экспорта")
            print("Экспортируется только информация о шаблоне")
        
        # Собираем все действия
        all_rules_data = system_rules_data + user_rules_data
        action_ids = set()
        global_list_ids = set()
        
        for rule_data in all_rules_data:
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
                # Сохраняем полные данные о действиях
                for action in all_actions:
                    if action.get('id') in action_ids:
                        related_actions.append(action)
                print(f"Найдено {len(related_actions)} действий")
        
        # Для глобальных списков
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
            "template": template_details,
            "system_rules": system_rules_data,  # Измененные системные правила
            "user_rules": user_rules_data,      # Пользовательские правила
            "related_actions": related_actions,
            "related_global_lists": related_global_lists,
            "export_info": {
                "export_time": datetime.datetime.now().isoformat(),
                "tenant_id": self.api_client.auth_manager.tenant_id,
                "api_path": self.api_client.auth_manager.api_path,
                "base_url": self.api_client.auth_manager.base_url,
                "export_type": "full",
                "has_user_rules": has_user_rules,
                "system_rules_count": len(system_rules_data),
                "user_rules_count": len(user_rules_data),
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
        
        absolute_filepath = os.path.abspath(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Шаблон успешно экспортирован в файл:")
            print(f"📁 Полный путь: {absolute_filepath}")
            print(f"📊 Экспортировано:")
            print(f"  - Системных правил с изменениями: {len(system_rules_data)}")
            print(f"  - Пользовательских правил: {len(user_rules_data)}")
            print(f"  - Связанных действий: {len(related_actions)}")
            print(f"  - Связанных глобальных списков: {len(related_global_lists)}")
            return absolute_filepath
        except Exception as e:
            print(f"❌ Ошибка при сохранении шаблона: {e}")
            return None
    
    # ==================== ИМПОРТ ШАБЛОНА ====================
    
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
    
    def _find_system_rule_in_template(self, template_id, rule_identifier, rule_name):
        """Находит системное правило в шаблоне по идентификатору или имени"""
        rules = self.get_template_rules(template_id)
        if not rules:
            return None
        
        # Пробуем найти по original_rule_id (system rule_id)
        for rule in rules:
            if rule.get('rule_id') == rule_identifier:
                return rule
        
        # Если не нашли по rule_id, ищем по имени среди системных правил
        for rule in rules:
            if rule.get('name') == rule_name and rule.get('is_system', False):
                return rule
        
        # Ищем по частичному совпадению имени среди системных правил
        for rule in rules:
            if rule_name in rule.get('name', '') and rule.get('is_system', False):
                return rule
        
        return None
    
    def _import_system_rules_with_overrides(self, template_id, system_rules_data, action_mapping, preserve_state=True):
        """Импортирует изменения в системные правила (has_overrides: true)"""
        if not system_rules_data:
            return 0, 0
        
        imported_count = 0
        failed_count = 0
        
        print(f"\n  Импорт изменений в {len(system_rules_data)} системных правил:")
        
        for i, rule_data in enumerate(system_rules_data, 1):
            rule_name = rule_data.get('name', f'Системное правило {i}')
            original_rule_id = rule_data.get('original_rule_id')
            original_rule_name = rule_data.get('original_rule_name', rule_name)
            
            print(f"    [{i}/{len(system_rules_data)}] Правило: {rule_name}")
            
            # Ищем системное правило в целевом шаблоне
            target_rule = self._find_system_rule_in_template(
                template_id, 
                original_rule_id, 
                original_rule_name
            )
            
            if not target_rule:
                print(f"      ⚠️ Системное правило не найдено в целевом шаблоне, пропускаем")
                failed_count += 1
                continue
            
            target_rule_id = target_rule.get('id')
            print(f"      ✓ Найдено системное правило в целевом шаблоне (ID: {target_rule_id})")
            
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
                print(f"      Обновлено {len(mapped_actions)} действий")
            
            # Сохраняем состояние, если нужно
            if 'enabled' in rule_data and preserve_state:
                update_data['enabled'] = rule_data['enabled']
                print(f"      Состояние: {'включено' if rule_data['enabled'] else 'выключено'}")
            
            # Обновляем переменные
            if 'variables' in rule_data and rule_data['variables']:
                update_data['variables'] = rule_data['variables'].copy()
                print(f"      Обновлены переменные")
            
            if not update_data:
                print(f"      ⚠️ Нет данных для обновления, пропускаем")
                failed_count += 1
                continue
            
            response = self.update_rule(template_id, target_rule_id, update_data)
            
            if response and response.status_code == 200:
                print(f"      ✅ Изменения успешно применены")
                
                # Обновляем настройки агрегации если есть
                if 'aggregation' in rule_data and rule_data['aggregation']:
                    aggregation_data = rule_data['aggregation'].copy()
                    
                    agg_response = self.update_rule_aggregation(template_id, target_rule_id, aggregation_data)
                    
                    if agg_response and agg_response.status_code == 200:
                        print(f"      ✅ Настройки агрегации обновлены")
                    else:
                        error_msg = agg_response.text if agg_response else "Неизвестная ошибка"
                        print(f"      ⚠️ Ошибка при обновлении агрегации: {error_msg}")
                
                imported_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"      ✗ Ошибка при обновлении правила: {error_msg}")
                failed_count += 1
        
        return imported_count, failed_count
    
    def _import_user_rules_to_template(self, template_id, user_rules_data, action_mapping, preserve_state=True):
        """Импортирует пользовательские правила в шаблон с учетом типа правил"""
        if not user_rules_data:
            return 0, 0
        
        # Разделяем правила по типу шаблона
        rules_from_set = []      # Правила из наборов (with_user_rules)
        rules_from_policy = []   # Правила в обычных шаблонах
        
        for rule_data in user_rules_data:
            template_type = rule_data.get('template_type', 'user')
            if template_type == 'with_user_rules':
                rules_from_set.append(rule_data)
            else:
                rules_from_policy.append(rule_data)
        
        print(f"\n  Импорт {len(user_rules_data)} пользовательских правил:")
        print(f"    - Из наборов правил: {len(rules_from_set)}")
        print(f"    - В обычных шаблонах: {len(rules_from_policy)}")
        
        imported_count = 0
        failed_count = 0
        
        # ШАГ 1: Импорт правил из наборов (with_user_rules) - отдельный процесс
        if rules_from_set:
            print(f"\n  ШАГ 1: Импорт пользовательских правил...")
            print(f"    Импорт {len(rules_from_set)} правил из набора (отдельный процесс):")
            set_imported, set_failed = self._import_rules_from_user_rules_set(
                template_id, rules_from_set, action_mapping, preserve_state
            )
            imported_count += set_imported
            failed_count += set_failed
        
        # ШАГ 4: Обновление пользовательских правил в обычном шаблоне
        if rules_from_policy:
            print(f"\n  ШАГ 4: Обновление пользовательских правил в шаблоне политики...")
            policy_imported, policy_failed = self._update_user_rules_in_policy_template(
                template_id, rules_from_policy, action_mapping, preserve_state
            )
            imported_count += policy_imported
            failed_count += policy_failed
        
        return imported_count, failed_count
    
    def _import_rules_from_user_rules_set(self, template_id, rules_data, action_mapping, preserve_state=True):
        """Импортирует правила из наборов пользовательских правил через RulesManager"""
        imported_count = 0
        failed_count = 0
        
        # Используем RulesManager для копирования пользовательских правил
        from rules_manager import RulesManager
        rules_manager = RulesManager(self.api_client)
        
        # Создаем временную директорию для экспорта пользовательских правил
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Сохраняем пользовательские правила в файлы
            user_rules_files = []
            for i, rule_data in enumerate(rules_data, 1):
                rule_name = rule_data.get('name', f'Пользовательское правило {i}')
                
                # Подготавливаем данные для экспорта
                export_rule_data = {
                    'rule_data': rule_data,
                    'actions_info': {},
                    'export_metadata': {
                        'export_time': datetime.datetime.now().isoformat(),
                        'rule_name': rule_name,
                        'preserve_state': preserve_state,
                        'rule_enabled': rule_data.get('enabled', True)
                    }
                }
                
                # Добавляем информацию о действиях
                original_actions = rule_data.get('actions', [])
                if original_actions:
                    all_actions = self.get_available_actions()
                    if all_actions:
                        actions_info = {}
                        for action in all_actions:
                            if action.get('id') in original_actions:
                                actions_info[str(action.get('id'))] = {
                                    'name': action.get('name'),
                                    'type_id': action.get('type_id'),
                                    'configuration': action.get('configuration')
                                }
                        export_rule_data['actions_info'] = actions_info
                
                # Сохраняем в файл
                safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in rule_name)
                safe_name = safe_name.replace(' ', '_')
                filename = f"{safe_name}_with_actions.ptafpro"
                filepath = os.path.join(temp_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_rule_data, f, ensure_ascii=False, indent=2)
                
                user_rules_files.append(filepath)
                print(f"    [{i}/{len(rules_data)}] Правило '{rule_name}' подготовлено для импорта")
            
            # Импортируем пользовательские правила с использованием action_mapping
            print(f"\n    Импорт пользовательских правил через RulesManager...")
            
            for file_path in user_rules_files:
                filename = os.path.basename(file_path)
                print(f"      Импорт файла: {filename}")
                
                # Используем import_single_rule_with_actions из RulesManager
                success = rules_manager.import_single_rule_with_actions(
                    file_path, action_mapping, False, preserve_state, None
                )
                
                if success:
                    imported_count += 1
                    print(f"      ✅ Правило успешно импортировано")
                else:
                    failed_count += 1
                    print(f"      ✗ Ошибка при импорте правила")
            
        except Exception as e:
            print(f"      ✗ Ошибка при импорте пользовательских правил: {e}")
            failed_count = len(rules_data)
        finally:
            # Очищаем временные файлы
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
        
        return imported_count, failed_count
    
    def _update_user_rules_in_policy_template(self, template_id, rules_data, action_mapping, preserve_state=True):
        """Обновляет пользовательские правила в обычном шаблоне через PATCH"""
        imported_count = 0
        failed_count = 0
        
        # Получаем текущие правила в шаблоне
        existing_rules = self.get_policy_user_rules_in_template(template_id)
        if not existing_rules:
            print(f"    ✗ Не найдено правил в шаблоне")
            return 0, len(rules_data)
        
        # Создаем словарь для быстрого поиска правил по имени
        existing_rules_dict = {rule.get('name'): rule for rule in existing_rules}
        
        for i, rule_data in enumerate(rules_data, 1):
            rule_name = rule_data.get('name', f'Пользовательское правило {i}')
            
            print(f"    [{i}/{len(rules_data)}] Обновление правила: {rule_name}")
            
            # Ищем правило в целевом шаблоне по имени
            if rule_name not in existing_rules_dict:
                print(f"      ✗ Правило '{rule_name}' не найдено в целевом шаблоне")
                failed_count += 1
                continue
            
            target_rule = existing_rules_dict[rule_name]
            target_rule_id = target_rule.get('id')
            
            if not target_rule_id:
                print(f"      ✗ У правила '{rule_name}' нет ID")
                failed_count += 1
                continue
            
            # Подготавливаем данные для PATCH запроса
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
                
                if 'configuration' not in update_data:
                    update_data['configuration'] = {}
                update_data['configuration']['actions'] = mapped_actions
            
            # Сохраняем состояние, если нужно
            if 'enabled' in rule_data and preserve_state:
                update_data['enabled'] = rule_data['enabled']
                print(f"      Состояние: {'включено' if rule_data['enabled'] else 'выключено'} (сохранено)")
            
            if not update_data:
                print(f"      ⚠️ Нет данных для обновления, пропускаем")
                failed_count += 1
                continue
            
            # Выполняем PATCH запрос для обновления правила
            response = self.api_client.update_policy_user_rule_in_template(
                template_id, target_rule_id, update_data
            )
            
            if response and response.status_code == 200:
                print(f"      ✅ Правило '{rule_name}' успешно обновлено")
                imported_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"      ✗ Ошибка при обновлении правила '{rule_name}': {error_msg}")
                failed_count += 1
        
        return imported_count, failed_count
    
    def import_template(self, file_path, target_tenant_id=None, preserve_state=True):
        """Импортирует шаблон с раздельной обработкой системных и пользовательских правил"""
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
        system_rules_data = import_data.get('system_rules', [])  # Измененные системные правила
        user_rules_data = import_data.get('user_rules', [])      # Пользовательские правила
        related_actions = import_data.get('related_actions', [])
        
        export_info = import_data.get('export_info', {})
        has_user_rules = template_data.get('has_user_rules', False)
        
        print(f"📊 Данные для импорта:")
        print(f"  - Системных правил с изменениями: {len(system_rules_data)}")
        print(f"  - Пользовательских правил: {len(user_rules_data)}")
        print(f"  - Связанных действий: {len(related_actions)}")
        print(f"  - Сохранение состояния: {'Да' if preserve_state else 'Нет'}")
        
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
                print(f"  ✓ Шаблон '{template_name}' создан (ID: {target_template_id})")
            
            print(f"\n3. Импортируем правила...")
            
            # ШАГ 1: Импорт пользовательских правил из наборов
            user_imported, user_failed = 0, 0
            if has_user_rules and user_rules_data:
                user_imported, user_failed = self._import_user_rules_to_template(
                    target_template_id, user_rules_data, action_mapping, preserve_state
                )
            
            # ШАГ 2: Применение изменений к системным правилам
            system_imported, system_failed = 0, 0
            if system_rules_data:
                print(f"\n  ШАГ 2: Применение изменений к системным правилам...")
                system_imported, system_failed = self._import_system_rules_with_overrides(
                    target_template_id, system_rules_data, action_mapping, preserve_state
                )
            
            total_imported = system_imported + user_imported
            total_failed = system_failed + user_failed
            total_rules = len(system_rules_data) + len(user_rules_data)
            
            print(f"\n✅ Импорт завершен!")
            print(f"📊 Результаты:")
            print(f"  - Всего правил: {total_rules}")
            print(f"  - Успешно обработано: {total_imported}")
            print(f"    • Изменения в системных правилах: {system_imported}")
            print(f"    • Пользовательские правила: {user_imported}")
            print(f"  - Не удалось обработать: {total_failed}")
            
            return total_imported > 0
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
    
    # ==================== КОПИРОВАНИЕ МЕЖДУ ТЕНАНТАМИ ====================
    
    def copy_template_to_another_tenant(self, source_template_id, target_tenant_id, preserve_state=True):
        """Копирует шаблон в другой тенант с раздельной обработкой правил"""
        print(f"\nКопирование шаблона в другой тенант...")
        
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # Переключаемся на исходный тенант
            self.api_client.auth_manager.tenant_id = original_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("❌ Не удалось переключиться на исходный тенант")
                return False
            
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            
            # Экспортируем шаблон с разделением на системные и пользовательские правила
            print("Экспорт шаблона с разделением правил...")
            export_file = self.export_template(source_template_id, temp_dir, include_user_rules=True)
            
            if not export_file:
                print("❌ Не удалось экспортировать шаблон")
                # Очищаем временную директорию
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            # Импортируем в целевой тенант с сохранением состояния
            result = self.import_template(export_file, target_tenant_id, preserve_state)
            
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
        export_file = self.export_template(template_id, export_dir, include_user_rules=True)
        
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
        
        # Спрашиваем про сохранение состояния
        preserve_choice = input("\nСохранить исходное состояние правил (включено/выключено)? (y/n): ").lower()
        preserve_state = preserve_choice == 'y'
        
        if preserve_state:
            print("Состояние правил будет сохранено")
        else:
            print("Все правила будут включены")
        
        print(f"\nИмпорт шаблона в тенант '{target_tenant_name}'...")
        result = self.import_template(file_path, target_tenant_id, preserve_state)
        
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
        
        # Спрашиваем про сохранение состояния
        print("\n📋 Настройки копирования:")
        print("Шаблон будет скопирован со всеми правилами и действиями")
        print("Пользовательские правила копируются отдельно (как в 'Копирование правил')")
        print("Изменения в системных правилах применяются к существующим правилам")
        
        preserve_choice = input("\nСохранить исходное состояние правил (включено/выключено)? (y/n): ").lower()
        preserve_state = preserve_choice == 'y'
        
        if preserve_state:
            print("Состояние правил будет сохранено")
        else:
            print("Все правила будут включены")
        
        confirm = input(f"\nВы уверены, что хотите скопировать шаблон '{template_name}' из тенанта '{source_tenant_name}' в тенант '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            return
        
        print(f"\nКопирование шаблона '{template_name}' из '{source_tenant_name}' в '{target_tenant_name}'...")
        result = self.copy_template_to_another_tenant(template_id, target_tenant_id, preserve_state)
        
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
            export_file = self.export_template(template_id, temp_dir, include_user_rules=True)
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
            
            # Импортируем правила в новый шаблон
            result = self.import_template(export_file, self.api_client.auth_manager.tenant_id, preserve_state=True)
            
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
            export_file = self.export_template(template_id, temp_dir, include_user_rules=True)
            if export_file:
                # Модифицируем экспортированные данные для нового шаблона
                with open(export_file, 'r', encoding='utf-8') as f:
                    export_data = json.load(f)
                
                export_data['template']['id'] = new_template_id
                export_data['template']['name'] = new_name
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                result = self.import_template(export_file, self.api_client.auth_manager.tenant_id, preserve_state=True)
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