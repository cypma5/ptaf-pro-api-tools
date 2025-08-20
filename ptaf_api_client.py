import os
import json
import argparse
import requests
import uuid
from urllib.parse import urljoin
import urllib3

# Отключаем предупреждения о неверифицированном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PTAFClient:
    def __init__(self, config_file="ptaf_api_client_config.json", debug=False):
        self.config = self.load_config(config_file)
        self.base_url = self.config.get("ptaf_url")
        self.username = self.config.get("username")
        self.password = self.config.get("password")
        self.api_path = self.config.get("api_path", "/api/ptaf/v4")
        self.verify_ssl = self.config.get("verify_ssl", False)
        self.ssl_cert_path = self.config.get("ssl_cert_path")
        self.access_token = None
        self.refresh_token = None
        self.tenant_id = None
        self.fingerprint = str(uuid.uuid4()).replace("-", "")
        self.headers = {
            "User-Agent": "PTAF-API-Client/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty"
        }
        self.failed_files = []
        self.success_files = []
        self.exported_files = []
        self.debug = debug
        
        self.ssl_verify = self.verify_ssl
        if self.ssl_cert_path:
            self.ssl_verify = self.ssl_cert_path
    
    def load_config(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Конфигурационный файл {config_file} не найден")
        except json.JSONDecodeError:
            raise Exception(f"Ошибка при чтении конфигурационного файла {config_file}")
    
    def _debug_request(self, method, url, **kwargs):
        """Выводит отладочную информацию о запросе"""
        if not self.debug:
            return
        
        print("\n=== DEBUG REQUEST ===")
        print(f"{method} {url}")
        print("Headers:", json.dumps(self.headers, indent=2, ensure_ascii=False))
        if 'json' in kwargs:
            print("Body:", json.dumps(kwargs['json'], indent=2, ensure_ascii=False))
        print("====================\n")
    
    def _debug_response(self, response):
        """Выводит отладочную информацию о ответе"""
        if not self.debug:
            return
        
        print("\n=== DEBUG RESPONSE ===")
        print(f"Status: {response.status_code}")
        print("Headers:", json.dumps(dict(response.headers), indent=2, ensure_ascii=False))
        try:
            print("Body:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        except ValueError:
            print("Body:", response.text)
        print("=====================\n")
    
    def _make_request(self, method, url, max_retries=2, **kwargs):
        """Универсальный метод для выполнения запросов с обработкой 401 ошибки"""
        for attempt in range(max_retries + 1):
            try:
                self._debug_request(method, url, **kwargs)
                response = requests.request(
                    method,
                    url,
                    headers=self.headers,
                    verify=self.ssl_verify,
                    **kwargs
                )
                self._debug_response(response)

                # Если получили 401 и это не первая попытка - обновляем токен
                if response.status_code == 401 and attempt < max_retries:
                    print("Получена 401 ошибка, пытаемся обновить токен...")
                    if not self.get_jwt_tokens():
                        print("Не удалось обновить JWT токены")
                        return None
                    continue
                
                return response

            except requests.exceptions.RequestException as e:
                print(f"Ошибка при выполнении запроса: {e}")
                return None
        
        return None  # Все попытки исчерпаны

    # Auth endpoints
    def get_jwt_tokens(self):
        """Получает JWT токены (access и refresh)"""
        url = urljoin(self.base_url, f"{self.api_path}/auth/refresh_tokens")
        payload = {
            "username": self.username,
            "password": self.password,
            "fingerprint": self.fingerprint
        }
        
        response = self._make_request("POST", url, json=payload)
        if not response:
            return False
            
        if response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            print("Успешно получены JWT токены")
            return True
        else:
            print(f"Ошибка при получении токенов. Код: {response.status_code}, Ответ: {response.text}")
            return False
    
    def update_jwt_with_tenant(self):
        """Обновляет JWT токен с учетом выбранного тенанта"""
        if not self.refresh_token:
            print("Отсутствует refresh token")
            return False
        
        url = urljoin(self.base_url, f"{self.api_path}/auth/access_tokens")
        payload = {
            "refresh_token": self.refresh_token,
            "tenant_id": self.tenant_id,
            "fingerprint": self.fingerprint
        }
        
        response = self._make_request("POST", url, json=payload)
        if not response:
            return False
            
        if response.status_code == 201:
            tokens = response.json()
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            print(f"Успешно обновлены JWT токены для тенанта {self.tenant_id}")
            return True
        else:
            print(f"Ошибка при обновлении токенов. Код: {response.status_code}, Ответ: {response.text}")
            return False

    # Account endpoints
    def get_available_tenants(self):
        """Получает список доступных тенантов для текущего пользователя"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/auth/account/tenants")
        
        response = self._make_request("GET", url)
        if not response:
            return None
                
        if response.status_code == 200:
            tenants = response.json()
            if isinstance(tenants, dict) and 'items' in tenants:
                return tenants['items']
            elif isinstance(tenants, list):
                return tenants
            else:
                print(f"Неподдерживаемый формат ответа. Получен: {type(tenants)}")
                return None
        else:
            print(f"Ошибка при получении списка тенантов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    # Policy Template endpoints
    def get_policy_template_id(self):
        """Получает ID первого доступного шаблона политики"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules")
        
        response = self._make_request("GET", url)
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
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules")
        
        response = self._make_request("GET", url)
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
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        
        response = self._make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def create_rule(self, template_id, rule_data):
        """Создает новое правило и возвращает response или None при ошибке"""
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules")
        return self._make_request("POST", url, json=rule_data)

    def update_rule(self, template_id, rule_id, update_data):
        """Обновляет существующее правило и возвращает response или None при ошибке"""
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        return self._make_request("PATCH", url, json=update_data)

    def enable_rule(self, template_id, rule_id, enable=True):
        """Включает или отключает правило"""
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
        payload = {"enabled": enable}
        return self._make_request("PATCH", url, json=payload)

    # Actions endpoints
    def get_available_actions(self):
        """Получает список доступных действий"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/actions")
        
        response = self._make_request("GET", url)
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

    # Business logic methods
    def select_tenant(self):
        """Позволяет пользователю выбрать тенант из списка доступных"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        print("\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            is_default = tenant.get("is_default", False)
            description = tenant.get("description", "Без описания")
            
            default_marker = " (по умолчанию)" if is_default else ""
            print(f"{i}. {name}{default_marker}")
            print(f"   ID: {tenant_id}")
            print(f"   Описание: {description}\n")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return False
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    selected_tenant = tenants[choice]
                    self.tenant_id = selected_tenant.get("id")
                    if self.tenant_id:
                        return self.update_jwt_with_tenant()
                    print("У выбранного тенанта отсутствует ID")
                else:
                    print("Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число или 'q' для выхода.")

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
        if not self.access_token:
            if not self.get_jwt_tokens():
                return False

        # Получаем список всех тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False

        print("\nВыберите режим экспорта:")
        print("1. Сохранить все правила со всех тенантов")
        print("2. Выбрать тенант и сохранить все правила")
        print("3. Выбрать тенант и выбрать правила для сохранения")
        
        while True:
            choice = input("Ваш выбор (1-3): ")
            
            if choice == '1':
                return self._export_all_tenants_rules(tenants, export_dir)
            elif choice == '2':
                return self._export_selected_tenant_all_rules(tenants, export_dir)
            elif choice == '3':
                return self._export_selected_tenant_selected_rules(tenants, export_dir)
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _export_all_tenants_rules(self, tenants, base_export_dir):
        """Экспортирует все правила со всех тенантов"""
        success_total = 0
        for tenant in tenants:
            tenant_id = tenant.get('id')
            tenant_name = tenant.get('name', 'unknown_tenant').replace(' ', '_')
            export_dir = os.path.join(base_export_dir, tenant_name)
            
            print(f"\nЭкспорт правил для тенанта: {tenant_name}")
            
            # Переключаемся на тенанта
            self.tenant_id = tenant_id
            if not self.update_jwt_with_tenant():
                print(f"Не удалось переключиться на тенанта {tenant_name}")
                continue
            
            # Экспортируем правила
            success_count = self._export_tenant_rules(export_dir)
            success_total += success_count
        
        print(f"\nИтоговый результат:")
        print(f"Успешно экспортировано правил: {success_total}")
        return success_total > 0

    def _export_selected_tenant_all_rules(self, tenants, base_export_dir):
        """Экспортирует все правила выбранного тенанта"""
        selected_tenant = self._select_tenant(tenants)
        if not selected_tenant:
            return False
        
        tenant_name = selected_tenant.get('name', 'unknown_tenant').replace(' ', '_')
        export_dir = os.path.join(base_export_dir, tenant_name)
        
        # Переключаемся на тенанта
        self.tenant_id = selected_tenant['id']
        if not self.update_jwt_with_tenant():
            print(f"Не удалось переключиться на тенанта {tenant_name}")
            return False
        
        return self._export_tenant_rules(export_dir)

    def _export_selected_tenant_selected_rules(self, tenants, base_export_dir):
        """Экспортирует выбранные правила выбранного тенанта"""
        selected_tenant = self._select_tenant(tenants)
        if not selected_tenant:
            return False
        
        tenant_name = selected_tenant.get('name', 'unknown_tenant').replace(' ', '_')
        export_dir = os.path.join(base_export_dir, tenant_name)
        
        # Переключаемся на тенанта
        self.tenant_id = selected_tenant['id']
        if not self.update_jwt_with_tenant():
            print(f"Не удалось переключиться на тенанта {tenant_name}")
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
        
        # Выводим список правил для выбора
        print("\nДоступные правила для экспорта:")
        for i, rule in enumerate(user_rules, 1):
            print(f"{i}. {rule.get('name', 'Без названия')} (ID: {rule.get('id', 'Без ID')})")
        
        while True:
            try:
                rule_nums = input(
                    "\nВыберите номера правил для экспорта (через запятую): "
                )
                selected_indices = [int(num.strip()) - 1 for num in rule_nums.split(',') if num.strip().isdigit()]
                valid_indices = [i for i in selected_indices if 0 <= i < len(user_rules)]
                
                if not valid_indices:
                    print("Некорректные номера правил")
                    continue
                
                # Создаем директорию для экспорта
                os.makedirs(export_dir, exist_ok=True)
                
                # Экспортируем выбранные правила
                success_count = 0
                for i in valid_indices:
                    rule = user_rules[i]
                    if self.export_single_rule(template_id, rule, export_dir):
                        success_count += 1
                
                print(f"\nЭкспортировано {success_count} из {len(valid_indices)} выбранных правил")
                return success_count > 0
                
            except ValueError:
                print("Пожалуйста, введите номера через запятую (например: 1,2,3)")

    def _export_tenant_rules(self, export_dir):
        """Экспортирует все правила текущего тенанта в указанную директорию"""
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

    def _select_tenant(self, tenants):
        """Выбирает тенанта из списка и возвращает его"""
        print("\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            is_default = tenant.get("is_default", False)
            
            default_marker = " (по умолчанию)" if is_default else ""
            print(f"{i}. {name}{default_marker}")
            print(f"   ID: {tenant_id}\n")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return None
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    return tenants[choice]
                else:
                    print("Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число или 'q' для выхода.")

    def delete_all_user_rules(self):
        """Удаляет все пользовательские правила из шаблона"""
        if not self.access_token:
            if not self.get_jwt_tokens():
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

            url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
            response = self._make_request("DELETE", url)

            if response and response.status_code == 204:
                print(f"Правило '{rule_name}' успешно удалено")
                deleted_count += 1
            else:
                error_msg = response.text if response else "Не удалось выполнить запрос"
                print(f"Ошибка при удалении правила '{rule_name}': {error_msg}")

        print(f"\nУдалено {deleted_count} из {len(user_rules)} правил")
        return deleted_count > 0

    def import_single_rule(self, template_id, file_path, selected_action_ids=None, enable_after_import=False):
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
                if response is None:  # Явная проверка на None
                    error_msg = "Не удалось выполнить запрос на обновление (нет ответа от сервера)"
                    print(error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
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
                    return False
            else:
                # Создание нового правила
                response = self.create_rule(template_id, rule_data)
                if response is None:  # Явная проверка на None
                    error_msg = "Не удалось выполнить запрос на создание (нет ответа от сервера)"
                    print(error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
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
            return False

    def import_rules(self, directory_path):
        """Импортирует правила из указанной директории"""
        if not os.path.isdir(directory_path):
            print(f"Директория не найдена: {directory_path}")
            return False
        
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
            
            if not choice.strip():  # Если просто нажали Enter
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
                    if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules):
                        success_count += 1
                
                # Выводим итоговую статистику
                fail_count = len(self.failed_files)
                total_count = len(json_files)
                
                print(f"\nИтог:")
                print(f"Успешно обработано: {success_count}")
                print(f"Не удалось обработать: {fail_count}")
                print(f"Всего файлов: {total_count}")
                
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
                        if self.import_single_rule(template_id, file_path, selected_action_ids, enable_rules):
                            success_count += 1
                    
                    # Выводим итоговую статистику
                    fail_count = len([i for i in selected_indices if i not in valid_indices]) + \
                                (len(valid_indices) - success_count)
                    total_count = len(valid_indices)
                    
                    print(f"\nИтог:")
                    print(f"Успешно обработано: {success_count}")
                    print(f"Не удалось обработать: {fail_count}")
                    print(f"Всего выбрано файлов: {total_count}")
                    
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

    def get_vendor_templates(self):
        """Получает список системных шаблонов политик"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/vendor")
        
        response = self._make_request("GET", url)
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
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/user")
        
        response = self._make_request("GET", url)
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
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/user")
        payload = {
            "name": name,
            "has_user_rules": True,
            "templates": vendor_template_ids
        }
        
        response = self._make_request("POST", url, json=payload)
        if not response:
            return None
            
        if response.status_code == 201:
            print("Шаблон политики успешно создан")
            return response.json()
        else:
            print(f"Ошибка при создании шаблона политики. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def manage_policy_templates(self):
        """Интерактивное управление шаблонами политик"""
        while True:
            print("\nУправление шаблонами политик:")
            print("1. Показать список системных шаблонов")
            print("2. Показать список пользовательских шаблонов")
            print("3. Создать новый шаблон политики")
            print("4. Создать политику на основе PTAF3")
            print("5. Просмотреть правила шаблона")
            print("6. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-6): ")
            
            if choice == '1':
                # Показать системные шаблоны
                templates = self.get_vendor_templates()
                if not templates:
                    print("Не удалось получить список системных шаблонов или список пуст")
                    continue
                
                print("\nСистемные шаблоны политик:")
                for i, template in enumerate(templates, 1):
                    print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')}, Тип: {template.get('type')})")
            
            elif choice == '2':
                # Показать пользовательские шаблоны
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
                # Создать новый шаблон
                print("\nСоздание нового шаблона политики")
                
                # Получаем список системных шаблонов для выбора
                vendor_templates = self.get_vendor_templates()
                if not vendor_templates:
                    print("Не удалось получить список системных шаблонов для создания")
                    continue
                
                # Вводим имя нового шаблона
                name = input("Введите имя нового шаблона: ").strip()
                if not name:
                    print("Имя шаблона не может быть пустым")
                    continue
                
                # Выбираем системные шаблоны для включения
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
                
                # Создаем шаблон
                result = self.create_user_template(name, [selected_template])
                if result:
                    print(f"Шаблон '{name}' успешно создан с ID: {result.get('id')}")
            
            elif choice == '4':
                # Создание политики на основе PTAF3
                self.import_ptaf3_policy()
            
            elif choice == '5':
                # Просмотр правил шаблона
                templates = self.get_user_templates()
                if not templates:
                    print("Не удалось получить список пользовательских шаблонов или список пуст")
                    continue
                
                print("\nДоступные пользовательские шаблоны:")
                for i, template in enumerate(templates, 1):
                    print(f"{i}. {template.get('name', 'Без названия')} (ID: {template.get('id')})")
                
                while True:
                    try:
                        choice = input("\nВыберите номер шаблона для просмотра правил (или 'q' для выхода): ")
                        if choice.lower() == 'q':
                            break
                        
                        selected_index = int(choice) - 1
                        if 0 <= selected_index < len(templates):
                            template = templates[selected_index]
                            template_id = template.get('id')
                            template_name = template.get('name', 'Без названия')
                            
                            rules = self.get_template_rules(template_id)
                            if rules is None:
                                print(f"Не удалось получить правила для шаблона '{template_name}'")
                                continue
                            
                            print(f"\nПравила шаблона '{template_name}':")
                            for i, rule in enumerate(rules, 1):
                                print(f"{i}. {rule.get('name', 'Без названия')} (ID: {rule.get('id')}, Включено: {'Да' if rule.get('enabled') else 'Нет'})")
                            
                            # Дополнительное меню для работы с конкретным правилом
                            rule_choice = input(
                                "\nВыберите:\n"
                                "1. Просмотреть детали правила\n"
                                "2. Изменить правило\n"
                                "3. Вернуться к списку шаблонов\n"
                                "Ваш выбор (1-3): "
                            )
                            
                            if rule_choice == '1':
                                # Просмотр деталей правила
                                rule_num = int(input("Введите номер правила для просмотра: ")) - 1
                                if 0 <= rule_num < len(rules):
                                    rule = rules[rule_num]
                                    rule_id = rule.get('id')
                                    rule_details = self.get_template_rule_details(template_id, rule_id)
                                    if rule_details:
                                        print(f"\nДетали правила '{rule.get('name')}':")
                                        print(json.dumps(rule_details, indent=2, ensure_ascii=False))
                                    else:
                                        print("Не удалось получить детали правила")
                                else:
                                    print("Некорректный номер правила")
                            
                            elif rule_choice == '2':
                                # Изменение правила
                                rule_num = int(input("Введите номер правила для изменения: ")) - 1
                                if 0 <= rule_num < len(rules):
                                    rule = rules[rule_num]
                                    rule_id = rule.get('id')
                                    rule_name = rule.get('name', 'Без названия')
                                    
                                    print(f"\nИзменение правила '{rule_name}'")
                                    print("Доступные поля для изменения:")
                                    print("1. Название")
                                    print("2. Описание")
                                    print("3. Состояние (включено/выключено)")
                                    
                                    field_choice = input("Выберите поле для изменения (1-3): ")
                                    update_data = {}
                                    
                                    if field_choice == '1':
                                        new_name = input("Введите новое название: ").strip()
                                        if new_name:
                                            update_data['name'] = new_name
                                        else:
                                            print("Название не может быть пустым")
                                            continue
                                    elif field_choice == '2':
                                        new_desc = input("Введите новое описание: ").strip()
                                        update_data['description'] = new_desc
                                    elif field_choice == '3':
                                        new_state = input("Включить правило? (y/n): ").lower() == 'y'
                                        update_data['enabled'] = new_state
                                    else:
                                        print("Некорректный выбор")
                                        continue
                                    
                                    if update_data:
                                        response = self.update_template_rule(template_id, rule_id, update_data)
                                        if response and response.status_code == 200:
                                            print("Правило успешно обновлено")
                                        else:
                                            error = response.text if response else "Неизвестная ошибка"
                                            print(f"Ошибка при обновлении правила: {error}")
                                    else:
                                        print("Нечего обновлять")
                                else:
                                    print("Некорректный номер правила")
                            
                            elif rule_choice == '3':
                                break
                            
                            else:
                                print("Некорректный выбор")
                        
                        else:
                            print("Некорректный номер шаблона")
                    except ValueError:
                        print("Пожалуйста, введите число")
            
            elif choice == '6':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def update_http_methods_rule(self, template_id, allowed_methods):
        """Обновляет правило method_not_allowed с новыми разрешенными методами"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило method_not_allowed
        method_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'method_not_allowed':
                method_rule = rule
                break
        
        if not method_rule:
            print("В шаблоне не найдено правило method_not_allowed")
            return False
        
        rule_id = method_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": {
                "allowed_methods": allowed_methods
            }
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print("Правило method_not_allowed успешно обновлено")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def update_frame_options_rule(self, template_id, x_frame_options):
        """Обновляет правило frame_options с новыми значениями"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило frame_options
        frame_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'frame_options':
                frame_rule = rule
                break
        
        if not frame_rule:
            print("В шаблоне не найдено правило frame_options")
            return False
        
        rule_id = frame_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Получаем текущие детали правила
        rule_details = self.get_template_rule_details(template_id, rule_id)
        if not rule_details:
            print("Не удалось получить детали правила")
            return False
        
        # Допустимые значения для преобразования
        valid_options = {
            "SAMEORIGIN": "SAMEORIGIN",
            "DENY": "DENY",
            "ALLOW-FROM": "ALLOW-FROM"
        }
        
        # Проверяем и нормализуем значение
        normalized_option = valid_options.get(x_frame_options.upper())
        if not normalized_option:
            print(f"Некорректное значение x_frame_options: {x_frame_options}")
            return False
        
        # Сохраняем все существующие переменные
        current_variables = rule_details.get('variables', {})
        updated_variables = {**current_variables}
        
        # Обновляем параметры
        updated_variables.update({
            "override": True,
            "mode": normalized_option
        })
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": updated_variables
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print(f"Правило frame_options успешно обновлено (X-Frame-Options: {normalized_option})")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def update_http_limit_rule(self, template_id, max_headers):
        """Обновляет правило http_limit_exceeded с новыми значениями лимитов"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило http_limit_exceeded
        limit_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'http_limit_exceeded':
                limit_rule = rule
                break
        
        if not limit_rule:
            print("В шаблоне не найдено правило http_limit_exceeded")
            return False
        
        rule_id = limit_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Получаем текущие детали правила
        rule_details = self.get_template_rule_details(template_id, rule_id)
        if not rule_details:
            print("Не удалось получить детали правила")
            return False
        
        try:
            max_headers_int = int(max_headers)
        except (ValueError, TypeError):
            print(f"Некорректное значение max_headers: {max_headers}")
            return False
        
        # Сохраняем все существующие переменные и обновляем только нужные
        current_variables = rule_details.get('variables', {})
        current_soft_limits = current_variables.get('soft_limits', {})
        
        # Создаем копию всех текущих параметров
        updated_variables = {**current_variables}
        updated_soft_limits = {**current_soft_limits}
        
        # Обновляем только нужный параметр
        updated_soft_limits['max_headers_number'] = max_headers_int
        updated_variables['soft_limits'] = updated_soft_limits
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": updated_variables
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print(f"Правило http_limit_exceeded успешно обновлено (max_headers: {max_headers_int})")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def update_content_type_rule(self, template_id, content_types):
        """Обновляет правило invalid_content_type с новыми разрешенными типами контента"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило invalid_content_type
        content_type_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'invalid_content_type':
                content_type_rule = rule
                break
        
        if not content_type_rule:
            print("В шаблоне не найдено правило invalid_content_type")
            return False
        
        rule_id = content_type_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Получаем текущие детали правила
        rule_details = self.get_template_rule_details(template_id, rule_id)
        if not rule_details:
            print("Не удалось получить детали правила")
            return False
        
        # Сохраняем все существующие переменные и обновляем только нужные
        current_variables = rule_details.get('variables', {})
        
        # Создаем копию всех текущих параметров
        updated_variables = {**current_variables}
        
        # Обновляем только нужный параметр
        updated_variables['allowed_content_types'] = content_types
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": updated_variables
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print("Правило invalid_content_type успешно обновлено")
            print("Разрешенные типы контента:")
            for ct in content_types:
                print(f" - {ct}")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def update_http_limits_rule(self, template_id, max_headers):
        """Обновляет правило http_limit_exceeded с новыми значениями лимитов"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило http_limit_exceeded
        limit_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'http_limit_exceeded':
                limit_rule = rule
                break
        
        if not limit_rule:
            print("В шаблоне не найдено правило http_limit_exceeded")
            return False
        
        rule_id = limit_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Преобразуем max_headers в число (если это строка или словарь)
        try:
            if isinstance(max_headers, dict):
                max_headers = int(max_headers.get('$numberLong', 20))
            elif isinstance(max_headers, str):
                max_headers = int(max_headers)
            else:
                max_headers = int(max_headers)
        except (ValueError, TypeError):
            print(f"Некорректное значение max_headers: {max_headers}, будет использовано значение по умолчанию 20")
            max_headers = 20
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": {
                "soft_limits": {
                    "max_headers_number": max_headers
                }
            }
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print(f"Правило http_limit_exceeded успешно обновлено (max_headers_number: {max_headers})")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def get_template_rule_details(self, template_id, rule_id):
        """Получает детали конкретного правила шаблона"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        
        response = self._make_request("GET", url)
        if not response:
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def update_template_rule(self, template_id, rule_id, update_data):
        """Обновляет правило шаблона политики"""
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/user/{template_id}/rules/{rule_id}")
        return self._make_request("PATCH", url, json=update_data)

    def get_template_rules(self, template_id):
        """Получает список правил для шаблона политики"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/user/{template_id}/rules")
        
        response = self._make_request("GET", url)
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

    def import_ptaf3_policy(self):
        """Импорт политики из PTAF3"""
        print("\nИмпорт политики из PTAF3")
        
        # Проверяем наличие папки ptaf3
        ptaf3_dir = os.path.join(os.path.dirname(__file__), "ptaf3")
        if not os.path.exists(ptaf3_dir):
            print(f"Папка ptaf3 не найдена: {ptaf3_dir}")
            return False
        
        # Получаем список доступных папок в ptaf3
        available_folders = [f for f in os.listdir(ptaf3_dir) 
                           if os.path.isdir(os.path.join(ptaf3_dir, f))]
        
        if not available_folders:
            print("В папке ptaf3 нет доступных подпапок")
            return False
        
        # Выбираем папку
        print("\nДоступные папки с политиками PTAF3:")
        for i, folder in enumerate(available_folders, 1):
            print(f"{i}. {folder}")
        
        while True:
            try:
                choice = input("\nВыберите папку (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return False
                
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(available_folders):
                    selected_folder = available_folders[selected_index]
                    break
                else:
                    print("Некорректный номер папки")
            except ValueError:
                print("Пожалуйста, введите число")
        
        # Ищем файл policies.json в выбранной папке
        policy_file = os.path.join(ptaf3_dir, selected_folder, "policies.json")
        if not os.path.exists(policy_file):
            print(f"Файл policies.json не найден в папке {selected_folder}")
            return False
        
        # Загружаем политики из файла
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                ptaf3_policies = json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла policies.json: {e}")
            return False
        
        if not isinstance(ptaf3_policies, list) or not ptaf3_policies:
            print("Файл policies.json не содержит валидных политик")
            return False
        
        # Выводим список доступных политик
        print("\nДоступные политики PTAF3:")
        for i, policy in enumerate(ptaf3_policies, 1):
            policy_name = policy.get('name', 'Без названия')
            policy_id = policy.get('_id', {}).get('$oid', 'Без ID')
            print(f"{i}. {policy_name} (ID: {policy_id})")
        
        # Выбираем режим импорта
        while True:
            choice = input(
                "\nВыберите:\n"
                "1. Импортировать все политики\n"
                "2. Выбрать конкретные политики\n"
                "3. Отмена\n"
                "Ваш выбор (1-3): "
            )
            
            if choice == '1':
                # Импорт всех политик
                selected_policies = ptaf3_policies
                break
            elif choice == '2':
                # Выбор конкретных политик
                selected_indices = input(
                    "Введите номера политик для импорта (через запятую): "
                ).strip()
                
                try:
                    selected_indices = [int(num.strip()) - 1 for num in selected_indices.split(',') 
                                      if num.strip().isdigit()]
                    valid_indices = [i for i in selected_indices if 0 <= i < len(ptaf3_policies)]
                    
                    if not valid_indices:
                        print("Некорректные номера политик")
                        continue
                    
                    selected_policies = [ptaf3_policies[i] for i in valid_indices]
                    break
                except ValueError:
                    print("Пожалуйста, введите номера через запятую")
            elif choice == '3':
                return False
            else:
                print("Некорректный выбор")
        
        # Получаем список системных шаблонов
        vendor_templates = self.get_vendor_templates()
        if not vendor_templates:
            print("Не удалось получить список системных шаблонов")
            return False
        
        # Ищем Default Template
        default_template = None
        for template in vendor_templates:
            if template.get('name') == 'Default Template':
                default_template = template
                break
        
        if not default_template:
            print("Не найден Default Template среди системных шаблонов")
            return False
        
        # Для каждой выбранной политики
        success_count = 0
        for policy in selected_policies:
            policy_name = policy.get('name', 'Без названия')
            new_template_name = f"PTAF3_{policy_name}"
            
            # Сре
            # Создаем новый шаблон на основе Default Template
            result = self.create_user_template(
                name=new_template_name,
                vendor_template_ids=[default_template['id']]
            )
            
            if not result:
                print(f"Не удалось создать шаблон для политики '{policy_name}'")
                continue
            
            template_id = result.get('id')
            print(f"Создан новый шаблон '{new_template_name}' (ID: {template_id})")
            
            # Конвертируем параметры политики PTAF3 в правила PTAF4
            if self.convert_ptaf3_policy(policy, template_id):
                success_count += 1
        
        print(f"\nИтог: успешно обработано {success_count} из {len(selected_policies)} политик")
        return success_count > 0

    def update_cookie_security_rule(self, template_id, response_filter):
        """Обновляет правило cookie_security на основе ResponseFilter из PTAF3"""
        if not template_id:
            print("Не указан ID шаблона")
            return False
        
        # Получаем все правила шаблона
        rules = self.get_template_rules(template_id)
        if not rules:
            print("Не удалось получить правила шаблона")
            return False
        
        # Ищем правило cookie_security
        cookie_rule = None
        for rule in rules:
            if rule.get('rule_id') == 'cookie_security':
                cookie_rule = rule
                break
        
        if not cookie_rule:
            print("В шаблоне не найдено правило cookie_security")
            return False
        
        rule_id = cookie_rule.get('id')
        if not rule_id:
            print("У правила отсутствует ID")
            return False
        
        # Получаем текущие детали правила
        rule_details = self.get_template_rule_details(template_id, rule_id)
        if not rule_details:
            print("Не удалось получить детали правила")
            return False
        
        # Подготавливаем обновленные параметры для cookie security
        security_attributes = {
            "secure": {
                "enabled": bool(response_filter.get("secure", False))
            },
            "httponly": {
                "enabled": bool(response_filter.get("http_only", False))
            },
            "samesite": {
                "enabled": True,  # По умолчанию
                "mode": "Strict",  # По умолчанию
                "override": True   # По умолчанию
            }
        }
        
        # Сохраняем все существующие переменные
        current_variables = rule_details.get('variables', {})
        updated_variables = {**current_variables}
        
        # Обновляем только security_attributes, сохраняя остальные параметры
        updated_variables['security_attributes'] = security_attributes
        
        # Подготавливаем данные для обновления
        update_data = {
            "variables": updated_variables
        }
        
        # Обновляем правило
        response = self.update_template_rule(template_id, rule_id, update_data)
        if response and response.status_code == 200:
            print("Правило cookie_security успешно обновлено")
            print("Настройки cookie:")
            print(f" - Secure: {security_attributes['secure']['enabled']}")
            print(f" - HttpOnly: {security_attributes['httponly']['enabled']}")
            return True
        else:
            error = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при обновлении правила: {error}")
            return False

    def convert_ptaf3_policy(self, ptaf3_policy, template_id):
        """Конвертирует политику PTAF3 в правила PTAF4"""
        if not ptaf3_policy or not isinstance(ptaf3_policy, dict):
            print("Некорректные данные политики PTAF3")
            return False
        
        policy_name = ptaf3_policy.get('name', 'Unknown')
        print(f"\nКонвертация политики PTAF3: {policy_name}")
        
        # Обрабатываем HTTP Protector
        http_protector = ptaf3_policy.get('HTTPProtector', {})
        if http_protector:
            # Обновляем разрешенные методы
            allowed_methods = http_protector.get('allowed_methods', [])
            if allowed_methods:
                print(f"Обнаружены разрешенные методы: {', '.join(allowed_methods)}")
                if not self.update_http_methods_rule(template_id, allowed_methods):
                    print("Не удалось обновить разрешенные HTTP методы")
            
            # Обновляем лимиты заголовков
            max_headers = http_protector.get('max_headers', {}).get('$numberLong')
            if max_headers:
                print(f"Обнаружен max_headers: {max_headers}")
                if not self.update_http_limit_rule(template_id, max_headers):
                    print("Не удалось обновить лимит заголовков")
            
            # Обновляем разрешенные типы контента
            content_types = http_protector.get('content_types', [])
            if content_types:
                print(f"Обнаружены разрешенные типы контента: {', '.join(content_types)}")
                if not self.update_content_type_rule(template_id, content_types):
                    print("Не удалось обновить разрешенные типы контента")
        
        # Обрабатываем Response Filter
        response_filter = ptaf3_policy.get('ResponseFilter', {})
        if response_filter:
            print("Обнаружены настройки ResponseFilter")
            if not self.update_cookie_security_rule(template_id, response_filter):
                print("Не удалось обновить настройки cookie security")
        
        return True

    def get_traffic_settings(self):
        """Получает текущие настройки трафика"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return None
        
        if not self.tenant_id:
            print("Не выбран тенант")
            return None
        
        url = urljoin(self.base_url, f"{self.api_path}/config/traffic_settings")
        
        response = self._make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            settings = response.json()
            print("Успешно получены параметры traffic_settings")
            return settings
        else:
            print(f"Ошибка при получении параметров traffic_settings. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def update_traffic_settings(self, settings_data):
        """Обновляет настройки трафика"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return False
        
        if not self.tenant_id:
            print("Не выбран тенант")
            return False
        
        url = urljoin(self.base_url, f"{self.api_path}/config/traffic_settings")
        
        response = self._make_request("PATCH", url, json=settings_data)
        if not response:
            return False
            
        if response.status_code == 200:
            print("Параметры traffic_settings успешно обновлены")
            return True
        else:
            print(f"Ошибка при обновлении параметров traffic_settings. Код: {response.status_code}, Ответ: {response.text}")
            return False

    def manage_traffic_settings(self):
        """Интерактивное управление настройками трафика"""
        current_settings = self.get_traffic_settings() or {}
        
        while True:
            print("\nУправление настройками трафика:")
            print("1. NGINX: Настройки загрузки файлов")
            print("2. Envoy Proxy: Sticky Session")
            print("3. Envoy Core: Настройки TLS")
            print("4. NGINX: Настройки access.log")
            print("5. NGINX: Настройки error.log")
            print("6. Система: Лимиты приложений")
            print("7. Система: Debug режим")
            print("8. Просмотр текущих настроек")
            print("9. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-9): ")
            
            if choice == '1':
                current_settings = self._edit_file_upload_settings(current_settings)
            
            elif choice == '2':
                current_settings = self._edit_sticky_session_settings(current_settings)
            
            elif choice == '3':
                current_settings = self._edit_envoy_core_settings(current_settings)
            
            elif choice == '4':
                current_settings = self._edit_logging_settings(current_settings)
            
            elif choice == '5':
                current_settings = self._edit_error_log_settings(current_settings)
            
            elif choice == '6':
                current_settings = self._edit_limit_settings(current_settings)
            
            elif choice == '7':
                current_settings = self._edit_debug_settings(current_settings)
            
            elif choice == '8':
                self._show_current_settings(current_settings)
            
            elif choice == '9':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _show_current_settings(self, settings):
        """Выводит текущие настройки"""
        print("\nТекущие настройки:")
        print(json.dumps(settings, indent=2, ensure_ascii=False))

    def _edit_file_upload_settings(self, current_settings):
        """NGINX: Настройки загрузки файлов"""
        print("\nNGINX: Настройки загрузки файлов:")
        
        new_settings = current_settings.copy()
        
        print("Примеры значений: 10m (10 мегабайт), 1g (1 гигабайт), 0 - без ограничений")
        new_size = input(
            f"Максимальный размер загружаемого файла [{current_settings.get('core_nginx_client_max_body_size', '1g')}]: "
        )
        
        if new_size:
            new_settings['core_nginx_client_max_body_size'] = new_size
        
        if self.update_traffic_settings(new_settings):
            print("Настройки загрузки файлов обновлены")
            return new_settings
        return current_settings

    def _edit_sticky_session_settings(self, current_settings):
        """Envoy Proxy: Sticky Session"""
        print("\nEnvoy Proxy: Sticky Session:")
        
        new_settings = current_settings.copy()
        current_cookie = current_settings.get('envoy_proxy_stateful_session_cookie', {})
        
        # Включение/выключение
        enabled = input(f"Включить Sticky Session? (y/n) [{'y' if current_cookie.get('enabled', False) else 'n'}]: ").lower() == 'y'
        
        if enabled:
            cookie_settings = {
                'enabled': True,
                'name': input(f"Имя куки [{current_cookie.get('name', 'STICKY_SESSION')}]: ") or current_cookie.get('name', 'STICKY_SESSION'),
                'path': input(f"Путь к ресурсу [{current_cookie.get('path', '/')}]: ") or current_cookie.get('path', '/'),
                'ttl': input(f"Время жизни куки (например, 3600s) [{current_cookie.get('ttl', '3600s')}]: ") or current_cookie.get('ttl', '3600s')
            }
            new_settings['envoy_proxy_stateful_session_cookie'] = cookie_settings
        else:
            new_settings['envoy_proxy_stateful_session_cookie'] = {'enabled': False}
        
        if self.update_traffic_settings(new_settings):
            print("Настройки Sticky Session обновлены")
            return new_settings
        return current_settings

    def _edit_envoy_core_settings(self, current_settings):
        """Envoy Core: Настройки TLS"""
        print("\nEnvoy Core: Настройки TLS")
        
        new_settings = current_settings.copy()
        
        # Минимальная версия TLS
        print("\nДоступные версии протоколов:")
        print("TLS_AUTO, TLSv1_0, TLSv1_1, TLSv1_2, TLSv1_3")
        min_version = input(
            f"Минимальная версия TLS [{current_settings.get('core_envoy_cds_tls_minimum_protocol_version', 'TLS_AUTO')}]: "
        )
        if min_version:
            new_settings['core_envoy_cds_tls_minimum_protocol_version'] = min_version
        
        # Максимальная версия TLS
        max_version = input(
            f"Максимальная версия TLS [{current_settings.get('core_envoy_cds_tls_maximum_protocol_version', 'TLS_AUTO')}]: "
        )
        if max_version:
            new_settings['core_envoy_cds_tls_maximum_protocol_version'] = max_version
        
        if self.update_traffic_settings(new_settings):
            print("Настройки Envoy Core обновлены")
            return new_settings
        return current_settings

    def _edit_logging_settings(self, current_settings):
        """NGINX: Настройки access.log"""
        print("\nNGINX: Настройки access.log:")
        
        new_settings = current_settings.copy()
        
        # Включение access log
        access_log_enabled = input(
            f"Включить access log? (y/n) [{'y' if current_settings.get('core_nginx_access_log', False) else 'n'}]: "
        ).lower() == 'y'
        new_settings['core_nginx_access_log'] = access_log_enabled
        
        if access_log_enabled:
            # Формат access log
            print("\nДоступные форматы access log:")
            print("1. Combined (стандартный)")
            print("2. Extended (с X-Forwarded-For)")
            print("3. Minimal (основные поля)")
            print("4. Пользовательский формат")
            
            choice = input("Выберите формат [1-4]: ")
            
            if choice == '1':
                new_settings['core_nginx_access_log_format'] = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
            elif choice == '2':
                new_settings['core_nginx_access_log_format'] = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"'
            elif choice == '3':
                new_settings['core_nginx_access_log_format'] = '$remote_addr [$time_local] "$request" $status $body_bytes_sent'
            elif choice == '4':
                custom_format = input("Введите свой формат: ")
                if custom_format:
                    new_settings['core_nginx_access_log_format'] = custom_format
        
        if self.update_traffic_settings(new_settings):
            print("Настройки логирования обновлены")
            return new_settings
        return current_settings

    def _edit_error_log_settings(self, current_settings):
        """NGINX: Настройки error.log"""
        print("\nNGINX: Настройки error.log")
        
        new_settings = current_settings.copy()
        
        # Включение/выключение error log
        error_log_enabled = input(
            f"Включить error.log? (y/n) [{'y' if current_settings.get('core_nginx_error_log_enabled', False) else 'n'}]: "
        ).lower() == 'y'
        
        new_settings['core_nginx_error_log_enabled'] = error_log_enabled
        
        if error_log_enabled:
            # Уровень логирования
            print("\nДоступные уровни логирования:")
            print("emerg, alert, crit, error, warn, notice, info, debug")
            log_level = input(
                f"Уровень логирования [{current_settings.get('core_nginx_log_level', 'error')}]: "
            )
            if log_level:
                new_settings['core_nginx_log_level'] = log_level
        
        if self.update_traffic_settings(new_settings):
            print("Настройки error.log обновлены")
            return new_settings
        return current_settings

    def _edit_limit_settings(self, current_settings):
        """Система: Лимиты приложений"""
        print("\nСистема: Лимиты приложений:")
        
        new_settings = current_settings.copy()
        
        try:
            new_limit = int(input(
                f"Максимальное количество приложений [{current_settings.get('max_applications_count', 30)}]: "
            ))
            new_settings['max_applications_count'] = new_limit
        except ValueError:
            print("Ошибка: введите целое число")
            return current_settings
        
        if self.update_traffic_settings(new_settings):
            print("Настройки лимитов обновлены")
            return new_settings
        return current_settings

    def _edit_debug_settings(self, current_settings):
        """Система: Debug режим"""
        print("\nСистема: Debug режим:")
        
        new_settings = current_settings.copy()
        
        debug_enabled = input(f"Включить debug режим? (y/n) [{'y' if current_settings.get('core_debug_mode', False) else 'n'}]: ").lower() == 'y'
        
        if debug_enabled:
            new_settings.update({
                'core_debug_mode': True,
                'core_nginx_log_level': 'debug',
                'envoy_proxy_log_level': 'debug',
                'core_ptaf_log_level': 'debug'
            })
        else:
            new_settings.update({
                'core_debug_mode': False,
                'core_nginx_log_level': 'error',
                'envoy_proxy_log_level': 'info',
                'core_ptaf_log_level': 'info'
            })
        
        if self.update_traffic_settings(new_settings):
            print("Настройки Debug обновлены")
            return new_settings
        return current_settings


def main():
    parser = argparse.ArgumentParser(description="PTAF PRO API Client")
    parser.add_argument(
        "--source",
        help="Путь к директории с JSON файлами правил для импорта"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Экспортировать существующие правила"
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Удалить все пользовательские правила"
    )
    parser.add_argument(
        "--policy",
        action="store_true",
        help="Управление шаблонами политик"
    )
    parser.add_argument(
        "--traffic-settings",
        action="store_true",
        help="Управление настройками трафика"
    )
    parser.add_argument(
        "--config",
        default="ptaf_api_client_config.json",
        help="Путь к конфигурационному файлу"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить отладочный режим (показывать полные запросы и ответы)"
    )
    args = parser.parse_args()

    try:
        client = PTAFClient(config_file=args.config, debug=args.debug)
        
        # Сначала получаем токены
        if not client.get_jwt_tokens():
            print("Не удалось получить JWT токены")
            return

        # Если нет аргументов - запускаем интерактивный режим
        if not any([args.source, args.export, args.delete_all, args.policy, args.traffic_settings]):
            while True:
                print("\nГлавное меню:")
                print("1. Импорт правил")
                print("2. Экспорт правил")
                print("3. Удалить все пользовательские правила")
                print("4. Управление шаблонами политик")
                print("5. Управление настройками трафика")
                print("6. Выход")
                
                choice = input("\nВыберите действие (1-6): ")
                
                if choice == '1':
                    source_dir = input("Введите путь к директории с JSON файлами: ").strip()
                    if source_dir and os.path.isdir(source_dir):
                        if not client.select_tenant():
                            print("Не удалось выбрать тенант")
                            continue
                        client.import_rules(directory_path=source_dir)
                    else:
                        print("Указанная директория не существует")
                
                elif choice == '2':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.export_rules()
                
                elif choice == '3':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.delete_all_user_rules()
                
                elif choice == '4':
                    client.manage_policy_templates()
                
                elif choice == '5':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    if hasattr(client, 'manage_traffic_settings'):
                        client.manage_traffic_settings()
                    else:
                        print("Функция управления настройками трафика недоступна")
                
                elif choice == '6':
                    return
                
                else:
                    print("Некорректный выбор. Попробуйте снова.")
        
        # Обработка аргументов командной строки
        else:
            if args.export:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.export_rules()
            
            elif args.source:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.import_rules(directory_path=args.source)
            
            elif args.delete_all:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.delete_all_user_rules()
            
            elif args.policy:
                client.manage_policy_templates()
            
            elif args.traffic_settings:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                if hasattr(client, 'manage_traffic_settings'):
                    client.manage_traffic_settings()
                else:
                    print("Функция управления настройками трафика недоступна")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()