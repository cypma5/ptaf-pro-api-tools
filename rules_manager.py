# rules_manager.py (оптимизированный с BaseManager)
import os
import json
import shutil
import datetime
import tempfile
from base_manager import BaseManager

class RulesManager(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)
        self.failed_files = []
        self.success_files = []
        self.exported_files = []
        self.problem_dir_created = False
    
    def get_policy_template_id(self):
        """Получает ID первого доступного шаблона политики"""
        response = self.api_client.get_templates_with_user_rules()
        templates = self._parse_response_items(response)
        if templates and len(templates) > 0:
            return templates[0].get('id')
        return None
    
    def get_existing_rules(self, template_id):
        """Получает список существующих правил для шаблона"""
        response = self.api_client.get_user_rules(template_id)
        return self._parse_response_items(response)
    
    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        response = self.api_client.get_user_rule_details(template_id, rule_id)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def create_rule(self, template_id, rule_data):
        """Создает новое правило"""
        return self.api_client.create_user_rule(template_id, rule_data)
    
    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет существующее правило"""
        return self.api_client.update_user_rule(template_id, rule_id, update_data)
    
    def enable_rule(self, template_id, rule_id, enable=True):
        """Включает или отключает правило"""
        payload = {"enabled": enable}
        return self.api_client.update_user_rule(template_id, rule_id, payload)
    
    def delete_rule(self, template_id, rule_id):
        """Удаляет правило"""
        return self.api_client.delete_user_rule(template_id, rule_id)
    
    def get_available_actions(self):
        """Получает список доступных действий"""
        response = self.api_client.get_actions()
        return self._parse_response_items(response)
    
    def get_action_details(self, action_ids):
        """Получает детали действий по их ID"""
        if not action_ids:
            return {}
        
        all_actions = self.get_available_actions()
        if not all_actions:
            return {}
        
        # Создаем словарь {id: action_data} для быстрого поиска
        action_dict = {}
        for action in all_actions:
            action_id = action.get('id')
            if action_id and action_id in action_ids:
                # Копируем только нужные поля
                action_dict[str(action_id)] = {
                    'name': action.get('name'),
                    'type_id': action.get('type_id'),
                    'configuration': action.get('configuration')
                }
        
        return action_dict
    
    def export_single_rule(self, template_id, rule, export_dir, preserve_state=False):
        """Экспортирует одно правило"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'unnamed_rule')
        rule_enabled = rule.get('enabled', True)  # Получаем состояние правила
        
        # Получаем детали правила
        rule_details = self.get_rule_details(template_id, rule_id)
        if not rule_details:
            print(f"Не удалось получить детали правила {rule_name} (ID: {rule_id})")
            return False
        
        # Удаляем ID из экспортируемых данных
        if 'id' in rule_details:
            del rule_details['id']
        
        # Если нужно сохранить состояние, добавляем флаг enabled
        if preserve_state:
            rule_details['enabled'] = rule_enabled
        
        # Формируем имя файла
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in rule_name)
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.ptafpro"
        filepath = os.path.join(export_dir, filename)
        
        # Получаем абсолютный путь
        absolute_filepath = os.path.abspath(filepath)
        
        # Сохраняем правило в файл
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule_details, f, ensure_ascii=False, indent=2)
            print(f"Правило '{rule_name}' экспортировано:")
            print(f"  Состояние: {'включено' if rule_enabled else 'выключено'}")
            print(f"📁 Путь: {absolute_filepath}")
            self.exported_files.append(absolute_filepath)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении правила '{rule_name}': {e}")
            return False
    
    def export_single_rule_with_actions(self, template_id, rule, export_dir, preserve_state=False):
        """Экспортирует одно правило с сохранением информации о связанных действиями"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'unnamed_rule')
        rule_enabled = rule.get('enabled', True)  # Получаем состояние правила
        
        # Получаем детали правила
        rule_details = self.get_rule_details(template_id, rule_id)
        if not rule_details:
            print(f"Не удалось получить детали правила {rule_name} (ID: {rule_id})")
            return False
        
        # Извлекаем ID действий из правила
        action_ids = []
        if 'configuration' in rule_details and 'actions' in rule_details['configuration']:
            action_ids = rule_details['configuration']['actions']
        
        # Получаем детали связанных действий
        action_details = {}
        if action_ids:
            action_details = self.get_action_details(action_ids)
        
        # Подготовка данных для экспорта
        export_data = {
            'rule_data': rule_details,
            'actions_info': action_details,
            'export_metadata': {
                'export_time': datetime.datetime.now().isoformat(),
                'tenant_id': self.api_client.auth_manager.tenant_id,
                'rule_name': rule_name,
                'rule_id': rule_id,
                'template_id': template_id,
                'action_count': len(action_ids),
                'preserve_state': preserve_state,
                'rule_enabled': rule_enabled  # Сохраняем исходное состояние
            }
        }
        
        # Удаляем ID из данных правила
        if 'id' in export_data['rule_data']:
            del export_data['rule_data']['id']
        
        # Если нужно сохранить состояние, добавляем флаг enabled в rule_data
        if preserve_state:
            export_data['rule_data']['enabled'] = rule_enabled
        
        # Формируем имя файла
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in rule_name)
        safe_name = safe_name.replace(' ', '_')
        if preserve_state:
            state_suffix = '_enabled' if rule_enabled else '_disabled'
            filename = f"{safe_name}_with_actions{state_suffix}.ptafpro"
        else:
            filename = f"{safe_name}_with_actions.ptafpro"
        filepath = os.path.join(export_dir, filename)
        
        # Получаем абсолютный путь
        absolute_filepath = os.path.abspath(filepath)
        
        # Сохраняем правило в файл
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"Правило '{rule_name}' с {len(action_ids)} действиями экспортировано:")
            print(f"  Состояние: {'включено' if rule_enabled else 'выключено'}")
            print(f"📁 Путь: {absolute_filepath}")
            self.exported_files.append(absolute_filepath)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении правила '{rule_name}' с действиями: {e}")
            return False
    
    def export_rules_with_actions(self, export_dir="exported_rules_with_actions", preserve_state=False):
        """Экспортирует правила с сохранением информации о связанных действиями"""
        if not self.api_client.auth_manager.access_token:
            if not self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
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
            print("Нет пользовательских правил для экспорта")
            return False
        
        # Создаем директорию для экспорта
        os.makedirs(export_dir, exist_ok=True)
        
        # Экспортируем все правила
        success_count = 0
        enabled_count = 0
        disabled_count = 0
        total_actions = 0
        
        for rule in user_rules:
            rule_enabled = rule.get('enabled', True)
            if preserve_state:
                if rule_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
            
            if self.export_single_rule_with_actions(template_id, rule, export_dir, preserve_state):
                success_count += 1
                # Подсчитываем количество действий
                rule_details = self.get_rule_details(template_id, rule.get('id'))
                if rule_details and 'configuration' in rule_details and 'actions' in rule_details['configuration']:
                    total_actions += len(rule_details['configuration']['actions'])
        
        print(f"\nЭкспортировано {success_count} из {len(user_rules)} правил")
        print(f"Всего сохранено {total_actions} связей с действиями")
        if preserve_state:
            print(f"Состояние правил: {enabled_count} включено, {disabled_count} выключено")
        return success_count > 0
    
    def export_rules(self, export_dir="exported_rules", preserve_state=False):
        """Экспортирует правила"""
        if not self.api_client.auth_manager.access_token:
            if not self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
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
            print("Нет пользовательских правил для экспорта")
            return False
        
        # Создаем директорию для экспорта
        os.makedirs(export_dir, exist_ok=True)
        
        # Экспортируем все правила
        success_count = 0
        enabled_count = 0
        disabled_count = 0
        
        for rule in user_rules:
            rule_enabled = rule.get('enabled', True)
            if preserve_state:
                if rule_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
            
            if self.export_single_rule(template_id, rule, export_dir, preserve_state):
                success_count += 1
        
        print(f"\nЭкспортировано {success_count} из {len(user_rules)} правил")
        if preserve_state:
            print(f"Состояние правил: {enabled_count} включено, {disabled_count} выключено")
        return success_count > 0
    
    def delete_all_user_rules(self):
        """Удаляет все пользовательские правила из шаблона"""
        if not self.api_client.auth_manager.access_token:
            if not self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
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
            rule_name = rule.get('name', 'Без названия')
            rule_id = rule.get('id', 'Без ID')
            rule_enabled = rule.get('enabled', True)
            status = "включено" if rule_enabled else "выключено"
            print(f"- {rule_name} (ID: {rule_id}) [{status}]")

        if not self._confirm_action(f"Вы уверены, что хотите удалить {len(user_rules)} правил?"):
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

            response = self.delete_rule(template_id, rule_id)

            if response and response.status_code == 204:
                print(f"Правило '{rule_name}' успешно удалено")
                deleted_count += 1
            else:
                error_msg = response.text if response else "Не удалось выполнить запрос"
                print(f"Ошибка при удалении правила '{rule_name}': {error_msg}")

        print(f"\nУдалено {deleted_count} из {len(user_rules)} правил")
        return deleted_count > 0

    def _create_problem_directory(self, original_dir):
        """Создает директорию для проблемных файлов"""
        problem_dir = os.path.join(original_dir, "problem")
        if not os.path.exists(problem_dir):
            try:
                os.makedirs(problem_dir, exist_ok=True)
                self.problem_dir_created = True
                print(f"Создана директория для проблемных файлов: {problem_dir}")
            except Exception as e:
                print(f"Не удалось создать директорию для проблемных файлов: {e}")
                return None
        return problem_dir

    def _save_import_report(self, directory_path, success_count, total_count):
        """Сохраняет отчет об импорте в файл"""
        report_file = os.path.join(directory_path, "import_report.txt")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("ОТЧЕТ ОБ ИМПОРТЕ ПРАВИЛ\n")
                f.write("=" * 50 + "\n\n")
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Дата и время импорта: {current_time}\n")
                f.write(f"Тенант ID: {self.api_client.auth_manager.tenant_id}\n\n")
                
                f.write(f"ИТОГИ:\n")
                f.write(f"  Успешно импортировано: {success_count}\n")
                f.write(f"  Не удалось импортировать: {len(self.failed_files)}\n")
                f.write(f"  Всего файлов: {total_count}\n\n")
                
                if self.success_files:
                    f.write("УСПЕШНО ИМПОРТИРОВАНЫ:\n")
                    f.write("-" * 30 + "\n")
                    for i, file_path in enumerate(self.success_files, 1):
                        f.write(f"{i}. {os.path.basename(file_path)}\n")
                    f.write("\n")
                
                if self.failed_files:
                    f.write("ПРОБЛЕМНЫЕ ФАЙЛЫ:\n")
                    f.write("=" * 50 + "\n")
                    for i, fail in enumerate(self.failed_files, 1):
                        f.write(f"{i}. {fail['file']}\n")
                        f.write(f"   Правило: {fail['rule']}\n")
                        f.write(f"   Причина: {fail['error']}\n")
                        if fail.get('code') is not None:
                            f.write(f"   Код ошибки: {fail['code']}\n")
                        if fail.get('response') is not None:
                            f.write(f"   Ответ сервера: {fail['response']}\n")
                        f.write("\n")
            
            print(f"Отчет об импорте сохранен в файл: {report_file}")
            return report_file
        except Exception as e:
            print(f"Ошибка при сохранении отчета: {e}")
            return None

    def _handle_404_error(self, template_id, file_path, rule_name, rule_data, selected_action_ids, enable_after_import, problem_dir):
        """Обрабатывает ошибку 404 через ErrorHandler"""
        print(f"\n⚠️ Обнаружена ошибка 404 для правила '{rule_name}'")
        
        # Используем ErrorHandler для обработки 404
        if not self.api_client.error_handler.handle_404_error():
            return False
        
        print("Повторяем импорт правила...")
        
        # Повторяем импорт с обновленным токеном
        existing_rules = self.get_existing_rules(template_id)
        if existing_rules is None:
            print("❌ Не удалось получить список существующих правил после обновления токена")
            return False
        
        existing_rules_dict = {rule['name']: rule['id'] for rule in existing_rules if 'name' in rule and 'id' in rule}
        
        if rule_name in existing_rules_dict:
            # Обновление существующего правила
            rule_id = existing_rules_dict[rule_name]
            update_data = {
                "configuration": {
                    "code": rule_data.get("configuration", {}).get("code", ""),
                    "actions": rule_data.get("configuration", {}).get("actions", []),
                    "parameters": rule_data.get("configuration", {}).get("parameters", [])
                }
            }
            
            response = self.update_rule(template_id, rule_id, update_data)
            if response and response.status_code == 200:
                print(f"✅ Правило '{rule_name}' успешно обновлено после обновления токена")
                self.success_files.append(file_path)
                
                if enable_after_import:
                    self.enable_rule(template_id, rule_id, True)
                return True
        else:
            # Создание нового правила
            response = self.create_rule(template_id, rule_data)
            if response and response.status_code == 201:
                print(f"✅ Правило '{rule_name}' успешно создано после обновления токена")
                self.success_files.append(file_path)
                
                if enable_after_import:
                    try:
                        new_rule = response.json()
                        rule_id = new_rule.get('id')
                        if rule_id:
                            self.enable_rule(template_id, rule_id, True)
                    except:
                        pass
                return True
        
        # Если повторная попытка тоже не удалась
        if response:
            error_msg = f"Ошибка при повторном импорте правила (код {response.status_code})"
            print(f"❌ {error_msg}: {rule_name}")
            
            # ДОБАВЛЯЕМ ПОДРОБНУЮ ИНФОРМАЦИЮ ОБ ОШИБКЕ
            response_body = ""
            try:
                if hasattr(response, 'text') and response.text:
                    response_body = response.text[:500]  # Ограничиваем длину
                    print(f"\n📄 ТЕЛО ОТВЕТА (первые 500 символов):")
                    print(f"{response_body}")
                    
                    # Пробуем распарсить как JSON для лучшего форматирования
                    try:
                        error_json = json.loads(response.text)
                        if isinstance(error_json, dict):
                            print(f"\n📋 ДЕТАЛИ ОШИБКИ:")
                            for key, value in error_json.items():
                                if key in ['error', 'message', 'detail', 'errors']:
                                    print(f"  {key}: {value}")
                    except:
                        pass
            except Exception as e:
                response_body = f"Не удалось получить тело ответа: {e}"
            
            self.failed_files.append({
                'file': file_path,
                'rule': rule_name,
                'error': error_msg,
                'code': response.status_code,
                'response': response_body
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, response_body)
        
        return False
    
    def _move_to_problem_directory(self, file_path, problem_dir, error_reason="", server_response=""):
        """Перемещает файл в problem директорию"""
        try:
            filename = os.path.basename(file_path)
            new_path = os.path.join(problem_dir, filename)
            
            # Если файл уже существует в problem директории, добавляем суффикс
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(new_path):
                new_filename = f"{base_name}_{counter}{ext}"
                new_path = os.path.join(problem_dir, new_filename)
                counter += 1
            
            shutil.move(file_path, new_path)
            print(f"Файл перемещен в проблемную директорию: {new_path}")
            
            # Создаем файл с описанием ошибки
            error_file = f"{os.path.splitext(new_path)[0]}_error.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Файл: {filename}\n")
                f.write(f"Ошибка: {error_reason}\n")
                if server_response:
                    f.write(f"Ответ сервера: {server_response}\n")
                f.write(f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            return new_path
        except Exception as e:
            print(f"Не удалось переместить файл в проблемную директорию: {e}")
            return None

    def import_single_rule(self, file_path, selected_action_ids=None, enable_after_import=False, 
                        preserve_state=False, problem_dir=None):
        """Импортирует одно правило из файла (стандартный формат)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
            
            rule_name = rule_data.get('name', os.path.basename(file_path))
            print(f"Правило: {rule_name}")
            
            # Получаем ID шаблона политики
            template_id = self.get_policy_template_id()
            if not template_id:
                error_msg = "Не удалось получить ID шаблона политики"
                print(f"❌ {error_msg}")
                self.failed_files.append({
                    'file': file_path,
                    'rule': rule_name,
                    'error': error_msg,
                    'code': None,
                    'response': None
                })
                
                if problem_dir:
                    self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                return False
            
            # Определяем, нужно ли сохранять исходное состояние
            should_preserve_state = preserve_state and 'enabled' in rule_data
            rule_enabled = rule_data.get('enabled', True)
            
            # Применяем выбранные действия, если они указаны
            if selected_action_ids is not None:
                if 'configuration' not in rule_data:
                    rule_data['configuration'] = {}
                rule_data['configuration']['actions'] = selected_action_ids
            
            # Получаем список существующих правил
            existing_rules = self.get_existing_rules(template_id)
            if existing_rules is None:
                error_msg = "Не удалось получить список существующих правил"
                print(f"❌ {error_msg}")
                self.failed_files.append({
                    'file': file_path,
                    'rule': rule_name,
                    'error': error_msg,
                    'code': None,
                    'response': None
                })
                
                if problem_dir:
                    self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                return False
            
            existing_rules_dict = {rule['name']: rule['id'] for rule in existing_rules if 'name' in rule and 'id' in rule}
            
            if rule_name in existing_rules_dict:
                # Обновление существующего правила - код для update
                # ... (оставляем как есть)
                pass
            else:
                # Создание нового правила
                if should_preserve_state:
                    rule_data['enabled'] = rule_enabled
                elif enable_after_import:
                    rule_data['enabled'] = True
                
                response = self.create_rule(template_id, rule_data)
                
                if response is None:
                    error_msg = "Не удалось выполнить запрос на создание"
                    print(f"❌ {error_msg}")
                    
                    error_details = self._get_last_error_details()
                    if error_details and isinstance(error_details, dict):
                        print(f"\n📄 ДЕТАЛИ ОШИБКИ:")
                        for key, value in error_details.items():
                            if key not in ['exception', 'response_json'] and value:
                                print(f"  {key}: {value}")
                    
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                    return False
                
                if response.status_code == 201:
                    status_text = "включено" if rule_enabled else "выключено"
                    if should_preserve_state:
                        print(f"✅ Правило '{rule_name}' успешно создано ({status_text})")
                    else:
                        print(f"✅ Правило '{rule_name}' успешно создано")
                    self.success_files.append(file_path)
                    return True
                else:
                    # ❌ ОШИБКА - ОДИН ЧИСТЫЙ ВЫВОД
                    print(f"\n{'='*60}")
                    print(f"❌ Ошибка {response.status_code} при создании правила")
                    print(f"{'='*60}")
                    print(f"Правило: {rule_name}")
                    print(f"Файл: {os.path.basename(file_path)}")
                    print(f"HTTP статус: {response.status_code}")
                    
                    # Получаем тело ответа и форматируем JSON красиво
                    try:
                        if hasattr(response, 'text') and response.text:
                            # Пробуем распарсить как JSON
                            try:
                                error_json = json.loads(response.text)
                                # Форматируем JSON с отступами для читаемости
                                formatted_json = json.dumps(error_json, indent=2, ensure_ascii=False)
                                print(f"\n{formatted_json}")
                                
                                # Сохраняем для failed_files
                                response_body = formatted_json
                            except:
                                # Если не JSON, выводим как есть
                                print(f"\n{response.text[:500]}")
                                response_body = response.text[:500]
                        else:
                            print(f"\nТело ответа пустое")
                            response_body = None
                    except Exception as e:
                        response_body = f"Не удалось получить тело ответа: {e}"
                        print(f"\n{response_body}")
                    
                    print(f"{'='*60}")
                    
                    # Сохраняем информацию об ошибке
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': f"Ошибка {response.status_code}",
                        'code': response.status_code,
                        'response': response_body
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(
                            file_path, problem_dir,
                            f"Ошибка {response.status_code}",
                            response_body
                        )
                    return False
        
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка чтения JSON: {str(e)}"
            print(f"❌ {error_msg}")
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
            return False
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
            return False


    def _get_last_error_details(self):
        """Получает детали последней ошибки из error_handler"""
        try:
            if hasattr(self.api_client, 'error_handler'):
                if hasattr(self.api_client.error_handler, 'last_error'):
                    return self.api_client.error_handler.last_error
        except Exception:
            pass
        return None


    def import_single_rule_with_actions(self, file_path, action_mapping=None, enable_after_import=False, 
                                        preserve_state=False, problem_dir=None):
        """Импортирует одно правило из файла с восстановлением связей с действиями"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Проверяем формат файла
            if 'rule_data' not in import_data or 'actions_info' not in import_data:
                print(f"Файл {os.path.basename(file_path)} имеет неверный формат для импорта с действиями")
                return self.import_single_rule(file_path, None, enable_after_import, preserve_state, problem_dir)
            
            rule_data = import_data['rule_data']
            actions_info = import_data['actions_info']
            export_metadata = import_data.get('export_metadata', {})
            
            rule_name = rule_data.get('name', os.path.basename(file_path))
            print(f"Правило с действиями: {rule_name}")
            
            # Проверяем, нужно ли сохранять состояние из метаданных экспорта
            metadata_preserve_state = export_metadata.get('preserve_state', False)
            rule_enabled = export_metadata.get('rule_enabled', True)
            
            # Определяем окончательное решение о сохранении состояния
            should_preserve_state = (preserve_state and metadata_preserve_state and 
                                    'enabled' in rule_data)
            
            # Получаем ID шаблона политики
            template_id = self.get_policy_template_id()
            if not template_id:
                error_msg = "Не удалось получить ID шаблона политики"
                print(f"❌ {error_msg}")
                self.failed_files.append({
                    'file': file_path,
                    'rule': rule_name,
                    'error': error_msg,
                    'code': None,
                    'response': None
                })
                
                if problem_dir:
                    self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                return False
            
            # Восстанавливаем связи с действиями
            original_action_ids = []
            if 'configuration' in rule_data and 'actions' in rule_data['configuration']:
                original_action_ids = rule_data['configuration']['actions']
            
            restored_action_ids = []
            if action_mapping:
                # Используем предоставленный маппинг
                for original_action_id in original_action_ids:
                    if str(original_action_id) in action_mapping:
                        restored_action_ids.append(action_mapping[str(original_action_id)])
                    else:
                        # Пытаемся найти действие по информации из файла
                        action_info = actions_info.get(str(original_action_id))
                        if action_info:
                            # Используем ActionsManager для поиска/создания
                            from actions_manager import ActionsManager
                            actions_manager = ActionsManager(self.api_client)
                            
                            target_action = actions_manager.find_or_create_action(action_info)
                            if target_action:
                                restored_action_ids.append(target_action.get('id'))
                                action_mapping[str(original_action_id)] = target_action.get('id')
                        else:
                            print(f"  ⚠️ Действие ID {original_action_id} не найдено в маппинге и файле")
            else:
                # Используем только информацию из файла
                for original_action_id in original_action_ids:
                    action_info = actions_info.get(str(original_action_id))
                    if action_info:
                        action_name = action_info.get('name')
                        action_type_id = action_info.get('type_id')
                        
                        if action_name and action_type_id:
                            # Используем ActionsManager для поиска/создания
                            from actions_manager import ActionsManager
                            actions_manager = ActionsManager(self.api_client)
                            
                            target_action = actions_manager.find_or_create_action(action_info)
                            if target_action:
                                restored_action_ids.append(target_action.get('id'))
                            else:
                                print(f"  ⚠️ Действие '{action_name}' не найдено и не удалось создать")
                    else:
                        print(f"  ⚠️ Информация о действии ID {original_action_id} не найдена в файле")
            
            # Обновляем действия в правиле
            if 'configuration' not in rule_data:
                rule_data['configuration'] = {}
            
            rule_data['configuration']['actions'] = restored_action_ids
            
            # Получаем список существующих правил
            existing_rules = self.get_existing_rules(template_id)
            if existing_rules is None:
                error_msg = "Не удалось получить список существующих правил"
                print(f"❌ {error_msg}")
                self.failed_files.append({
                    'file': file_path,
                    'rule': rule_name,
                    'error': error_msg,
                    'code': None,
                    'response': None
                })
                
                if problem_dir:
                    self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                return False
            
            existing_rules_dict = {rule['name']: rule['id'] for rule in existing_rules if 'name' in rule and 'id' in rule}
            
            if rule_name in existing_rules_dict:
                # Обновление существующего правила
                rule_id = existing_rules_dict[rule_name]
                update_data = {
                    "configuration": {
                        "code": rule_data.get("configuration", {}).get("code", ""),
                        "actions": rule_data.get("configuration", {}).get("actions", []),
                        "parameters": rule_data.get("configuration", {}).get("parameters", [])
                    }
                }
                
                # Если нужно сохранить состояние, добавляем enabled
                if should_preserve_state:
                    update_data['enabled'] = rule_enabled
                    print(f"  Состояние: {'включено' if rule_enabled else 'выключено'} (сохранено)")
                elif enable_after_import:
                    update_data['enabled'] = True
                    print(f"  Состояние: включено (новое)")
                
                response = self.update_rule(template_id, rule_id, update_data)
                if response is None:
                    error_msg = "Не удалось выполнить запрос на обновление (нет ответа от сервера)"
                    print(f"❌ {error_msg}")
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                    return False
                    
                if response.status_code == 200:
                    status_text = "включено" if rule_enabled else "выключено"
                    action_text = f"с {len(restored_action_ids)} действиями"
                    if should_preserve_state:
                        print(f"✅ Правило '{rule_name}' успешно обновлено ({status_text}, {action_text})")
                    else:
                        print(f"✅ Правило '{rule_name}' успешно обновлено ({action_text})")
                    self.success_files.append(file_path)
                    return True
                else:
                    # ❌ ОШИБКА - выводим код и тело ответа
                    error_msg = f"Ошибка {response.status_code} при обновлении правила с действиями"
                    print(f"\n{'='*60}")
                    print(f"❌ {error_msg}")
                    print(f"{'='*60}")
                    print(f"Правило: {rule_name}")
                    print(f"Файл: {os.path.basename(file_path)}")
                    print(f"HTTP статус: {response.status_code}")
                    
                    # Получаем тело ответа
                    response_body = ""
                    try:
                        if hasattr(response, 'text') and response.text:
                            response_body = response.text[:500]  # Ограничиваем длину
                            print(f"\n📄 ТЕЛО ОТВЕТА (первые 500 символов):")
                            print(f"{response_body}")
                            
                            # Пробуем распарсить как JSON для лучшего форматирования
                            try:
                                error_json = json.loads(response.text)
                                if isinstance(error_json, dict):
                                    print(f"\n📋 ДЕТАЛИ ОШИБКИ:")
                                    for key, value in error_json.items():
                                        if key in ['error', 'message', 'detail', 'errors']:
                                            print(f"  {key}: {value}")
                            except:
                                pass
                        else:
                            print(f"\n📄 Тело ответа пустое")
                    except Exception as e:
                        response_body = f"Не удалось получить тело ответа: {e}"
                        print(f"\n📄 {response_body}")
                    
                    print(f"{'='*60}")
                    
                    # Сохраняем информацию об ошибке
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': response.status_code,
                        'response': response_body
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg, response_body)
                    return False
            else:
                # Создание нового правила
                # Если нужно сохранить состояние, добавляем enabled
                if should_preserve_state:
                    rule_data['enabled'] = rule_enabled
                elif enable_after_import:
                    rule_data['enabled'] = True
                
                response = self.create_rule(template_id, rule_data)
                if response is None:
                    error_msg = "Не удалось выполнить запрос на создание (нет ответа от сервера)"
                    print(f"❌ {error_msg}")
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
                    return False
                    
                if response.status_code == 201:
                    status_text = "включено" if rule_enabled else "выключено"
                    action_text = f"с {len(restored_action_ids)} действиями"
                    if should_preserve_state:
                        print(f"✅ Правило '{rule_name}' успешно создано ({status_text}, {action_text})")
                    else:
                        print(f"✅ Правило '{rule_name}' успешно создано ({action_text})")
                    self.success_files.append(file_path)
                    return True
                else:
                    # ❌ ОШИБКА - выводим код и тело ответа
                    error_msg = f"Ошибка {response.status_code} при создании правила с действиями"
                    print(f"\n{'='*60}")
                    print(f"❌ {error_msg}")
                    print(f"{'='*60}")
                    print(f"Правило: {rule_name}")
                    print(f"Файл: {os.path.basename(file_path)}")
                    print(f"HTTP статус: {response.status_code}")
                    
                    # Получаем тело ответа
                    response_body = ""
                    try:
                        if hasattr(response, 'text') and response.text:
                            response_body = response.text[:500]  # Ограничиваем длину
                            print(f"\n📄 ТЕЛО ОТВЕТА (первые 500 символов):")
                            print(f"{response_body}")
                            
                            # Пробуем распарсить как JSON для лучшего форматирования
                            try:
                                error_json = json.loads(response.text)
                                if isinstance(error_json, dict):
                                    print(f"\n📋 ДЕТАЛИ ОШИБКИ:")
                                    for key, value in error_json.items():
                                        if key in ['error', 'message', 'detail', 'errors']:
                                            print(f"  {key}: {value}")
                            except:
                                pass
                        else:
                            print(f"\n📄 Тело ответа пустое")
                    except Exception as e:
                        response_body = f"Не удалось получить тело ответа: {e}"
                        print(f"\n📄 {response_body}")
                    
                    print(f"{'='*60}")
                    
                    # Сохраняем информацию об ошибке
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': response.status_code,
                        'response': response_body
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg, response_body)
                    return False
        
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка чтения JSON: {str(e)}"
            print(f"❌ Ошибка при чтении файла {file_path}: {error_msg}")
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
            return False
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            print(f"❌ Неожиданная ошибка при обработке файла {file_path}: {error_msg}")
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, None)
            return False


    def import_rules(self, directory_path, include_actions=False, preserve_state=False):
        """Импортирует правила из указанной директории"""
        if not os.path.isdir(directory_path):
            print(f"Директория не найдена: {directory_path}")
            return False
        
        # Сбрасываем списки файлов перед новым импортом
        self.failed_files = []
        self.success_files = []
        self.problem_dir_created = False
        
        # Сохраняем текущий тенант для возможного восстановления
        original_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Создаем директорию для проблемных файлов
        problem_dir = self._create_problem_directory(directory_path)
        
        # Определяем, нужно ли спрашивать о действиях
        ask_about_actions = not include_actions
        
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print("Не удалось получить ID шаблона политики")
            # Восстанавливаем исходный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        print(f"\nИспользуется шаблон политики с ID: {template_id}")
        
        selected_action_ids = None
        
        # Если не импортируем с действиями, спрашиваем о выборе действий
        if ask_about_actions:
            # Получаем список доступных действий
            actions = self.get_available_actions()
            if not actions:
                print("Не удалось получить список доступных действий")
                # Восстанавливаем исходный тенант
                if original_tenant_id:
                    self.api_client.auth_manager.tenant_id = original_tenant_id
                    self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            
            # Выводим список доступных действий
            print("\nДоступные действия:")
            for i, action in enumerate(actions, 1):
                print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
            
            # Запрашиваем выбор действий для всех правил
            while True:
                choice = input(
                    "\nВыберите номера действий для применения ко ВСЕМ правилам (через запятую, или Enter чтобы пропустить): "
                )
                
                if not choice.strip():
                    print("Действия не будут изменены")
                    selected_action_ids = None
                    break
                
                try:
                    selected_indices = [int(num.strip()) - 1 for num in choice.split(',') if num.strip().isdigit()]
                    valid_indices = [i for i in selected_indices if 0 <= i < len(actions)]
                    
                    if not valid_indices:
                        print("Некорректные номера действий")
                        continue
                    
                    # Формируем список ID выбранных действий
                    selected_action_ids = [actions[i]['id'] for i in valid_indices]
                    break
                    
                except ValueError:
                    print("Пожалуйста, введите номера через запятую (например: 1,2,3)")
        
        # Спрашиваем, нужно ли включать правила после импорта
        enable_after_import = False
        if not preserve_state:
            enable_choice = input("\nВключить импортированные правила? (y/n): ").lower()
            if enable_choice == 'y':
                enable_after_import = True
                print("Импортированные правила будут включены")
            else:
                print("Импортированные правила останутся выключенными")
        else:
            print("\nСостояние правил будет сохранено из исходных файлов")
        
        # Получаем список JSON файлов в директории
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.ptafpro')]
        
        if not json_files:
            print("В указанной директории нет .ptafpro файлов")
            # Восстанавливаем исходный тенант
            if original_tenant_id:
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            return False
        
        # Выводим список файлов для выбора
        print("\nДоступные файлы для импорта:")
        for i, filename in enumerate(json_files, 1):
            print(f"{i}. {filename}")
        
        while True:
            choice = input(
                "\nВыберите:\n"
                "1. Импортировать все файлы\n"
                "2. Выбрать файлы для импорта (через запятую)\n"
                "3. Отмена\n"
                "Ваш выбор (1-3): "
            )
            
            if choice == '1':
                # Импорт всех файлов
                success_count = 0
                for i, filename in enumerate(json_files, 1):
                    print(f"\n[{i}/{len(json_files)}] ", end="")
                    file_path = os.path.abspath(os.path.join(directory_path, filename))
                    
                    if include_actions:
                        # Импорт с восстановлением действий
                        if self.import_single_rule_with_actions(file_path, enable_after_import, 
                                                               preserve_state, problem_dir):
                            success_count += 1
                    else:
                        # Стандартный импорт
                        if self.import_single_rule(file_path, selected_action_ids, enable_after_import,
                                                  preserve_state, problem_dir):
                            success_count += 1
                
                # Восстанавливаем исходный тенант
                if original_tenant_id:
                    self.api_client.auth_manager.tenant_id = original_tenant_id
                    self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                
                # Выводим итоговую статистику
                fail_count = len(self.failed_files)
                total_count = len(json_files)
                
                print(f"\nИтог:")
                print(f"Успешно обработано: {success_count}")
                print(f"Не удалось обработать: {fail_count}")
                print(f"Всего файлов: {total_count}")
                
                # Сохраняем отчет об импорте
                self._save_import_report(directory_path, success_count, total_count)
                
                # Выводим список проблемных файлов
                self.print_failed_files()
                return success_count > 0
            
            elif choice == '2':
                # Выбор конкретных файлов
                try:
                    file_nums = input("Введите номера файлов для импорта (через запятую): ")
                    selected_indices = [int(num.strip()) - 1 for num in file_nums.split(',') if num.strip().isdigit()]
                    
                    valid_indices = [i for i in selected_indices if 0 <= i < len(json_files)]
                    
                    if not valid_indices:
                        print("Некорректные номера файлов")
                        continue
                    
                    success_count = 0
                    for i, index in enumerate(valid_indices, 1):
                        print(f"\n[{i}/{len(valid_indices)}] ", end="")
                        filename = json_files[index]
                        file_path = os.path.abspath(os.path.join(directory_path, filename))
                        
                        if include_actions:
                            # Импорт с восстановлением действий
                            if self.import_single_rule_with_actions(file_path, enable_after_import,
                                                                   preserve_state, problem_dir):
                                success_count += 1
                        else:
                            # Стандартный импорт
                            if self.import_single_rule(file_path, selected_action_ids, enable_after_import,
                                                      preserve_state, problem_dir):
                                success_count += 1
                    
                    # Восстанавливаем исходный тенант
                    if original_tenant_id:
                        self.api_client.auth_manager.tenant_id = original_tenant_id
                        self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                    
                    # Выводим итоговую статистику
                    fail_count = len([i for i in selected_indices if i not in valid_indices]) + \
                                (len(valid_indices) - success_count)
                    total_count = len(valid_indices)
                    
                    print(f"\nИтог:")
                    print(f"Успешно обработано: {success_count}")
                    print(f"Не удалось обработать: {fail_count}")
                    print(f"Всего выбрано файлов: {total_count}")
                    
                    # Сохраняем отчет об импорте
                    self._save_import_report(directory_path, success_count, total_count)
                    
                    self.print_failed_files()
                    return success_count > 0
                
                except ValueError:
                    print("Пожалуйста, введите номера через запятую (например: 1,2,3)")
            
            elif choice == '3':
                # Восстанавливаем исходный тенант
                if original_tenant_id:
                    self.api_client.auth_manager.tenant_id = original_tenant_id
                    self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def print_failed_files(self):
        """Выводит список проблемных файлов с причинами ошибок"""
        if not self.failed_files:
            print("\nНет проблемных файлов!")
            return
        
        print("\nСписок проблемных файлов:")
        for i, fail in enumerate(self.failed_files, 1):
            print(f"{i}. {fail['file']}")
            print(f"   Правило: {fail['rule']}")
            print(f"   Причина: {fail['error']}")
            if fail.get('code') is not None:
                print(f"   Код ошибки: {fail['code']}")
            if fail.get('response') is not None:
                print(f"   Ответ сервера: {fail['response'][:200]}")
            print()

    def manage_rules(self):
        """Меню управления правилами"""
        while True:
            print("\n=== РАБОТА С ПРАВИЛАМИ ===")
            print("1. Импорт правил")
            print("2. Экспорт правил")
            print("3. Копирование правил в другой тенант")
            print("4. (Опасное) Удалить все пользовательские правила")
            print("5. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-5): ")
            
            if choice == '1':
                self._import_rules_menu()
            elif choice == '2':
                self._export_rules_menu()
            elif choice == '3':
                self._copy_rules_menu()
            elif choice == '4':
                self._delete_all_rules_menu()
            elif choice == '5':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")
    
    def _import_rules_menu(self):
        """Меню импорта правил"""
        print("\n=== ИМПОРТ ПРАВИЛ ===")
        
        # Используем TenantManager для выбора тенанта
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("Не удалось выбрать тенант")
            return
        
        source_dir = input("Введите путь к директории с JSON файлами: ").strip()
        if not source_dir or not os.path.isdir(source_dir):
            print("Указанная директория не существует")
            return
        
        # Спрашиваем, нужно ли сохранить связи с действиями
        include_actions = False
        choice = input("\nСохранить связи с действиями при импорте? (y/n): ").lower()
        if choice == 'y':
            include_actions = True
            print("Связи с действиями будут восстановлены")
        else:
            print("Связи с действиями не будут восстановлены")
        
        # Спрашиваем, нужно ли сохранить исходное состояние правил
        preserve_state = False
        if include_actions:
            choice = input("\nПеренести правила в исходном состоянии (включено/выключено)? (y/n): ").lower()
            if choice == 'y':
                preserve_state = True
                print("Состояние правил будет сохранено")
            else:
                print("Состояние правил НЕ будет сохранено")
        
        self.import_rules(source_dir, include_actions, preserve_state)

    def _export_rules_menu(self):
        """Меню экспорта правил"""
        print("\n=== ЭКСПОРТ ПРАВИЛ ===")
        
        # Используем TenantManager для выбора тенанта
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("Не удалось выбрать тенант")
            return
        
        # Спрашиваем, нужно ли сохранить связи с действиями
        include_actions = False
        choice = input("\nСохранить связи с действиями при экспорте? (y/n): ").lower()
        if choice == 'y':
            include_actions = True
            print("Связи с действиями будут сохранены")
        else:
            print("Связи с действиями не будут сохранены")
        
        # Спрашиваем, нужно ли сохранить исходное состояние правил
        preserve_state = False
        if include_actions:
            choice = input("\nСохранить исходное состояние правил (включено/выключено)? (y/n): ").lower()
            if choice == 'y':
                preserve_state = True
                print("Состояние правил будет сохранено")
            else:
                print("Состояние правил НЕ будет сохранено")
        
        if include_actions:
            export_dir = input("Введите путь для экспорта [exported_rules_with_actions]: ").strip()
            if not export_dir:
                export_dir = "exported_rules_with_actions"
            self.export_rules_with_actions(export_dir, preserve_state)
        else:
            export_dir = input("Введите путь для экспорта [exported_rules]: ").strip()
            if not export_dir:
                export_dir = "exported_rules"
            self.export_rules(export_dir, preserve_state)

    def _copy_rules_menu(self):
        """Меню копирования правил в другой тенант"""
        print("\n=== КОПИРОВАНИЕ ПРАВИЛ В ДРУГОЙ ТЕНАНТ ===")
        
        # Получаем список доступных тенантов
        from snapshot_manager import SnapshotManager
        snapshot_manager = SnapshotManager(self.api_client)
        tenants = snapshot_manager.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        source_tenant = self._select_item_from_list(tenants, "Выберите исходный тенант")
        if not source_tenant:
            return
        
        source_tenant_id = source_tenant['id']
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Выбор целевого тенанта
        print(f"\nВыберите целевой тенант (куда копировать):")
        target_tenant = self._select_item_from_list(tenants, "Выберите целевой тенант")
        if not target_tenant:
            return
        
        target_tenant_id = target_tenant['id']
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return
        
        # Спрашиваем, нужно ли сохранить связи с действиями
        include_actions = False
        choice = input("\nСохранить связи с действиями при копировании? (y/n): ").lower()
        if choice == 'y':
            include_actions = True
            print("Связи с действиями будут сохранены")
        else:
            print("Связи с действиями не будут сохранены")
        
        # Спрашиваем, нужно ли сохранить исходное состояние правил
        preserve_state = False
        if include_actions:
            choice = input("\nСохранить исходное состояние правил (включено/выключено)? (y/n): ").lower()
            if choice == 'y':
                preserve_state = True
                print("Состояние правил будет сохранено")
            else:
                print("Состояние правил НЕ будет сохранено")
        
        print(f"\nКопирование правил из '{source_tenant_name}' в '{target_tenant_name}'...")
        
        # Создаем временную директорию для экспорта
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Переключаемся на исходный тенант и экспортируем правила
            original_tenant_id = self.api_client.auth_manager.tenant_id
            
            self.api_client.auth_manager.tenant_id = source_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
                return False
            
            if include_actions:
                export_result = self.export_rules_with_actions(temp_dir, preserve_state)
            else:
                export_result = self.export_rules(temp_dir, preserve_state)
            
            if not export_result:
                print("Не удалось экспортировать правила из исходного тенанта")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            
            # Если нужно копировать с действиями, создаем маппинг действий
            action_mapping = {}
            if include_actions:
                from actions_manager import ActionsManager
                actions_manager = ActionsManager(self.api_client)
                action_mapping = actions_manager.copy_actions_between_tenants(source_tenant_id, target_tenant_id)
            
            # Переключаемся на целевой тенант и импортируем правила
            self.api_client.auth_manager.tenant_id = target_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
                return False
            
            # Импортируем правила
            success_count = 0
            total_files = 0
            
            for filename in os.listdir(temp_dir):
                if filename.endswith('.ptafpro'):
                    total_files += 1
                    file_path = os.path.join(temp_dir, filename)
                    print(f"\nИмпорт файла {filename} ({total_files})...")
                    
                    if include_actions:
                        success = self.import_single_rule_with_actions(
                            file_path, action_mapping, False, preserve_state, None
                        )
                    else:
                        success = self.import_single_rule(
                            file_path, None, False, preserve_state, None
                        )
                    
                    if success:
                        success_count += 1
            
            # Восстанавливаем исходный тенант
            self.api_client.auth_manager.tenant_id = original_tenant_id
            self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            
            # Удаляем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            print(f"\nИтог копирования:")
            print(f"Успешно импортировано: {success_count} из {total_files} правил")
            print(f"Маппинг действий создан для: {len(action_mapping)} действий")
            
            if success_count > 0:
                print(f"✅ Правила успешно скопированы из '{source_tenant_name}' в '{target_tenant_name}'")
                return True
            else:
                print(f"❌ Не удалось скопировать правила")
                return False
            
        except Exception as e:
            print(f"Ошибка при копировании правил: {e}")
            # Восстанавливаем исходный тенант
            if 'original_tenant_id' in locals():
                self.api_client.auth_manager.tenant_id = original_tenant_id
                self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request)
            
            # Удаляем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return False

    def _delete_all_rules_menu(self):
        """Меню удаления всех правил"""
        print("\n=== (ОПАСНОЕ) УДАЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЬСКИХ ПРАВИЛ ===")
        
        # Используем TenantManager для выбора тенанта
        from tenants import TenantManager
        tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
        if not tenant_manager.select_tenant_interactive():
            print("Не удалось выбрать тенант")
            return
        
        self.delete_all_user_rules()

    def manage_dangerous_actions(self):
        """Управление опасными действиями"""
        while True:
            print("\n=== ОПАСНЫЕ ДЕЙСТВИЯ ===")
            print("ВНИМАНИЕ: Эти операции могут привести к потере данных!")
            print("1. Удалить все пользовательские правила")
            print("2. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-2): ")
            
            if choice == '1':
                # Используем TenantManager для выбора тенанта
                from tenants import TenantManager
                tenant_manager = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
                if not tenant_manager.select_tenant_interactive():
                    print("Не удалось выбрать тенант")
                    continue
                self.delete_all_user_rules()
            elif choice == '2':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")