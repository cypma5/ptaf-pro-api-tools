# traffic_settings.py
import os
import json
import datetime
from urllib.parse import urljoin

class TrafficSettingsManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_traffic_settings(self):
        """Получает текущие настройки трафика"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        if not self.auth_manager.tenant_id:
            print("Не выбран тенант")
            return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/traffic_settings")
        
        response = self.make_request("GET", url)
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
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return False
        
        if not self.auth_manager.tenant_id:
            print("Не выбран тенант")
            return False
        
        # Создаем бекап перед изменением
        if not self._create_backup():
            print("Предупреждение: не удалось создать бекап перед изменением")
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/traffic_settings")
        
        response = self.make_request("PATCH", url, json=settings_data)
        if not response:
            return False
            
        if response.status_code == 200:
            print("Параметры traffic_settings успешно обновлены")
            return True
        else:
            print(f"Ошибка при обновлении параметров traffic_settings. Код: {response.status_code}, Ответ: {response.text}")
            return False

    def _create_backup(self):
        """Создает бекап текущих настроек"""
        current_settings = self.get_traffic_settings()
        if not current_settings:
            return False
        
        # Создаем директорию для бекапов
        backup_dir = os.path.join("traffic_settings", self.auth_manager.tenant_id)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-traffic_settings.json"
        filepath = os.path.join(backup_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
            print(f"Бекап настроек сохранен в файл: {filepath}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении бекапа: {e}")
            return False

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

    def manage_traffic_settings(self):
        """Управление настройками traffic_settings"""
        current_settings = self.get_traffic_settings() or {}
        
        while True:
            print("\nУправление настройками traffic_settings:")
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