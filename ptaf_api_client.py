import os
import json
import argparse
import requests
import uuid
from urllib.parse import urljoin
import urllib3
from colorama import init, Fore, Style

# Отключаем предупреждения о неверифицированном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Инициализация colorama для цветного вывода
init(autoreset=True)

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
        
        print(Fore.CYAN + "\n=== DEBUG REQUEST ===")
        print(Fore.YELLOW + f"{method} {url}")
        print(Fore.YELLOW + "Headers:", json.dumps(self.headers, indent=2, ensure_ascii=False))
        if 'json' in kwargs:
            print(Fore.YELLOW + "Body:", json.dumps(kwargs['json'], indent=2, ensure_ascii=False))
        print(Fore.CYAN + "====================\n")
    
    def _debug_response(self, response):
        """Выводит отладочную информацию о ответе"""
        if not self.debug:
            return
        
        print(Fore.CYAN + "\n=== DEBUG RESPONSE ===")
        print(Fore.YELLOW + f"Status: {response.status_code}")
        print(Fore.YELLOW + "Headers:", json.dumps(dict(response.headers), indent=2, ensure_ascii=False))
        try:
            print(Fore.YELLOW + "Body:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        except ValueError:
            print(Fore.YELLOW + "Body:", response.text)
        print(Fore.CYAN + "=====================\n")
    
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
                    print(Fore.YELLOW + "Получена 401 ошибка, пытаемся обновить токен...")
                    if not self.get_jwt_tokens():
                        print(Fore.RED + "Не удалось обновить JWT токены")
                        return None
                    continue
                
                return response

            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"Ошибка при выполнении запроса: {e}")
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
            print(Fore.GREEN + "Успешно получены JWT токены")
            return True
        else:
            print(Fore.RED + f"Ошибка при получении токенов. Код: {response.status_code}, Ответ: {response.text}")
            return False
    
    def update_jwt_with_tenant(self):
        """Обновляет JWT токен с учетом выбранного тенанта"""
        if not self.refresh_token:
            print(Fore.RED + "Отсутствует refresh token")
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
            print(Fore.GREEN + f"Успешно обновлены JWT токены для тенанта {self.tenant_id}")
            return True
        else:
            print(Fore.RED + f"Ошибка при обновлении токенов. Код: {response.status_code}, Ответ: {response.text}")
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
                print(Fore.YELLOW + f"Неподдерживаемый формат ответа. Получен: {type(tenants)}")
                return None
        else:
            print(Fore.RED + f"Ошибка при получении списка тенантов. Код: {response.status_code}, Ответ: {response.text}")
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
                print(Fore.RED + "Не найдено доступных шаблонов политик")
                return None
                
        except json.JSONDecodeError as e:
            print(Fore.RED + f"Ошибка декодирования JSON: {e}")
            print(Fore.YELLOW + "Полученный ответ:", response.text)
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
                print(Fore.YELLOW + f"Неподдерживаемый формат ответа. Получен: {type(actions)}")
                return None
        else:
            print(Fore.RED + f"Ошибка при получении списка действий. Код: {response.status_code}, Ответ: {response.text}")
            return None

    # Business logic methods
    def select_tenant(self):
        """Позволяет пользователю выбрать тенант из списка доступных"""
        tenants = self.get_available_tenants()
        if not tenants:
            print(Fore.RED + "Не удалось получить список тенантов")
            return False
        
        print(Fore.CYAN + "\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            is_default = tenant.get("is_default", False)
            description = tenant.get("description", "Без описания")
            
            default_marker = Fore.GREEN + " (по умолчанию)" if is_default else ""
            print(f"{Fore.CYAN}{i}. {name}{default_marker}")
            print(f"   ID: {tenant_id}")
            print(f"   Описание: {description}\n")
        
        while True:
            try:
                choice = input(f"{Fore.CYAN}\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return False
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    selected_tenant = tenants[choice]
                    self.tenant_id = selected_tenant.get("id")
                    if self.tenant_id:
                        return self.update_jwt_with_tenant()
                    print(Fore.YELLOW + "У выбранного тенанта отсутствует ID")
                else:
                    print(Fore.YELLOW + "Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print(Fore.YELLOW + "Пожалуйста, введите число или 'q' для выхода.")

    def export_single_rule(self, template_id, rule, export_dir):
        """Экспортирует одно правило"""
        rule_id = rule.get('id')
        rule_name = rule.get('name', 'unnamed_rule')
        
        # Получаем детали правила
        rule_details = self.get_rule_details(template_id, rule_id)
        if not rule_details:
            print(Fore.RED + f"Не удалось получить детали правила {rule_name} (ID: {rule_id})")
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
            print(Fore.GREEN + f"Правило '{rule_name}' экспортировано в {filepath}")
            self.exported_files.append(filepath)
            return True
        except Exception as e:
            print(Fore.RED + f"Ошибка при сохранении правила '{rule_name}': {e}")
            return False

    def export_rules(self, export_dir="exported_rules"):
        """Экспортирует правила с различными опциями"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return False

        # Получаем список всех тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print(Fore.RED + "Не удалось получить список тенантов")
            return False

        print(Fore.CYAN + "\nВыберите режим экспорта:")
        print("1. Сохранить все правила со всех тенантов")
        print("2. Выбрать тенант и сохранить все правила")
        print("3. Выбрать тенант и выбрать правила для сохранения")
        
        while True:
            choice = input(f"{Fore.CYAN}Ваш выбор (1-3): ")
            
            if choice == '1':
                return self._export_all_tenants_rules(tenants, export_dir)
            elif choice == '2':
                return self._export_selected_tenant_all_rules(tenants, export_dir)
            elif choice == '3':
                return self._export_selected_tenant_selected_rules(tenants, export_dir)
            else:
                print(Fore.YELLOW + "Некорректный выбор. Попробуйте снова.")

    def _export_all_tenants_rules(self, tenants, base_export_dir):
        """Экспортирует все правила со всех тенантов"""
        success_total = 0
        for tenant in tenants:
            tenant_id = tenant.get('id')
            tenant_name = tenant.get('name', 'unknown_tenant').replace(' ', '_')
            export_dir = os.path.join(base_export_dir, tenant_name)
            
            print(Fore.CYAN + f"\nЭкспорт правил для тенанта: {tenant_name}")
            
            # Переключаемся на тенанта
            self.tenant_id = tenant_id
            if not self.update_jwt_with_tenant():
                print(Fore.RED + f"Не удалось переключиться на тенанта {tenant_name}")
                continue
            
            # Экспортируем правила
            success_count = self._export_tenant_rules(export_dir)
            success_total += success_count
        
        print(Fore.CYAN + f"\nИтоговый результат:")
        print(Fore.GREEN + f"Успешно экспортировано правил: {success_total}")
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
            print(Fore.RED + f"Не удалось переключиться на тенанта {tenant_name}")
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
            print(Fore.RED + f"Не удалось переключиться на тенанта {tenant_name}")
            return False
        
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print(Fore.RED + "Не удалось получить ID шаблона политики")
            return False
        
        print(Fore.CYAN + f"\nИспользуется шаблон политики с ID: {template_id}")
        
        # Получаем список всех правил
        rules = self.get_existing_rules(template_id)
        if rules is None:
            return False
        
        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]
        
        if not user_rules:
            print(Fore.YELLOW + "Нет пользовательских правил для экспорта")
            return False
        
        # Выводим список правил для выбора
        print(Fore.CYAN + "\nДоступные правила для экспорта:")
        for i, rule in enumerate(user_rules, 1):
            print(f"{i}. {rule.get('name', 'Без названия')} (ID: {rule.get('id', 'Без ID')})")
        
        while True:
            try:
                rule_nums = input(
                    f"{Fore.CYAN}\nВыберите номера правил для экспорта (через запятую): "
                )
                selected_indices = [int(num.strip()) - 1 for num in rule_nums.split(',') if num.strip().isdigit()]
                valid_indices = [i for i in selected_indices if 0 <= i < len(user_rules)]
                
                if not valid_indices:
                    print(Fore.YELLOW + "Некорректные номера правил")
                    continue
                
                # Создаем директорию для экспорта
                os.makedirs(export_dir, exist_ok=True)
                
                # Экспортируем выбранные правила
                success_count = 0
                for i in valid_indices:
                    rule = user_rules[i]
                    if self.export_single_rule(template_id, rule, export_dir):
                        success_count += 1
                
                print(Fore.CYAN + f"\nЭкспортировано {success_count} из {len(valid_indices)} выбранных правил")
                return success_count > 0
                
            except ValueError:
                print(Fore.YELLOW + "Пожалуйста, введите номера через запятую (например: 1,2,3)")

    def _export_tenant_rules(self, export_dir):
        """Экспортирует все правила текущего тенанта в указанную директорию"""
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print(Fore.RED + "Не удалось получить ID шаблона политики")
            return False
        
        print(Fore.CYAN + f"\nИспользуется шаблон политики с ID: {template_id}")
        
        # Получаем список всех правил
        rules = self.get_existing_rules(template_id)
        if rules is None:
            return False
        
        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]
        
        if not user_rules:
            print(Fore.YELLOW + "Нет пользовательских правил для экспорта")
            return False
        
        # Создаем директорию для экспорта
        os.makedirs(export_dir, exist_ok=True)
        
        # Экспортируем все правила
        success_count = 0
        for rule in user_rules:
            if self.export_single_rule(template_id, rule, export_dir):
                success_count += 1
        
        print(Fore.CYAN + f"\nЭкспортировано {success_count} из {len(user_rules)} правил")
        return success_count > 0

    def _select_tenant(self, tenants):
        """Выбирает тенанта из списка и возвращает его"""
        print(Fore.CYAN + "\nДоступные тенанты:")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            is_default = tenant.get("is_default", False)
            
            default_marker = Fore.GREEN + " (по умолчанию)" if is_default else ""
            print(f"{Fore.CYAN}{i}. {name}{default_marker}")
            print(f"   ID: {tenant_id}\n")
        
        while True:
            try:
                choice = input(f"{Fore.CYAN}\nВыберите номер тенанта (или 'q' для выхода): ")
                if choice.lower() == 'q':
                    return None
                
                choice = int(choice) - 1
                if 0 <= choice < len(tenants):
                    return tenants[choice]
                else:
                    print(Fore.YELLOW + "Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print(Fore.YELLOW + "Пожалуйста, введите число или 'q' для выхода.")

    def delete_all_user_rules(self):
        """Удаляет все пользовательские правила из шаблона"""
        if not self.access_token:
            if not self.get_jwt_tokens():
                return False

        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print(Fore.RED + "Не удалось получить ID шаблона политики")
            return False

        print(Fore.CYAN + f"\nИспользуется шаблон политики с ID: {template_id}")

        # Получаем список всех правил
        rules = self.get_existing_rules(template_id)
        if rules is None:
            return False

        # Фильтруем только пользовательские правила
        user_rules = [rule for rule in rules if not rule.get('is_system', True)]

        if not user_rules:
            print(Fore.YELLOW + "Нет пользовательских правил для удаления")
            return False

        # Подтверждение от пользователя
        print(Fore.RED + "\nВНИМАНИЕ: Будут удалены следующие правила:")
        for rule in user_rules:
            print(f"- {rule.get('name', 'Без названия')} (ID: {rule.get('id', 'Без ID')})")

        confirm = input(f"\n{Fore.RED}Вы уверены, что хотите удалить {len(user_rules)} правил? (y/n): ").lower()
        if confirm != 'y':
            print(Fore.YELLOW + "Удаление отменено")
            return False

        # Удаляем правила
        deleted_count = 0
        for rule in user_rules:
            rule_id = rule.get('id')
            rule_name = rule.get('name', 'Без названия')
            
            if not rule_id:
                print(Fore.YELLOW + f"Правило '{rule_name}' не имеет ID, пропускаем")
                continue

            url = urljoin(self.base_url, f"{self.api_path}/config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}")
            response = self._make_request("DELETE", url)

            if response and response.status_code == 204:
                print(Fore.GREEN + f"Правило '{rule_name}' успешно удалено")
                deleted_count += 1
            else:
                error_msg = response.text if response else "Не удалось выполнить запрос"
                print(Fore.RED + f"Ошибка при удалении правила '{rule_name}': {error_msg}")

        print(Fore.CYAN + f"\nУдалено {deleted_count} из {len(user_rules)} правил")
        return deleted_count > 0


    def import_single_rule(self, template_id, file_path, selected_action_ids=None, enable_after_import=False):
        """Импортирует одно правило из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
            
            rule_name = rule_data.get('name', os.path.basename(file_path))
            print(f"\n{Fore.CYAN}Обработка файла: {file_path}")
            print(f"{Fore.CYAN}Правило: {rule_name}{Style.RESET_ALL}")
            
            if selected_action_ids is not None:
                if 'configuration' not in rule_data:
                    rule_data['configuration'] = {}
                rule_data['configuration']['actions'] = selected_action_ids
                print(Fore.GREEN + "Применены выбранные действия к правилу")
            
            # Получаем список существующих правил
            existing_rules = self.get_existing_rules(template_id)
            if existing_rules is None:
                error_msg = "Не удалось получить список существующих правил"
                print(Fore.RED + error_msg)
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
                    print(Fore.RED + error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    return False
                    
                if response.status_code == 200:
                    print(Fore.GREEN + f"Правило '{rule_name}' успешно обновлено")
                    self.success_files.append(file_path)
                    
                    if enable_after_import:
                        print(Fore.CYAN + f"Включаем правило '{rule_name}'...")
                        enable_response = self.enable_rule(template_id, rule_id, True)
                        if enable_response is None or enable_response.status_code != 200:
                            error_msg = "Не удалось включить правило"
                            print(Fore.YELLOW + error_msg)
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
                    print(Fore.RED + f"{error_msg}: {rule_name}")
                    print(Fore.YELLOW + f"Ответ сервера: {response.text}")
                    
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
                    print(Fore.RED + error_msg)
                    self.failed_files.append({
                        'file': file_path,
                        'rule': rule_name,
                        'error': error_msg,
                        'code': None,
                        'response': None
                    })
                    return False
                    
                if response.status_code == 201:
                    print(Fore.GREEN + f"Правило '{rule_name}' успешно создано")
                    self.success_files.append(file_path)
                    
                    try:
                        new_rule = response.json()
                        rule_id = new_rule.get('id')
                        
                        if enable_after_import and rule_id:
                            print(Fore.CYAN + f"Включаем правило '{rule_name}'...")
                            enable_response = self.enable_rule(template_id, rule_id, True)
                            if enable_response is None or enable_response.status_code != 200:
                                error_msg = "Не удалось включить правило"
                                print(Fore.YELLOW + error_msg)
                                self.failed_files.append({
                                    'file': file_path,
                                    'rule': rule_name,
                                    'error': error_msg,
                                    'code': getattr(enable_response, 'status_code', None),
                                    'response': getattr(enable_response, 'text', None)
                                })
                    except json.JSONDecodeError:
                        error_msg = "Не удалось получить ID созданного правила"
                        print(Fore.YELLOW + error_msg)
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
                    print(Fore.RED + f"{error_msg}: {rule_name}")
                    print(Fore.YELLOW + f"Ответ сервера: {response.text}")
                    
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
            print(Fore.RED + f"Ошибка при чтении файла {file_path}: {error_msg}")
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
            print(Fore.RED + f"Неожиданная ошибка при обработке файла {file_path}: {error_msg}")
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
            print(Fore.RED + f"Директория не найдена: {directory_path}")
            return False
        
        # Получаем ID шаблона политики
        template_id = self.get_policy_template_id()
        if not template_id:
            print(Fore.RED + "Не удалось получить ID шаблона политики")
            return False
        
        print(Fore.CYAN + f"\nИспользуется шаблон политики с ID: {template_id}")
        
        # Получаем список доступных действий
        actions = self.get_available_actions()
        if not actions:
            print(Fore.RED + "Не удалось получить список доступных действий")
            return False
        
        # Выводим список доступных действий
        print(Fore.CYAN + "\nДоступные действия:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action.get('name')} (ID: {action.get('id')})")
        
        # Запрашиваем выбор действий для всех правил
        selected_action_ids = []
        while True:
            choice = input(
                f"{Fore.CYAN}\nВыберите номера действий для применения ко ВСЕМ правилам (через запятую, или Enter чтобы пропустить): "
            )
            
            if not choice.strip():  # Если просто нажали Enter
                print(Fore.YELLOW + "Действия не будут изменены")
                selected_action_ids = None
                break
            
            try:
                selected_indices = [int(num.strip()) - 1 for num in choice.split(',') if num.strip().isdigit()]
                valid_indices = [i for i in selected_indices if 0 <= i < len(actions)]
                
                if not valid_indices:
                    print(Fore.YELLOW + "Некорректные номера действий")
                    continue
                
                # Формируем список ID выбранных действий
                selected_action_ids = [actions[i]['id'] for i in valid_indices]
                break
                
            except ValueError:
                print(Fore.YELLOW + "Пожалуйста, введите номера через запятую (например: 1,2,3)")
        
        # Спрашиваем, нужно ли включать правила после импорта
        enable_rules = False
        enable_choice = input(f"{Fore.CYAN}\nВключить импортированные правила? (y/n): ").lower()
        if enable_choice == 'y':
            enable_rules = True
            print(Fore.GREEN + "Импортированные правила будут включены")
        else:
            print(Fore.YELLOW + "Импортированные правила останутся выключенными")
        
        # Получаем список JSON файлов в директории
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.ptafpro')]
        
        if not json_files:
            print(Fore.YELLOW + "В указанной директории нет .ptafpro файлов")
            return False
        
        # Выводим список файлов для выбора
        print(Fore.CYAN + "\nДоступные файлы для импорта:")
        for i, filename in enumerate(json_files, 1):
            print(f"{i}. {filename}")
        
        while True:
            choice = input(
                f"{Fore.CYAN}\nВыберите:\n"
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
                
                print(f"\n{Fore.CYAN}Итог:")
                print(f"{Fore.GREEN}Успешно обработано: {success_count}")
                print(f"{Fore.RED}Не удалось обработать: {fail_count}")
                print(f"{Fore.CYAN}Всего файлов: {total_count}{Style.RESET_ALL}")
                
                self.print_failed_files()
                return success_count > 0
            
            elif choice == '2':
                # Выбор конкретных файлов
                try:
                    file_nums = input(f"{Fore.CYAN}Введите номера файлов для импорта (через запятую): ")
                    selected_indices = [int(num.strip()) - 1 for num in file_nums.split(',') if num.strip().isdigit()]
                    
                    valid_indices = [i for i in selected_indices if 0 <= i < len(json_files)]
                    
                    if not valid_indices:
                        print(Fore.YELLOW + "Некорректные номера файлов")
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
                    
                    print(f"\n{Fore.CYAN}Итог:")
                    print(f"{Fore.GREEN}Успешно обработано: {success_count}")
                    print(f"{Fore.RED}Не удалось обработать: {fail_count}")
                    print(f"{Fore.CYAN}Всего выбрано файлов: {total_count}{Style.RESET_ALL}")
                    
                    self.print_failed_files()
                    return success_count > 0
                
                except ValueError:
                    print(Fore.YELLOW + "Пожалуйста, введите номера через запятую (например: 1,2,3)")
            
            elif choice == '3':
                return False
            
            else:
                print(Fore.YELLOW + "Некорректный выбор. Попробуйте снова.")

    def print_failed_files(self):
        """Выводит список проблемных файлов с причинами ошибок"""
        if not self.failed_files:
            print(Fore.GREEN + "\nНет проблемных файлов!")
            return
        
        print(Fore.RED + "\nСписок проблемных файлов:")
        for i, fail in enumerate(self.failed_files, 1):
            print(f"{Fore.RED}{i}. {fail['file']}")
            print(f"{Fore.YELLOW}   Правило: {fail['rule']}")
            print(f"{Fore.YELLOW}   Причина: {fail['error']}")
            if fail.get('code') is not None:
                print(f"{Fore.YELLOW}   Код ошибки: {fail['code']}")
            if fail.get('response') is not None:
                print(f"{Fore.YELLOW}   Ответ сервера: {fail['response']}")
            print()


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

    if not args.source and not args.export and not args.delete_all:
        parser.error("Необходимо указать один из параметров: --source, --export или --delete-all")

    try:
        client = PTAFClient(config_file=args.config, debug=args.debug)
        # Сначала получаем токены
        if not client.get_jwt_tokens():
            print(Fore.RED + "Не удалось получить JWT токены")
            return

        if args.export:
            # Экспортируем правила
            client.export_rules()
        elif args.source:
            # Импортируем правила (требуется выбор тенанта)
            if not client.select_tenant():
                print(Fore.RED + "Не удалось выбрать тенант")
                return
            client.import_rules(directory_path=args.source)
        elif args.delete_all:
            # Удаляем правила (требуется выбор тенанта)
            if not client.select_tenant():
                print(Fore.RED + "Не удалось выбрать тенант")
                return
            client.delete_all_user_rules()
    except Exception as e:
        print(Fore.RED + f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()