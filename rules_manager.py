import os
import json
import shutil
import datetime
from urllib.parse import urljoin

class RulesManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func
        self.failed_files = []
        self.success_files = []
        self.exported_files = []
        self.problem_dir_created = False

    def get_policy_template_id(self):
        """Получает ID первого доступного шаблона политики"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            templates = response.json()
            
            if isinstance(templates, dict) and 'items' in templates and len(templates['items']) > 0:
                return templates['items'][0].get('id')
            elif isinstance(templates, list) and len(templates) > 0:
                return templates[0].get('id')
            else:
                print("Не найдено доступных шаблонов политик")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON: {e}")
            print("Полученный ответ:", response.text)
            return None

    def get_existing_rules(self, template_id):
        """Получает список существующих правил для шаблона"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            rules = response.json()
            if isinstance(rules, dict) and 'items' in rules:
                return rules['items']
            return []
        except json.JSONDecodeError:
            return []

    def get_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def create_rule(self, template_id, rule_data):
        """Создает новое правило и возвращает response или None при ошибке"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules")
        return self.make_request("POST", url, json=rule_data)

    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет существующее правило и возвращает response или None при ошибке"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        return self.make_request("PATCH", url, json=update_data)

    def enable_rule(self, template_id, rule_id, enable=True):
        """Включает или отключает правило"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        payload = {"enabled": enable}
        return self.make_request("PATCH", url, json=payload)

    def delete_rule(self, template_id, rule_id):
        """Удаляет правило"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        return self.make_request("DELETE", url)

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
        else:
            print(f"Ошибка при получении списка действий. Код: {response.status_code}, Ответ: {response.text}")
            return None

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
        
        # Сохраняем правило в файл
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule_details, f, ensure_ascii=False, indent=2)
            print(f"Правило '{rule_name}' экспортировано в {filepath}")
            self.exported_files.append(filepath)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении правила '{rule_name}': {e}")
            return False

    def export_rules(self, export_dir="exported_rules"):
        """Экспортирует правила с различными опциями"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
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
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
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
                f.write(f"Тенант ID: {self.auth_manager.tenant_id}\n\n")
                
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

    def import_single_rule(self, template_id, file_path, selected_action_ids=None, enable_after_import=False, problem_dir=None):
        """Импортирует одно правило из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
            
            rule_name = rule_data.get('name', os.path.basename(file_path))
            print(f"\nОбработка файла: {file_path}")
            print(f"Правило: {rule_name}")
            
            if selected_action_ids is not None:
                if 'configuration' not in rule_data:
                    rule_data['configuration'] = {}
                rule_data['configuration']['actions'] = selected_action_ids
                print("Применены выбранные действия к правилу")
            
            # Получаем список существующих правил
            existing_rules = self.get_existing_rules(template_id)
            if existing_rules is None:
                error_msg = "Не удалось получить список существующих правил"
                print(error_msg)
                self.failed_files.append({
                    'file': file_path,
                    'rule': rule_name,
                    'error': error_msg,
                    'code': None,
                    'response': None
                })
                
                # Перемещаем файл в problem директорию, если она существует
                if problem_dir:
                    self._move_to_problem_directory(file_path, problem_dir, error_msg)
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
                    print(error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg)
                    return False
                    
                if response.status_code == 200:
                    print(f"Правило '{rule_name}' успешно обновлено")
                    self.success_files.append(file_path)
                    
                    if enable_after_import:
                        print(f"Включаем правило '{rule_name}'...")
                        enable_response = self.enable_rule(template_id, rule_id, True)
                        if enable_response is None or enable_response.status_code != 200:
                            error_msg = "Не удалось включить правило"
                            print(error_msg)
                            self.failed_files.append({
                                'file': file_path,
                                'rule': rule_name,
                                'error': error_msg,
                                'code': getattr(enable_response, 'status_code', None),
                                'response': getattr(enable_response, 'text', None)
                            })
                    return True
                else:
                    error_msg = f"Ошибка при обновлении правила (код {response.status_code})"
                    print(f"{error_msg}: {rule_name}")
                    print(f"Ответ сервера: {response.text}")
                    
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': response.status_code,
                        'response': response.text
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg)
                    return False
            else:
                # Создание нового правила
                response = self.create_rule(template_id, rule_data)
                if response is None:
                    error_msg = "Не удалось выполнить запрос на создание (нет ответа от сервера)"
                    print(error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg)
                    return False
                    
                if response.status_code == 201:
                    print(f"Правило '{rule_name}' успешно создано")
                    self.success_files.append(file_path)
                    
                    try:
                        new_rule = response.json()
                        rule_id = new_rule.get('id')
                        
                        if enable_after_import and rule_id:
                            print(f"Включаем правило '{rule_name}'...")
                            enable_response = self.enable_rule(template_id, rule_id, True)
                            if enable_response is None or enable_response.status_code != 200:
                                error_msg = "Не удалось включить правило"
                                print(error_msg)
                                self.failed_files.append({
                                    'file': file_path,
                                    'rule': rule_name,
                                    'error': error_msg,
                                    'code': getattr(enable_response, 'status_code', None),
                                    'response': getattr(enable_response, 'text', None)
                                })
                    except json.JSONDecodeError:
                        error_msg = "Не удалось получить ID созданного правила"
                        print(error_msg)
                        self.failed_files.append({
                            'file': file_path,
                            'rule': rule_name,
                            'error': error_msg,
                            'code': response.status_code,
                            'response': response.text
                        })
                    
                    return True
                else:
                    error_msg = f"Ошибка при создании правила (код {response.status_code})"
                    print(f"{error_msg}: {rule_name}")
                    print(f"Ответ сервера: {response.text}")
                    
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': response.status_code,
                        'response': response.text
                    })
                    
                    if problem_dir:
                        self._move_to_problem_directory(file_path, problem_dir, error_msg)
                    return False
        
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка чтения JSON: {str(e)}"
            print(f"Ошибка при чтении файла {file_path}: {error_msg}")
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg)
            return False
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            print(f"Неожиданная ошибка при обработке файла {file_path}: {error_msg}")
            self.failed_files.append({
                'file': file_path,
                'rule': os.path.basename(file_path),
                'error': error_msg,
                'code': None,
                'response': None
            })
            
            if problem_dir:
                self._move_to_problem_directory(file_path, problem_dir, error_msg)
            return False

    def _move_to_problem_directory(self, file_path, problem_dir, error_reason="", error_code=None, server_response=None):
        """Перемещает файл в problem директорию и создает файл с подробным описанием ошибки"""
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
            
            # Перемещаем исходный файл
            shutil.move(file_path, new_path)
            print(f"Файл перемещен в проблемную директорию: {new_path}")
            
            # Создаем файл с подробным описанием ошибки
            error_filename = f"{os.path.splitext(new_path)[0]}_error.txt"
            with open(error_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("ОШИБКА ПРИ ИМПОРТЕ ПРАВИЛА\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"ФАЙЛ: {filename}\n")
                
                # Читаем имя правила из исходного файла
                try:
                    with open(new_path, 'r', encoding='utf-8') as rule_file:
                        rule_data = json.load(rule_file)
                        rule_name = rule_data.get('name', 'Не указано')
                        f.write(f"ИМЯ ПРАВИЛА: {rule_name}\n")
                except:
                    f.write(f"ИМЯ ПРАВИЛА: Не удалось прочитать из файла\n")
                
                f.write(f"ВРЕМЯ ОШИБКИ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("ДЕТАЛИ ОШИБКИ:\n")
                f.write("-" * 40 + "\n")
                f.write(f"ПРИЧИНА: {error_reason}\n")
                
                if error_code is not None:
                    f.write(f"КОД ОШИБКИ: {error_code}\n")
                
                if server_response:
                    f.write("\nОТВЕТ СЕРВЕРА:\n")
                    f.write("-" * 40 + "\n")
                    
                    # Пытаемся красиво отформатировать JSON ответ
                    try:
                        response_json = json.loads(server_response)
                        formatted_response = json.dumps(response_json, indent=2, ensure_ascii=False)
                        f.write(formatted_response + "\n")
                    except:
                        f.write(server_response + "\n")
                
                # Добавляем информацию о возможных причинах ошибки
                f.write("\n\nВОЗМОЖНЫЕ ПРИЧИНЫ:\n")
                f.write("-" * 40 + "\n")
                
                if error_code == 422:
                    f.write("Ошибка 422 (Unprocessable Entity) обычно означает:\n")
                    f.write("1. Синтаксическая ошибка в коде правила\n")
                    f.write("2. Некорректный формат данных в конфигурации\n")
                    f.write("3. Несоответствие схеме валидации API\n")
                    f.write("4. Проблемы с парсингом кода правила\n\n")
                    
                    if server_response and "UnparseError" in server_response:
                        f.write("Обнаружена ошибка UnparseError - проблемы с синтаксисом кода:\n")
                        f.write("• Проверьте корректность синтаксиса JavaScript/TypeScript\n")
                        f.write("• Убедитесь в правильности закрытия скобок и кавычек\n")
                        f.write("• Проверьте отсутствие недопустимых символов\n")
                
                elif error_code == 400:
                    f.write("Ошибка 400 (Bad Request) обычно означает:\n")
                    f.write("1. Неверный формат запроса\n")
                    f.write("2. Отсутствуют обязательные поля\n")
                    f.write("3. Некорректные типы данных\n")
                
                elif error_code == 401:
                    f.write("Ошибка 401 (Unauthorized) - проблема с авторизацией\n")
                    f.write("• Проверьте актуальность токена\n")
                    f.write("• Убедитесь в правильности выбранного тенанта\n")
                
                elif error_code == 403:
                    f.write("Ошибка 403 (Forbidden) - недостаточно прав\n")
                    f.write("• Проверьте разрешения пользователя\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            print(f"Создан файл с описанием ошибки: {error_filename}")
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
        
        # Создаем директорию для проблемных файлов
        problem_dir = self._create_problem_directory(directory_path)
        
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print("Не удалось получить ID шаблона политики")
            return False
        
        print(f"\nИспользуется шаблон политики с ID: {template_id}")
        
        # Получаем список доступных действий
        actions = self.get_available_actions()
        if not actions:
            print("Не удалось получить список доступных действий")
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
                for filename in json_files:
                    file_path = os.path.abspath(os.path.join(directory_path, filename))
                    if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules, problem_dir):
                        success_count += 1
                
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
                    for i in valid_indices:
                        filename = json_files[i]
                        file_path = os.path.abspath(os.path.join(directory_path, filename))
                        if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules, problem_dir):
                            success_count += 1
                    
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