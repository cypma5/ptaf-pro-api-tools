# rules_manager.py (оптимизированный с BaseManager)
import os
import json
import shutil
import datetime
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
    
    def export_single_rule(self, template_id, rule, export_dir):
        """Экспортирует одно правило"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'unnamed_rule')
        
        # Получаем детали правила
        rule_details = self.get_rule_details(template_id, rule_id)
        if not rule_details:
            print(f"Не удалось получить детали правила {rule_name} (ID: {rule_id})")
            return False
        
        # Удаляем ID из экспортируемых данных
        if 'id' in rule_details:
            del rule_details['id']
        
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
            print(f"📁 Путь: {absolute_filepath}")
            self.exported_files.append(absolute_filepath)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении правила '{rule_name}': {e}")
            return False
    
    def export_rules(self, export_dir="exported_rules"):
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
        for rule in user_rules:
            if self.export_single_rule(template_id, rule, export_dir):
                success_count += 1
        
        print(f"\nЭкспортировано {success_count} из {len(user_rules)} правил")
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
            print(f"- {rule.get('name', 'Без названия')} (ID: {rule.get('id', 'Без ID')})")

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
            
            self.failed_files.append({
                'file': file_path,
                'rule': rule_name,
                'error': error_msg,
                'code': response.status_code,
                'response': response.text[:200] if response.text else ""
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg, response.text[:200] if response.text else "")
        
        return False
    
    def import_single_rule(self, template_id, file_path, selected_action_ids=None, enable_after_import=False, problem_dir=None):
        """Импортирует одно правило из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
            
            rule_name = rule_data.get('name', os.path.basename(file_path))
            print(f"Правило: {rule_name}")
            
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
                    
                # Проверяем на ошибку 404
                if response.status_code == 404:
                    # Обрабатываем ошибку 404
                    return self._handle_404_error(
                        template_id, file_path, rule_name, rule_data, 
                        selected_action_ids, enable_after_import, problem_dir
                    )
                
                if response.status_code == 200:
                    print(f"✅ Правило '{rule_name}' успешно обновлено")
                    self.success_files.append(file_path)
                    
                    if enable_after_import:
                        self.enable_rule(template_id, rule_id, True)
                    return True
                else:
                    # Используем ErrorHandler для обработки других ошибок
                    if not self.api_client.error_handler.handle_common_error(response, f"Обновление правила '{rule_name}'"):
                        self.failed_files.append({
                            'file': file_path,
                            'rule': rule_name,
                            'error': f"Ошибка {response.status_code}",
                            'code': response.status_code,
                            'response': response.text[:200] if response.text else ""
                        })
                        
                        if problem_dir:
                            self._move_to_problem_directory(file_path, problem_dir, f"Ошибка {response.status_code}", response.text[:200] if response.text else "")
                    return False
            else:
                # Создание нового правила
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
                
                # Проверяем на ошибку 404
                if response.status_code == 404:
                    # Обрабатываем ошибку 404
                    return self._handle_404_error(
                        template_id, file_path, rule_name, rule_data,
                        selected_action_ids, enable_after_import, problem_dir
                    )
                    
                if response.status_code == 201:
                    print(f"✅ Правило '{rule_name}' успешно создано")
                    self.success_files.append(file_path)
                    
                    try:
                        new_rule = response.json()
                        rule_id = new_rule.get('id')
                        
                        if enable_after_import and rule_id:
                            self.enable_rule(template_id, rule_id, True)
                    except json.JSONDecodeError:
                        pass
                    
                    return True
                else:
                    # Используем ErrorHandler для обработки других ошибок
                    if not self.api_client.error_handler.handle_common_error(response, f"Создание правила '{rule_name}'"):
                        self.failed_files.append({
                            'file': file_path,
                            'rule': rule_name,
                            'error': f"Ошибка {response.status_code}",
                            'code': response.status_code,
                            'response': response.text[:200] if response.text else ""
                        })
                        
                        if problem_dir:
                            self._move_to_problem_directory(file_path, problem_dir, f"Ошибка {response.status_code}", response.text[:200] if response.text else "")
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

    def import_rules(self, directory_path):
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
        selected_action_ids = []
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
        enable_rules = False
        enable_choice = input("\nВключить импортированные правила? (y/n): ").lower()
        if enable_choice == 'y':
            enable_rules = True
            print("Импортированные правила будут включены")
        else:
            print("Импортированные правила останутся выключенными")
        
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
                    if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules, problem_dir):
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
                        if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules, problem_dir):
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
                print(f"   Ответ сервера: {fail['response']}")
            print()

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