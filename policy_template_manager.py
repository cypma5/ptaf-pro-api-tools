# policy_template_manager.py (очищенная версия)
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

    def create_rule(self, template_id, rule_data):
        """Создает правило в шаблоне (для совместимости с _import_user_rules_changes)."""
        return self.api_client.create_user_rule(template_id, rule_data)
    
    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет правило"""
        return self.api_client.update_template_rule(template_id, rule_id, update_data)
    
    def update_user_rule(self, template_id, rule_id, update_data):
        """Обновляет пользовательское правило"""
        return self.api_client.update_user_rule(template_id, rule_id, update_data)
    
    def update_rule_aggregation(self, template_id, rule_id, aggregation_data):
        """Обновляет настройки агрегации"""
        return self.api_client.update_template_rule_aggregation(template_id, rule_id, aggregation_data)

    def _print_rule_update_error(self, response, update_data, context="правила", error_verb="обновлении"):
        """Выводит подробную информацию об ошибке обновления/создания правила: запрос, код, тело ответа."""
        print(f"      ✗ Ошибка при {error_verb} {context}:")
        if response is not None:
            code = getattr(response, "status_code", None)
            body = getattr(response, "text", None) or "(пусто)"
            req = getattr(response, "request", None)
            method = req.method if req else "PATCH"
            url = req.url if req else ""
            print(f"        REQUEST: {method} {url}")
            try:
                print(f"        Request body: {json.dumps(update_data, ensure_ascii=False)}")
            except Exception:
                print(f"        Request body: {update_data}")
            print(f"        Код ответа: {code}")
            print(f"        Тело ответа: {body}")
        else:
            print(f"        Неизвестная ошибка (нет ответа от сервера)")
            try:
                print(f"        Request body: {json.dumps(update_data, ensure_ascii=False)}")
            except Exception:
                print(f"        Request body: {update_data}")

    def _print_aggregation_update_error(self, agg_response, aggregation_data):
        """Выводит подробную информацию об ошибке обновления агрегации: запрос, код, тело ответа."""
        print(f"      ⚠️ Ошибка при обновлении агрегации:")
        if agg_response is not None:
            code = getattr(agg_response, "status_code", None)
            body = getattr(agg_response, "text", None) or "(пусто)"
            req = getattr(agg_response, "request", None)
            method = req.method if req else "PATCH"
            url = req.url if req else ""
            print(f"        REQUEST: {method} {url}")
            try:
                print(f"        Request body: {json.dumps(aggregation_data, ensure_ascii=False)}")
            except Exception:
                print(f"        Request body: {aggregation_data}")
            print(f"        Код ответа: {code}")
            print(f"        Тело ответа: {body}")
        else:
            print(f"        Неизвестная ошибка (нет ответа от сервера)")
            try:
                print(f"        Request body: {json.dumps(aggregation_data, ensure_ascii=False)}")
            except Exception:
                print(f"        Request body: {aggregation_data}")
    
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
        has_user_rules = template_details.get('has_user_rules', False)
        
        if not has_user_rules:
            print("Шаблон не поддерживает пользовательские правила")
            return []
        
        user_rules = []
        
        if template_type == 'with_user_rules':
            # Это отдельный набор пользовательских правил
            print("Шаблон типа 'with_user_rules' - получение правил из набора...")
            user_rules = self.get_user_rules(template_id)
        else:
            # Это обычный шаблон с пользовательскими правилами
            print("Обычный шаблон с пользовательскими правилами - получение правил...")
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
                rule_details['has_user_rules'] = has_user_rules
                full_rules_data.append(rule_details)
        
        return full_rules_data
    
    def _get_user_rule_names_enabled_in_policies(self, template_id):
        """
        Возвращает множество имён пользовательских правил, которые включены (enabled=True)
        в политике безопасности хотя бы одного веб-приложения с данным шаблоном.
        """
        enabled_names = set()
        try:
            apps_resp = self.api_client.get_applications()
            applications = self._parse_response_items(apps_resp) or []
            for app in applications:
                if app.get('policy_template_id') != template_id:
                    continue
                policy_id = app.get('policy_id')
                if not policy_id:
                    continue
                rules_resp = self.api_client.get_policy_user_rules(policy_id)
                rules = self._parse_response_items(rules_resp) or []
                for r in rules:
                    if r.get('enabled') is True:
                        name = r.get('name')
                        if name:
                            enabled_names.add(name)
        except Exception as e:
            print(f"  ⚠️ Не удалось получить состояние правил в политиках приложений: {e}")
            return None
        return enabled_names
    
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
            # Переносим только правила, включённые хотя бы в одном месте:
            # 1) в наборе пользовательских правил, 2) в шаблоне политики, 3) в политике безопасности приложения
            enabled_in_policies = self._get_user_rule_names_enabled_in_policies(template_id)
            if user_rules_data:
                total = len(user_rules_data)
                def should_transfer_rule(r):
                    name = r.get('name') or r.get('original_name')
                    # Включено в наборе или в шаблоне (enabled в деталях правила)
                    if r.get('enabled') is True:
                        return True
                    # Включено в политике безопасности хотя бы одного приложения
                    if enabled_in_policies is not None and name and name in enabled_in_policies:
                        return True
                    return False
                user_rules_data = [r for r in user_rules_data if should_transfer_rule(r)]
                skipped = total - len(user_rules_data)
                if skipped > 0:
                    print(f"  Пропущено пользовательских правил (нигде не включены): {skipped}")
                print(f"  К переносу пользовательских правил (вкл. в наборе/шаблоне/политике): {len(user_rules_data)}")
        
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
            created_count = 0
            found_count = 0
            
            print(f"  Создание маппинга для {len(source_actions)} действий...")
            
            for i, action in enumerate(source_actions, 1):
                original_action_id = action.get('id')
                action_name = action.get('name', f'Действие {i}')
                action_type_id = action.get('type_id')
                
                # Пропускаем системные действия
                if action.get('is_system', True):
                    print(f"    [{i}] ⚠️ Пропускаем системное действие: {action_name}")
                    continue
                
                print(f"    [{i}] Обработка действия: {action_name}")
                
                # Ищем или создаем действие в целевом тенанте
                target_action = actions_manager.find_or_create_action(action)
                
                if target_action:
                    new_action_id = target_action.get('id')
                    action_mapping[original_action_id] = new_action_id
                    
                    if target_action.get('id') == original_action_id:
                        found_count += 1
                        print(f"      ✓ Найдено существующее действие (ID: {new_action_id})")
                    else:
                        created_count += 1
                        print(f"      ✓ Создано новое действие (ID: {new_action_id})")
                else:
                    print(f"      ✗ Не удалось найти или создать действие")
            
            print(f"  ✓ Маппинг действий создан:")
            print(f"     - Найдено существующих: {found_count}")
            print(f"     - Создано новых: {created_count}")
            print(f"     - Всего в маппинге: {len(action_mapping)}")
            
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
            if (rule.get('name') == rule_name and 
                rule.get('is_system', False) and 
                not rule.get('has_overrides', False)):
                return rule
        
        # Ищем по частичному совпадению имени среди системных правил
        for rule in rules:
            if (rule_name in rule.get('name', '') and 
                rule.get('is_system', False) and 
                not rule.get('has_overrides', False)):
                return rule
        
        # Ищем среди всех правил (включая с has_overrides)
        for rule in rules:
            if (rule_name in rule.get('name', '') and 
                rule.get('is_system', False)):
                return rule
        
        return None

    def _import_system_rules_with_overrides(self, template_id, system_rules_data, action_mapping, 
                                            global_list_mapping=None, preserve_state=True):
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
            
            # 1. Обновляем действия с использованием маппинга
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
            
            # 2. Сохраняем состояние, если нужно
            if 'enabled' in rule_data and preserve_state:
                update_data['enabled'] = rule_data['enabled']
                print(f"      Состояние: {'включено' if rule_data['enabled'] else 'выключено'}")
            
            # 3. Обновляем переменные
            if 'variables' in rule_data and rule_data['variables']:
                variables_copy = rule_data['variables'].copy()
                
                # Применяем маппинг глобальных списков в переменных
                if global_list_mapping:
                    # Динамические глобальные списки
                    if 'dynamic_global_lists' in variables_copy:
                        dgl = variables_copy['dynamic_global_lists']
                        if 'value' in dgl and isinstance(dgl['value'], list):
                            mapped_dgl = []
                            for list_id in dgl['value']:
                                if str(list_id) in global_list_mapping:
                                    mapped_dgl.append(global_list_mapping[str(list_id)])
                                else:
                                    mapped_dgl.append(list_id)
                            dgl['value'] = mapped_dgl
                            print(f"      Обновлены динамические глобальные списки: {len(mapped_dgl)}")
                
                update_data['variables'] = variables_copy
                print(f"      Обновлены переменные")
            
            # 4. Обновляем конфигурацию (если есть)
            if 'configuration' in rule_data and rule_data['configuration']:
                config_copy = rule_data['configuration'].copy()
                
                # Применяем маппинг глобальных списков в конфигурации
                if global_list_mapping:
                    # В параметрах конфигурации
                    if 'parameters' in config_copy and isinstance(config_copy['parameters'], list):
                        for param in config_copy['parameters']:
                            if 'global_list_id' in param:
                                gl_id = param['global_list_id']
                                if str(gl_id) in global_list_mapping:
                                    param['global_list_id'] = global_list_mapping[str(gl_id)]
                    
                    # В переменных конфигурации
                    if 'variables' in config_copy:
                        variables = config_copy['variables']
                        if 'dynamic_global_lists' in variables:
                            dgl = variables['dynamic_global_lists']
                            if 'value' in dgl and isinstance(dgl['value'], list):
                                mapped_dgl = []
                                for list_id in dgl['value']:
                                    if str(list_id) in global_list_mapping:
                                        mapped_dgl.append(global_list_mapping[str(list_id)])
                                    else:
                                        mapped_dgl.append(list_id)
                                dgl['value'] = mapped_dgl
                
                update_data['configuration'] = config_copy
                print(f"      Обновлена конфигурация")
            
            if not update_data:
                print(f"      ⚠️ Нет данных для обновления, пропускаем")
                failed_count += 1
                continue
            
            # Обновляем правило
            response = self.update_rule(template_id, target_rule_id, update_data)
            
            if response and response.status_code == 200:
                print(f"      ✅ Изменения успешно применены")
                
                # 5. Обновляем настройки агрегации если есть и агрегация включена
                if 'aggregation' in rule_data and rule_data['aggregation']:
                    aggregation_data = rule_data['aggregation'].copy()
                    if aggregation_data.get('enabled') is False:
                        print(f"      Агрегация выключена — обновление агрегации пропущено")
                    else:
                        # Применяем маппинг глобальных списков в агрегации (ключи в маппинге — строки)
                        if global_list_mapping and 'global_list_id' in aggregation_data:
                            gl_id = aggregation_data['global_list_id']
                            mapped_id = global_list_mapping.get(str(gl_id), gl_id)
                            aggregation_data['global_list_id'] = mapped_id
                            if mapped_id != gl_id:
                                print(f"      Обновлен глобальный список в агрегации: {gl_id} -> {mapped_id}")
                            elif global_list_mapping:
                                print(f"      ⚠ Глобальный список {gl_id} не найден в маппинге, отправка как есть (возможна ошибка reference_not_exist)")
                        
                        agg_response = self.update_rule_aggregation(template_id, target_rule_id, aggregation_data)
                        
                        if agg_response and agg_response.status_code == 200:
                            print(f"      ✅ Настройки агрегации обновлены")
                        else:
                            self._print_aggregation_update_error(agg_response, aggregation_data)
                
                imported_count += 1
            else:
                self._print_rule_update_error(response, update_data, "правила (системное)")
                failed_count += 1
        
        return imported_count, failed_count

    def _import_user_rules_from_file_data(self, template_id, user_rules_data, action_mapping, global_list_mapping,
                                          preserve_state):
        """Создаёт в целевом шаблоне только правила из user_rules_data (импорт из файла), без экспорта всего набора."""
        if not user_rules_data:
            return 0, 0
        imported_count = 0
        failed_count = 0
        print(f"\n  Создание пользовательских правил из файла ({len(user_rules_data)} правил)...")
        existing = self.get_policy_user_rules_in_template(template_id) or []
        existing_by_name = {r.get('name'): r for r in existing if r.get('name')}
        for i, rule_data in enumerate(user_rules_data, 1):
            rule_name = rule_data.get('name', f'Пользовательское правило {i}')
            if rule_name in existing_by_name:
                print(f"    [{i}/{len(user_rules_data)}] Правило '{rule_name}' уже есть в шаблоне, пропускаем создание")
                continue
            create_data = rule_data.copy()
            for field in ('id', 'original_id', 'original_name', 'template_type', 'has_user_rules'):
                create_data.pop(field, None)
            actions = create_data.get('actions') or (create_data.get('configuration') or {}).get('actions') or []
            if actions and action_mapping:
                mapped = [action_mapping.get(str(aid), aid) for aid in actions]
                if 'configuration' not in create_data:
                    create_data['configuration'] = {}
                create_data['configuration']['actions'] = mapped
            if global_list_mapping and create_data.get('configuration'):
                config = create_data['configuration']
                if config.get('variables', {}).get('dynamic_global_lists', {}).get('value'):
                    dgl = config['variables']['dynamic_global_lists']
                    dgl['value'] = [global_list_mapping.get(str(lid), lid) for lid in dgl['value']]
                for param in (config.get('parameters') or []):
                    if 'global_list_id' in param and param['global_list_id']:
                        param['global_list_id'] = global_list_mapping.get(str(param['global_list_id']), param['global_list_id'])
            if global_list_mapping and create_data.get('aggregation', {}).get('global_list_id'):
                create_data['aggregation']['global_list_id'] = global_list_mapping.get(
                    str(create_data['aggregation']['global_list_id']), create_data['aggregation']['global_list_id'])
            if preserve_state and 'enabled' in rule_data:
                create_data['enabled'] = rule_data['enabled']
            template_type = rule_data.get('template_type', 'user')
            try:
                if template_type == 'with_user_rules':
                    resp = self.create_user_rule(template_id, create_data)
                else:
                    resp = self.create_rule(template_id, create_data)
                if resp and resp.status_code in (200, 201):
                    if preserve_state and 'enabled' in rule_data and resp.status_code == 201:
                        try:
                            created = resp.json() or {}
                            rid = created.get('id')
                            if rid and template_type != 'with_user_rules':
                                self.update_policy_user_rule_in_template(template_id, rid, {"enabled": rule_data["enabled"]})
                            elif rid:
                                self.update_user_rule(template_id, rid, {"enabled": rule_data["enabled"]})
                        except Exception:
                            pass
                    print(f"    [{i}/{len(user_rules_data)}] ✅ Правило '{rule_name}' создано")
                    imported_count += 1
                else:
                    msg = getattr(resp, 'text', None) or 'Неизвестная ошибка'
                    print(f"    [{i}/{len(user_rules_data)}] ✗ Ошибка создания '{rule_name}': {msg}")
                    failed_count += 1
            except Exception as e:
                print(f"    [{i}/{len(user_rules_data)}] ✗ Ошибка создания '{rule_name}': {e}")
                failed_count += 1
        return imported_count, failed_count

    def _import_user_rules_to_template(self, template_id, user_rules_data, action_mapping, preserve_state=True,
                                      source_tenant_id=None, target_tenant_id=None, use_file_data_only=False,
                                      global_list_mapping=None):
        """Импортирует пользовательские правила в шаблон.

        Если use_file_data_only=True (импорт из файла), создаются только правила из user_rules_data
        в целевом тенанте, без переключения на исходный и без экспорта всего набора.
        """
        if not user_rules_data:
            return 0, 0
        
        # Режим «только из файла»: создаём в целевом тенанте только правила из user_rules_data
        if use_file_data_only:
            return self._import_user_rules_from_file_data(
                template_id, user_rules_data, action_mapping, global_list_mapping or {}, preserve_state
            )
        
        print(f"\n  Используем логику 'Копирование правил в другой тенант'...")
        print(f"    Сохранение связей с действиями: Да")
        print(f"    Сохранение состояния правил: {'Да' if preserve_state else 'Нет'}")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # ШАГ 1: Получаем ID исходного набора правил
            if not source_tenant_id:
                print("    ✗ Не указан исходный тенант")
                return 0, len(user_rules_data)
            
            print(f"    🔀 Переключаемся на исходный тенант: {source_tenant_id}")
            self.api_client.auth_manager.tenant_id = source_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("    ✗ Не удалось переключиться на исходный тенант")
                return 0, 0
            
            # Получаем все наборы пользовательских правил в исходном тенанте
            user_rules_sets = self.get_templates_with_user_rules()
            if not user_rules_sets:
                print("    ✗ Не найдено наборов пользовательских правил в исходном тенанте")
                return 0, len(user_rules_data)
            
            source_set_id = user_rules_sets[0].get('id')
            source_set_name = user_rules_sets[0].get('name', 'Без названия')
            print(f"    ✓ Найден исходный набор правил: '{source_set_name}' (ID: {source_set_id})")
            
            # ШАГ 2: Используем RulesManager для копирования ВСЕХ правил из набора
            from rules_manager import RulesManager
            rules_manager = RulesManager(self.api_client)
            
            # Создаем временную директорию для экспорта ВСЕХ правил
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Экспортируем ВСЕ правила из исходного набора
                print(f"    Экспорт всех правил из набора '{source_set_name}'...")
                export_result = rules_manager.export_rules_with_actions(temp_dir, preserve_state)
                
                if not export_result:
                    print("    ✗ Не удалось экспортировать правила из исходного набора")
                    return 0, len(user_rules_data)
                
                print(f"    ✓ Правила успешно экспортированы во временную директорию")
                
                # ШАГ 3: Переключаемся на целевой тенант
                if target_tenant_id and target_tenant_id != self.api_client.auth_manager.tenant_id:
                    print(f"    🔀 Переключаемся на целевой тенант: {target_tenant_id}")
                    self.api_client.auth_manager.tenant_id = target_tenant_id
                    if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                        print("    ✗ Не удалось переключиться на целевой тенант")
                        return 0, 0
                
                # ШАГ 4: Импортируем все правила в целевой тенант
                print(f"    Импорт всех правил в целевой тенант...")
                
                success_count = 0
                total_files = 0
                
                # Получаем список экспортированных файлов
                for filename in os.listdir(temp_dir):
                    if filename.endswith('.ptafpro'):
                        total_files += 1
                        file_path = os.path.join(temp_dir, filename)
                        
                        print(f"      Импорт файла {filename} ({total_files})...")
                        
                        ret = rules_manager.import_single_rule_with_actions(
                            file_path, action_mapping, False, preserve_state, None
                        )
                        success = (ret[0] if isinstance(ret, tuple) else ret)
                        if success:
                            success_count += 1
                            print(f"      ✅ Правило успешно импортировано")
                        else:
                            print(f"      ✗ Ошибка при импорте правила")
                
                return success_count, total_files - success_count
                
            except Exception as e:
                print(f"      ✗ Ошибка при копировании правил: {e}")
                return 0, len(user_rules_data)
            finally:
                # Очищаем временные файлы
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    print(f"      ⚠️ Не удалось удалить временную директорию: {e}")
                    pass
            
        finally:
            # Восстанавливаем оригинальный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)

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

    def update_policy_user_rule_in_template(self, template_id, rule_id, update_data):
        """Обновляет пользовательское правило внутри обычного шаблона"""
        return self.api_client.update_policy_user_rule_in_template(template_id, rule_id, update_data)


    def _import_user_rules_changes(self, target_template_id, user_rules_data, action_mapping, 
                                global_list_mapping=None, preserve_state=True):
        """Применяет изменения к пользовательским правилам в целевом шаблоне"""
        if not user_rules_data:
            return 0, 0  # imported_count, failed_count
        
        imported_count = 0
        failed_count = 0
        
        print(f"\n  Импорт изменений в {len(user_rules_data)} пользовательских правил:")
        
        for i, rule_data in enumerate(user_rules_data, 1):
            rule_name = rule_data.get('name', f'Пользовательское правило {i}')
            original_id = rule_data.get('original_id')
            template_type = rule_data.get('template_type', 'user')
            has_user_rules = rule_data.get('has_user_rules', False)
            
            print(f"    [{i}/{len(user_rules_data)}] Правило: {rule_name}")
            
            # ШАГ 1: Поиск существующего правила в целевом тенанте
            target_rule = None
            
            if template_type == 'with_user_rules':
                # Это отдельный набор пользовательских правил
                # Получаем все правила из набора
                user_rules = self.get_user_rules(target_template_id)
                if user_rules:
                    # Ищем по original_id или имени
                    for rule in user_rules:
                        if (rule.get('id') == original_id or 
                            rule.get('name') == rule_name):
                            target_rule = rule
                            break
            else:
                # Это обычный шаблон с пользовательскими правилами
                # Получаем пользовательские правила внутри шаблона
                user_rules = self.get_policy_user_rules_in_template(target_template_id)
                if user_rules:
                    # Ищем по original_id или имени
                    for rule in user_rules:
                        if (rule.get('id') == original_id or 
                            rule.get('name') == rule_name):
                            target_rule = rule
                            break
            
            # ШАГ 2: Если правило не найдено, создаем новое
            if not target_rule:
                print(f"      ⚠️ Правило не найдено в целевом тенанте, создаем новое...")
                
                # Подготавливаем данные для создания
                create_data = rule_data.copy()
                
                # Удаляем системные поля
                for field in ['id', 'original_id', 'original_name', 
                            'template_type', 'has_user_rules']:
                    if field in create_data:
                        del create_data[field]
                
                # Применяем маппинг действий
                if 'actions' in create_data:
                    mapped_actions = []
                    for action_id in create_data['actions']:
                        if str(action_id) in action_mapping:
                            mapped_actions.append(action_mapping[str(action_id)])
                        else:
                            mapped_actions.append(action_id)
                    create_data['actions'] = mapped_actions
                
                # Применяем маппинг глобальных списков
                if global_list_mapping:
                    # В конфигурации
                    if 'configuration' in create_data:
                        config = create_data['configuration']
                        # Обработка variables
                        if 'variables' in config:
                            variables = config['variables']
                            # Динамические глобальные списки
                            if 'dynamic_global_lists' in variables:
                                dgl = variables['dynamic_global_lists']
                                if 'value' in dgl and isinstance(dgl['value'], list):
                                    mapped_dgl = []
                                    for list_id in dgl['value']:
                                        if str(list_id) in global_list_mapping:
                                            mapped_dgl.append(global_list_mapping[str(list_id)])
                                        else:
                                            mapped_dgl.append(list_id)
                                    dgl['value'] = mapped_dgl
                    
                    # В агрегации
                    if 'aggregation' in create_data and global_list_mapping:
                        aggregation = create_data['aggregation']
                        if 'global_list_id' in aggregation:
                            gl_id = aggregation['global_list_id']
                            aggregation['global_list_id'] = global_list_mapping.get(str(gl_id), gl_id)
                
                # Состояние (enabled): при сохранении берём из исходных данных, иначе включаем
                if preserve_state and 'enabled' in rule_data:
                    create_data['enabled'] = rule_data['enabled']
                elif not preserve_state:
                    create_data['enabled'] = True
                
                # Создаем правило в зависимости от типа шаблона
                if template_type == 'with_user_rules':
                    response = self.create_user_rule(target_template_id, create_data)
                else:
                    # Для обычного шаблона используем создание правила
                    create_response = self.create_rule(target_template_id, create_data)
                    
                    # Проверяем ответ
                    if create_response and create_response.status_code == 201:
                        # Получаем ID созданного правила
                        new_rule_data = create_response.json()
                        rule_id = new_rule_data.get('id')
                        
                        # Если нужно, обновляем пользовательское правило
                        if 'is_user_rule' in create_data and create_data['is_user_rule']:
                            # Преобразуем в пользовательское правило
                            update_data = {
                                "enabled": create_data.get('enabled', True),
                                "configuration": create_data.get('configuration', {})
                            }
                            response = self.update_policy_user_rule_in_template(
                                target_template_id, rule_id, update_data
                            )
                        else:
                            response = create_response
                    else:
                        response = create_response
                
                if response and response.status_code in [200, 201]:
                    # После создания при необходимости явно выставляем состояние (API может игнорировать enabled при POST)
                    if preserve_state and 'enabled' in rule_data:
                        try:
                            created = response.json() if hasattr(response, 'json') else {}
                            new_rule_id = created.get('id')
                            if new_rule_id:
                                if template_type == 'with_user_rules':
                                    self.update_user_rule(target_template_id, new_rule_id, {"enabled": rule_data["enabled"]})
                                else:
                                    self.update_policy_user_rule_in_template(
                                        target_template_id, new_rule_id, {"enabled": rule_data["enabled"]}
                                    )
                                print(f"      Состояние: {'включено' if rule_data['enabled'] else 'выключено'}")
                        except Exception as e:
                            print(f"      ⚠️ Не удалось выставить состояние правила: {e}")
                    print(f"      ✅ Правило '{rule_name}' успешно создано")
                    imported_count += 1
                    continue
                else:
                    self._print_rule_update_error(response, create_data, "правила", error_verb="создании")
                    failed_count += 1
                    continue
            
            # ШАГ 3: Обновление существующего правила
            target_rule_id = target_rule.get('id')
            print(f"      ✓ Найдено правило в целевом тенанте (ID: {target_rule_id})")
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            # 1. Обновляем действия с использованием маппинга
            original_actions = rule_data.get('actions', [])
            if original_actions:
                mapped_actions = []
                for action_id in original_actions:
                    if str(action_id) in action_mapping:
                        mapped_actions.append(action_mapping[str(action_id)])
                    else:
                        mapped_actions.append(action_id)  # Для системных действий
                
                update_data['actions'] = mapped_actions
                print(f"      Обновлено {len(mapped_actions)} действий")
            
            # 2. Обновляем конфигурацию
            if 'configuration' in rule_data:
                config_copy = rule_data['configuration'].copy()
                
                # Применяем маппинг глобальных списков в конфигурации
                if global_list_mapping and 'variables' in config_copy:
                    variables = config_copy['variables']
                    if 'dynamic_global_lists' in variables:
                        dgl = variables['dynamic_global_lists']
                        if 'value' in dgl and isinstance(dgl['value'], list):
                            mapped_dgl = []
                            for list_id in dgl['value']:
                                if str(list_id) in global_list_mapping:
                                    mapped_dgl.append(global_list_mapping[str(list_id)])
                                else:
                                    mapped_dgl.append(list_id)
                            dgl['value'] = mapped_dgl
                
                update_data['configuration'] = config_copy
                print(f"      Обновлена конфигурация")
            
            # 3. Сохраняем состояние, если нужно
            if 'enabled' in rule_data and preserve_state:
                update_data['enabled'] = rule_data['enabled']
                print(f"      Состояние: {'включено' if rule_data['enabled'] else 'выключено'}")
            
            # 4. Обновляем переменные (если не в конфигурации)
            if 'variables' in rule_data and rule_data['variables']:
                variables_copy = rule_data['variables'].copy()
                
                # Применяем маппинг глобальных списков в переменных
                if global_list_mapping and 'dynamic_global_lists' in variables_copy:
                    dgl = variables_copy['dynamic_global_lists']
                    if 'value' in dgl and isinstance(dgl['value'], list):
                        mapped_dgl = []
                        for list_id in dgl['value']:
                            if str(list_id) in global_list_mapping:
                                mapped_dgl.append(global_list_mapping[str(list_id)])
                            else:
                                mapped_dgl.append(list_id)
                        dgl['value'] = mapped_dgl
                
                update_data['variables'] = variables_copy
                print(f"      Обновлены переменные")
            
            # 5. Обновляем агрегацию (только если агрегация включена)
            if 'aggregation' in rule_data and rule_data['aggregation']:
                aggregation_copy = rule_data['aggregation'].copy()
                if aggregation_copy.get('enabled') is False:
                    print(f"      Агрегация выключена — обновление агрегации пропущено")
                else:
                    # Применяем маппинг глобальных списков в агрегации (ключи в маппинге — строки)
                    if global_list_mapping and 'global_list_id' in aggregation_copy:
                        gl_id = aggregation_copy['global_list_id']
                        mapped_id = global_list_mapping.get(str(gl_id), gl_id)
                        aggregation_copy['global_list_id'] = mapped_id
                        if mapped_id == gl_id and global_list_mapping:
                            print(f"      ⚠ Глобальный список {gl_id} не найден в маппинге при обновлении агрегации")
                    
                    # Для обновления агрегации нужен отдельный запрос
                    agg_response = self.update_rule_aggregation(
                        target_template_id, target_rule_id, aggregation_copy
                    )
                    
                    if agg_response and agg_response.status_code == 200:
                        print(f"      ✅ Настройки агрегации обновлены")
                    else:
                        self._print_aggregation_update_error(agg_response, aggregation_copy)
            
            if not update_data:
                print(f"      ⚠️ Нет данных для обновления, пропускаем")
                failed_count += 1
                continue
            
            # ШАГ 4: Отправляем запрос на обновление
            if template_type == 'with_user_rules':
                response = self.update_user_rule(target_template_id, target_rule_id, update_data)
            else:
                # Для обычного шаблона
                if target_rule.get('is_user_rule', False):
                    response = self.update_policy_user_rule_in_template(
                        target_template_id, target_rule_id, update_data
                    )
                else:
                    response = self.update_rule(target_template_id, target_rule_id, update_data)
            
            if response and response.status_code == 200:
                print(f"      ✅ Изменения успешно применены")
                imported_count += 1
            else:
                self._print_rule_update_error(response, update_data, "правила (пользовательское)")
                failed_count += 1
        
        return imported_count, failed_count


    def import_template(self, file_path, target_tenant_id=None, preserve_state=True):
        """Импортирует шаблон с раздельной обработкой всех типов правил"""
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
        related_global_lists = import_data.get('related_global_lists', [])
        
        export_info = import_data.get('export_info', {})
        has_user_rules = template_data.get('has_user_rules', False)
        
        # Извлекаем исходный тенант из метаданных экспорта
        source_tenant_id = export_info.get('tenant_id')
        
        print(f"📊 Данные для импорта:")
        print(f"  - Системных правил с изменениями: {len(system_rules_data)}")
        print(f"  - Пользовательских правил: {len(user_rules_data)}")
        print(f"  - Связанных действий: {len(related_actions)}")
        print(f"  - Связанных глобальных списков: {len(related_global_lists)}")
        print(f"  - Сохранение состояния: {'Да' if preserve_state else 'Нет'}")
        if source_tenant_id:
            print(f"  - Исходный тенант: {source_tenant_id}")
        
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
            
            print("\n2. Создаем маппинг глобальных списков...")
            global_list_mapping = self._create_global_list_mapping(related_global_lists, target_tenant_id)
            print(f"  ✓ Создан маппинг для {len(global_list_mapping)} глобальных списков")
            
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
            
            print(f"\n4. Импортируем правила...")
            
            # ШАГ 1: Копирование пользовательских правил через RulesManager
            user_imported_1, user_failed_1 = 0, 0
            if has_user_rules and user_rules_data:
                print(f"\n  ШАГ 1: Копирование пользовательских правил из файла...")
                user_imported_1, user_failed_1 = self._import_user_rules_to_template(
                    target_template_id, user_rules_data, action_mapping, preserve_state,
                    source_tenant_id, target_tenant_id,
                    use_file_data_only=True,
                    global_list_mapping=global_list_mapping
                )
            
            # ШАГ 2: Применение изменений к системным правилам
            system_imported, system_failed = 0, 0
            if system_rules_data:
                print(f"\n  ШАГ 2: Применение изменений к системным правилам...")
                system_imported, system_failed = self._import_system_rules_with_overrides(
                    target_template_id, system_rules_data, action_mapping, 
                    global_list_mapping, preserve_state
                )
            
            # ШАГ 3: Применение изменений к пользовательским правилам
            user_imported_2, user_failed_2 = 0, 0
            if user_rules_data:
                print(f"\n  ШАГ 3: Применение изменений к пользовательским правилам...")
                user_imported_2, user_failed_2 = self._import_user_rules_changes(
                    target_template_id, user_rules_data, action_mapping, 
                    global_list_mapping, preserve_state
                )
            
            # Суммируем результаты
            total_imported = system_imported + user_imported_1 + user_imported_2
            total_failed = system_failed + user_failed_1 + user_failed_2
            num_system = len(system_rules_data)
            num_user = len(user_rules_data)
            total_rules = num_system + num_user
            
            print(f"\n✅ Импорт завершен!")
            print(f"📊 Результаты:")
            print(f"  - Всего записей в файле: {total_rules} (системных с изменениями: {num_system}, пользовательских: {num_user})")
            print(f"  - Успешно обработано: {total_imported}")
            print(f"    • Системные правила: применено изменений {system_imported} из {num_system}")
            print(f"    • Пользовательские правила: создано {user_imported_1}, обновлено {user_imported_2} (всего в файле: {num_user})")
            print(f"  - Не удалось обработать: {total_failed} (системные: {system_failed}, пользовательские: {user_failed_1 + user_failed_2})")
            print(f"  - Маппинг действий: {len(action_mapping)}")
            print(f"  - Маппинг глобальных списков: {len(global_list_mapping)}")
            
            return total_imported > 0
            
        finally:
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)


    def _create_global_list_mapping(self, source_global_lists, target_tenant_id):
        """Создает маппинг ID глобальных списков между тенантами"""
        if not source_global_lists:
            return {}
        
        from global_lists_manager import GlobalListsManager
        lists_manager = GlobalListsManager(self.api_client)
        
        # Сохраняем текущий тенант
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        try:
            # Переключаемся на целевой тенант
            if target_tenant_id and target_tenant_id != original_tenant_id:
                self.api_client.auth_manager.tenant_id = target_tenant_id
                if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                    print(f"❌ Не удалось переключиться на тенант {target_tenant_id}")
                    return {}
            
            global_list_mapping = {}
            created_count = 0
            found_count = 0
            
            print(f"  Создание маппинга для {len(source_global_lists)} глобальных списков...")
            
            for i, gl_list in enumerate(source_global_lists, 1):
                original_list_id = gl_list.get('id')
                list_name = gl_list.get('name', f'Список {i}')
                list_type = gl_list.get('type')
                is_system = gl_list.get('is_system', True)
                
                print(f"    [{i}] Обработка списка: {list_name} ({list_type})" + (" [системный]" if is_system else ""))
                
                # Ищем список в целевом тенанте по имени и типу (включая системные, чтобы маппить source_id -> target_id)
                existing_list = lists_manager.find_list_by_name_and_type_including_system(list_name, list_type)
                
                if existing_list:
                    global_list_mapping[str(original_list_id)] = existing_list.get('id')
                    found_count += 1
                    print(f"      ✓ Найден в целевом тенанте (ID: {existing_list.get('id')})")
                elif is_system:
                    print(f"      ⚠ Системный список не найден в целевом тенанте по имени — маппинг отсутствует")
                else:
                    # Создаем новый список (только для пользовательских)
                    create_data = gl_list.copy()
                    
                    # Удаляем системные поля
                    for field in ['id', 'is_system', 'size', 'updated', 
                                'is_applied', 'is_marked_to_delete']:
                        if field in create_data:
                            del create_data[field]
                    
                    result = lists_manager.create_list_from_data(create_data)
                    if result:
                        new_list_id = result.get('id')
                        global_list_mapping[str(original_list_id)] = new_list_id
                        created_count += 1
                        print(f"      ✓ Создан новый список (ID: {new_list_id})")
                    else:
                        print(f"      ✗ Ошибка при создании списка")
            
            print(f"  ✓ Маппинг глобальных списков создан:")
            print(f"     - Найдено существующих: {found_count}")
            print(f"     - Создано новых: {created_count}")
            print(f"     - Всего в маппинге: {len(global_list_mapping)}")
            
            return global_list_mapping
            
        finally:
            # Восстанавливаем оригинальный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)

    # ==================== КОПИРОВАНИЕ МЕЖДУ ТЕНАНТАМИ ====================
    
    def copy_template_to_another_tenant(self, source_template_id, target_tenant_id, preserve_state=True, export_file=None):
        """Копирует шаблон в другой тенант с раздельной обработкой правил.

        Если передан export_file (путь к уже экспортированному .template.json), переключения на
        исходный тенант не выполняется: предполагается, что экспорт сделан вызывающим кодом.
        Выполняется только переключение на целевой тенант (если нужно) и импорт.
        """
        original_tenant_id = self.api_client.auth_manager.tenant_id

        if export_file:
            # Режим «только импорт»: вызывающий код уже экспортировал шаблон (например, пока был в исходном тенанте)
            print(f"\nКопирование шаблона в другой тенант (импорт из готового файла)...")
            if original_tenant_id != target_tenant_id:
                self.api_client.auth_manager.tenant_id = target_tenant_id
                if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                    print("❌ Не удалось переключиться на целевой тенант")
                    return False
            try:
                return self.import_template(export_file, target_tenant_id, preserve_state)
            finally:
                try:
                    if export_file and os.path.isfile(export_file):
                        os.remove(export_file)
                except Exception as e:
                    print(f"⚠️ Не удалось удалить временный файл экспорта: {e}")

        # Классический режим: экспорт в исходном тенанте, затем импорт в целевом
        print(f"\nКопирование шаблона в другой тенант...")
        try:
            # Считаем, что текущий контекст — исходный тенант (как при вызове из меню)
            temp_dir = tempfile.mkdtemp()
            print("Экспорт шаблона с разделением правил...")
            export_path = self.export_template(source_template_id, temp_dir, include_user_rules=True)
            if not export_path:
                print("❌ Не удалось экспортировать шаблон")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            # Переключаемся на целевой тенант и импортируем
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("❌ Не удалось переключиться на целевой тенант")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            result = self.import_template(export_path, target_tenant_id, preserve_state)
            try:
                if export_path and os.path.isfile(export_path):
                    os.remove(export_path)
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
        """Управление шаблонами и политиками безопасности — единое меню действий"""
        while True:
            print("\n=== УПРАВЛЕНИЕ ШАБЛОНАМИ И ПОЛИТИКАМИ БЕЗОПАСНОСТИ ===")
            print("1. Показать наборы системных правил")
            print("2. Создать шаблон политики безопасности")
            print("3. Экспорт шаблона политики безопасности в JSON (экспериментальный)")
            print("4. Импорт шаблона политики безопасности из JSON файла (экспериментальный)")
            print("5. Копировать шаблон политики безопасности в другой тенант")
            print("6. Копировать шаблон политики безопасности в выбранном тенанте")
            print("7. Посмотреть список политик безопасности")
            print("8. Создать шаблон политики безопасности на основе выбранной политики безопасности (Экспериментальный)")
            print("9. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-9): ")
            
            if choice == '1':
                if not self._select_tenant_for_operation("ПОКАЗАТЬ НАБОРЫ СИСТЕМНЫХ ПРАВИЛ"):
                    continue
                self._show_vendor_templates()
            elif choice == '2':
                if not self._select_tenant_for_operation("СОЗДАТЬ ШАБЛОН ПОЛИТИКИ БЕЗОПАСНОСТИ"):
                    continue
                self._create_new_template()
            elif choice == '3':
                if not self._select_tenant_for_operation("ЭКСПОРТ ШАБЛОНА В JSON"):
                    continue
                self._export_template()
            elif choice == '4':
                self._import_template()
            elif choice == '5':
                self._copy_template_to_another_tenant_menu()
            elif choice == '6':
                if not self._select_tenant_for_operation("КОПИРОВАТЬ ШАБЛОН В ВЫБРАННОМ ТЕНАНТЕ"):
                    continue
                self._duplicate_template_in_tenant()
            elif choice == '7':
                if not self._select_tenant_for_operation("ПОСМОТРЕТЬ СПИСОК ПОЛИТИК БЕЗОПАСНОСТИ"):
                    continue
                self._show_security_policies()
            elif choice == '8':
                if not self._select_tenant_for_operation("СОЗДАТЬ ШАБЛОН НА ОСНОВЕ ПОЛИТИКИ"):
                    continue
                self._create_template_from_policy()
            elif choice == '9':
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