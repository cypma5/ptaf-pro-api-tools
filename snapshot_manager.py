# snapshot_manager.py
import os
import json
import datetime
from urllib.parse import urljoin

class SnapshotManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    def get_tenant_snapshot(self, tenant_id=None):
        """Получает конфигурацию тенанта"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        # Если указан tenant_id, обновляем токен для этого тенанта
        if tenant_id and tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/snapshot")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            snapshot = response.json()
            print("Успешно получена конфигурация тенанта")
            return snapshot
        else:
            print(f"Ошибка при получении конфигурации. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def get_tenant_backends(self, tenant_id=None):
        """Получает список бекендов тенанта"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        # Если указан tenant_id, обновляем токен для этого тенанта
        if tenant_id and tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/backends")
        
        response = self.make_request("GET", url)
        if not response:
            return None
            
        if response.status_code == 200:
            backends = response.json()
            print("Успешно получены бекенды тенанта")
            return backends
        else:
            print(f"Ошибка при получении бекендов. Код: {response.status_code}, Ответ: {response.text}")
            return None

    def save_snapshot_to_file(self, snapshot, tenant_id, base_dir="snapshot"):
        """Сохраняет конфигурацию в файл"""
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-snapshot.json"
        filepath = os.path.join(tenant_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            print(f"Конфигурация сохранена в файл: {filepath}")
            return filepath
        except Exception as e:
            print(f"Ошибка при сохранении конфигурации: {e}")
            return None

    def save_backends_to_file(self, backends, tenant_id, base_dir="snapshot"):
        """Сохраняет бекенды в файл"""
        # Создаем директорию для тенанта
        tenant_dir = os.path.join(base_dir, tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        # Формируем имя файла с датой и временем
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{current_time}-backends.json"
        filepath = os.path.join(tenant_dir, filename)
        
        try:
            # Удаляем ключ traffic_profiles из каждого бекенда
            cleaned_backends = self._clean_backends_data(backends)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_backends, f, ensure_ascii=False, indent=2)
            print(f"Бекенды сохранены в файл: {filepath}")
            return filepath
        except Exception as e:
            print(f"Ошибка при сохранении бекендов: {e}")
            return None

    def _clean_backends_data(self, backends_data):
        """Очищает данные бекендов - удаляет traffic_profiles и id"""
        if isinstance(backends_data, dict) and 'items' in backends_data:
            items = backends_data['items']
            cleaned_items = []
            for backend in items:
                cleaned_backend = backend.copy()
                # Удаляем ненужные поля
                cleaned_backend.pop('id', None)
                cleaned_backend.pop('traffic_profiles', None)
                cleaned_items.append(cleaned_backend)
            return {'items': cleaned_items}
        elif isinstance(backends_data, list):
            cleaned_items = []
            for backend in backends_data:
                cleaned_backend = backend.copy()
                # Удаляем ненужные поля
                cleaned_backend.pop('id', None)
                cleaned_backend.pop('traffic_profiles', None)
                cleaned_items.append(cleaned_backend)
            return cleaned_items
        else:
            return backends_data

    def get_available_tenants(self):
        """Получает список доступных тенантов"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return None
        
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/auth/account/tenants")
        
        response = self.make_request("GET", url)
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

    def get_single_tenant_snapshot(self):
        """Получает конфигурацию выбранного тенанта"""
        if not self.auth_manager.tenant_id:
            print("Сначала выберите тенант")
            return False
        
        print(f"\nПолучение конфигурации тенанта {self.auth_manager.tenant_id}...")
        
        # Получаем конфигурацию
        snapshot = self.get_tenant_snapshot()
        if not snapshot:
            print("Не удалось получить конфигурацию")
            return False
        
        # Получаем бекенды
        backends = self.get_tenant_backends()
        if not backends:
            print("Не удалось получить бекенды")
            return False
        
        # Сохраняем в файлы
        snapshot_filepath = self.save_snapshot_to_file(snapshot, self.auth_manager.tenant_id)
        backends_filepath = self.save_backends_to_file(backends, self.auth_manager.tenant_id)
        
        if snapshot_filepath and backends_filepath:
            print("Конфигурация и бекенды успешно сохранены")
            return True
        else:
            print("Не удалось сохранить конфигурацию или бекенды")
            return False

    def get_all_tenants_snapshots(self):
        """Получает конфигурации со всех доступных тенантов"""
        print("\nПолучение конфигураций со всех доступных тенантов...")
        
        # Сохраняем текущий тенант
        original_tenant_id = self.auth_manager.tenant_id
        
        # Получаем список всех тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        success_count = 0
        total_tenants = len(tenants)
        
        for tenant in tenants:
            tenant_id = tenant.get('id')
            tenant_name = tenant.get('name', 'Без названия')
            
            print(f"\nОбработка тенанта: {tenant_name} (ID: {tenant_id})")
            
            # Получаем конфигурацию тенанта
            snapshot = self.get_tenant_snapshot(tenant_id)
            if snapshot:
                # Получаем бекенды тенанта
                backends = self.get_tenant_backends(tenant_id)
                
                # Сохраняем в файлы
                snapshot_filepath = self.save_snapshot_to_file(snapshot, tenant_id)
                if backends:
                    backends_filepath = self.save_backends_to_file(backends, tenant_id)
                    if snapshot_filepath and backends_filepath:
                        success_count += 1
                        print(f"Конфигурация и бекенды тенанта {tenant_name} успешно сохранены")
                    else:
                        print(f"Не удалось сохранить конфигурацию или бекенды тенанта {tenant_name}")
                else:
                    if snapshot_filepath:
                        success_count += 1
                        print(f"Конфигурация тенанта {tenant_name} успешно сохранена (бекенды не получены)")
                    else:
                        print(f"Не удалось сохранить конфигурацию тенанта {tenant_name}")
            else:
                print(f"Не удалось получить конфигурацию тенанта {tenant_name}")
        
        # Восстанавливаем оригинальный тенант
        if original_tenant_id:
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
        
        print(f"\nИтог: успешно обработано {success_count} из {total_tenants} тенантов")
        return success_count > 0

    def check_backend_exists(self, backend_data, tenant_id=None):
        """Проверяет, существует ли бекенд с такими же address и port"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return False
        
        # Если указан tenant_id, обновляем токен для этого тенанта
        if tenant_id and tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return False
        
        # Получаем все существующие бекенды
        existing_backends = self.get_tenant_backends()
        if not existing_backends:
            return False
        
        # Извлекаем список бекендов
        if isinstance(existing_backends, dict) and 'items' in existing_backends:
            backends_list = existing_backends['items']
        elif isinstance(existing_backends, list):
            backends_list = existing_backends
        else:
            return False
        
        # Проверяем совпадение по address и port
        target_address = backend_data.get('address')
        target_port = backend_data.get('port')
        target_protocol = backend_data.get('protocol')
        
        for backend in backends_list:
            if (backend.get('address') == target_address and 
                backend.get('port') == target_port and 
                backend.get('protocol') == target_protocol):
                return True
        
        return False

    def restore_backends(self, target_tenant_id=None):
        """Восстанавливает бекенды из сохраненного файла"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return False
        
        # Если указан target_tenant_id, восстанавливаем в другой тенант
        if target_tenant_id and target_tenant_id != self.auth_manager.tenant_id:
            original_tenant_id = self.auth_manager.tenant_id
            self.auth_manager.tenant_id = target_tenant_id
            if not self.auth_manager.update_jwt_with_tenant(self.make_request):
                print(f"Не удалось переключиться на тенант {target_tenant_id}")
                self.auth_manager.tenant_id = original_tenant_id
                return False
            print(f"Восстановление в тенант: {target_tenant_id}")
        
        # Поиск файла с бекендами
        backends_file = self._find_latest_backends_file()
        if not backends_file:
            print("Не найден файл с бекендами для восстановления")
            return False
        
        print(f"Найден файл с бекендами: {backends_file}")
        
        try:
            with open(backends_file, 'r', encoding='utf-8') as f:
                backends_data = json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла бекендов: {e}")
            return False
        
        # Извлекаем список бекендов
        if isinstance(backends_data, dict) and 'items' in backends_data:
            backends = backends_data['items']
        elif isinstance(backends_data, list):
            backends = backends_data
        else:
            print("Неподдерживаемый формат файла бекендов")
            return False
        
        if not backends:
            print("Файл бекендов пуст")
            return False
        
        print(f"Найдено {len(backends)} бекендов для восстановления")
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите восстановить {len(backends)} бекендов? (y/n): ").lower()
        if confirm != 'y':
            print("Восстановление отменено")
            return False
        
        # Восстанавливаем каждый бекенд
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_backends = len(backends)
        
        for backend in backends:
            backend_data = backend.copy()
            
            # Проверяем, не существует ли уже такой бекенд
            if self.check_backend_exists(backend_data):
                print(f"Бекенд уже существует, пропускаем: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                skipped_count += 1
                continue
            
            # Создаем бекенд
            response = self._create_backend(backend_data)
            if response and response.status_code == 201:
                print(f"Успешно создан бекенд: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                success_count += 1
            elif response and response.status_code == 422:
                print(f"Ошибка 422 при создании бекенда {backend_data.get('address')}: конфликт уникальности")
                error_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при создании бекенда {backend_data.get('address')}: {error_msg}")
                error_count += 1
        
        print(f"\nИтог восстановления:")
        print(f"Успешно создано: {success_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")
        print(f"Ошибок: {error_count}")
        print(f"Всего бекендов: {total_backends}")
        
        return success_count > 0

    def restore_security_config(self):
        """Восстанавливает конфигурацию безопасности из снапшота"""
        if not self.auth_manager.access_token:
            if not self.auth_manager.get_jwt_tokens(self.make_request):
                return False
        
        # Поиск доступных снапшотов
        snapshot_files = self._find_available_snapshots()
        if not snapshot_files:
            print("Не найдены файлы снапшотов для восстановления")
            return False
        
        print("\nДоступные снапшоты:")
        for i, (filepath, timestamp) in enumerate(snapshot_files, 1):
            print(f"{i}. {timestamp} - {os.path.basename(filepath)}")
        
        snapshot_index = self._select_index(snapshot_files, "Выберите номер снапшота для восстановления: ")
        if snapshot_index is None:
            return False
        
        selected_file = snapshot_files[snapshot_index][0]
        print(f"Выбран файл: {selected_file}")
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла снапшота: {e}")
            return False
        
        if not snapshot_data:
            print("Файл снапшота пуст")
            return False
        
        # Подтверждение
        print("\nВНИМАНИЕ: Восстановление конфигурации безопасности перезапишет текущую конфигурацию!")
        confirm = input("Вы уверены, что хотите восстановить конфигурацию безопасности? (y/n): ").lower()
        if confirm != 'y':
            print("Восстановление отменено")
            return False
        
        # Восстанавливаем конфигурацию
        response = self._restore_snapshot(snapshot_data)
        if response and response.status_code == 201:
            print("Конфигурация безопасности успешно восстановлена")
            return True
        else:
            error_msg = response.text if response else "Неизвестная ошибка"
            print(f"Ошибка при восстановлении конфигурации: {error_msg}")
            return False

    def _find_available_snapshots(self):
        """Находит все доступные файлы снапшотов для текущего тенанта"""
        if not self.auth_manager.tenant_id:
            return []
        
        tenant_dir = os.path.join("snapshot", self.auth_manager.tenant_id)
        if not os.path.exists(tenant_dir):
            return []
        
        # Ищем все файлы снапшотов
        snapshot_files = []
        for filename in os.listdir(tenant_dir):
            if filename.endswith('-snapshot.json'):
                filepath = os.path.join(tenant_dir, filename)
                # Извлекаем timestamp из имени файла
                timestamp = filename.split('-snapshot.json')[0]
                snapshot_files.append((filepath, timestamp))
        
        # Сортируем по времени (последний первый)
        snapshot_files.sort(key=lambda x: x[1], reverse=True)
        return snapshot_files

    def _restore_snapshot(self, snapshot_data):
        """Восстанавливает конфигурацию из снапшота"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/snapshot")
        
        response = self.make_request("POST", url, json=snapshot_data)
        return response

    def copy_backends_to_another_tenant(self):
        """Копирует бекенды из одного тенанта в другой"""
        print("\nКопирование бекендов между тенантами")
        
        # Получаем список доступных тенантов
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return False
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        source_index = self._select_index(tenants, "Выберите номер исходного тенанта: ")
        if source_index is None:
            return False
        
        source_tenant = tenants[source_index]
        source_tenant_id = source_tenant['id']
        source_tenant_name = source_tenant.get('name', 'Без названия')
        
        # Выбор целевого тенанта
        print(f"\nВыберите целевой тенант (куда копировать):")
        for i, tenant in enumerate(tenants, 1):
            print(f"{i}. {tenant.get('name', 'Без названия')} (ID: {tenant.get('id')})")
        
        target_index = self._select_index(tenants, "Выберите номер целевого тенанта: ")
        if target_index is None:
            return False
        
        target_tenant = tenants[target_index]
        target_tenant_id = target_tenant['id']
        target_tenant_name = target_tenant.get('name', 'Без названия')
        
        if source_tenant_id == target_tenant_id:
            print("Исходный и целевой тенанты совпадают")
            return False
        
        print(f"\nКопирование бекендов из '{source_tenant_name}' в '{target_tenant_name}'")
        
        # Получаем бекенды из исходного тенанта
        original_tenant_id = self.auth_manager.tenant_id
        
        # Переключаемся на исходный тенант
        self.auth_manager.tenant_id = source_tenant_id
        if not self.auth_manager.update_jwt_with_tenant(self.make_request):
            print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
            self.auth_manager.tenant_id = original_tenant_id
            return False
        
        backends = self.get_tenant_backends()
        if not backends:
            print("Не удалось получить бекенды из исходного тенанта")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Очищаем данные бекендов
        cleaned_backends = self._clean_backends_data(backends)
        if isinstance(cleaned_backends, dict) and 'items' in cleaned_backends:
            backends_list = cleaned_backends['items']
        elif isinstance(cleaned_backends, list):
            backends_list = cleaned_backends
        else:
            print("Неподдерживаемый формат бекендов")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        if not backends_list:
            print("В исходном тенанте нет бекендов для копирования")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        print(f"Найдено {len(backends_list)} бекендов для копирования")
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите скопировать {len(backends_list)} бекендов из '{source_tenant_name}' в '{target_tenant_name}'? (y/n): ").lower()
        if confirm != 'y':
            print("Копирование отменено")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Переключаемся на целевой тенант
        self.auth_manager.tenant_id = target_tenant_id
        if not self.auth_manager.update_jwt_with_tenant(self.make_request):
            print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
            self.auth_manager.tenant_id = original_tenant_id
            self.auth_manager.update_jwt_with_tenant(self.make_request)
            return False
        
        # Копируем каждый бекенд
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_backends = len(backends_list)
        
        for backend in backends_list:
            backend_data = backend.copy()
            
            # Проверяем, не существует ли уже такой бекенд в целевом тенанте
            if self.check_backend_exists(backend_data):
                print(f"Бекенд уже существует в целевом тенанте, пропускаем: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                skipped_count += 1
                continue
            
            # Создаем бекенд в целевом тенанте
            response = self._create_backend(backend_data)
            if response and response.status_code == 201:
                print(f"Успешно скопирован бекенд: {backend_data.get('address')}:{backend_data.get('port')} ({backend_data.get('protocol')})")
                success_count += 1
            elif response and response.status_code == 422:
                print(f"Ошибка 422 при копировании бекенда {backend_data.get('address')}: конфликт уникальности")
                error_count += 1
            else:
                error_msg = response.text if response else "Неизвестная ошибка"
                print(f"Ошибка при копировании бекенда {backend_data.get('address')}: {error_msg}")
                error_count += 1
        
        # Восстанавливаем оригинальный тенант
        self.auth_manager.tenant_id = original_tenant_id
        self.auth_manager.update_jwt_with_tenant(self.make_request)
        
        print(f"\nИтог копирования:")
        print(f"Успешно скопировано: {success_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")
        print(f"Ошибок: {error_count}")
        print(f"Всего бекендов: {total_backends}")
        
        return success_count > 0

    def manage_tenant_transfer(self):
        """Управление переносом объектов между тенантами"""
        while True:
            print("\nПеренос объектов между тенантами:")
            print("1. Перенос защищаемых серверов в другой тенант")
            print("2. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-2): ")
            
            if choice == '1':
                self.copy_backends_to_another_tenant()
            elif choice == '2':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def _find_latest_backends_file(self):
        """Находит последний файл с бекендами для текущего тенанта"""
        if not self.auth_manager.tenant_id:
            return None
        
        tenant_dir = os.path.join("snapshot", self.auth_manager.tenant_id)
        if not os.path.exists(tenant_dir):
            return None
        
        # Ищем все файлы бекендов
        backends_files = []
        for filename in os.listdir(tenant_dir):
            if filename.endswith('-backends.json'):
                filepath = os.path.join(tenant_dir, filename)
                backends_files.append((filepath, os.path.getmtime(filepath)))
        
        if not backends_files:
            return None
        
        # Сортируем по времени изменения (последний первый)
        backends_files.sort(key=lambda x: x[1], reverse=True)
        return backends_files[0][0]

    def _create_backend(self, backend_data):
        """Создает новый бекенд"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/backends")
        
        response = self.make_request("POST", url, json=backend_data)
        return response

    def _select_index(self, items, prompt):
        """Выбор индекса из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return index
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")

    def manage_snapshots(self):
        """Управление получением конфигураций"""
        while True:
            print("\nПолучение конфигураций тенантов:")
            print("1. Получить конфигурацию текущего тенанта")
            print("2. Получить конфигурации со всех тенантов")
            print("3. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-3): ")
            
            if choice == '1':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                self.get_single_tenant_snapshot()
            
            elif choice == '2':
                self.get_all_tenants_snapshots()
            
            elif choice == '3':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def manage_restore(self):
        """Управление восстановлением конфигураций"""
        while True:
            print("\nВосстановление конфигураций тенантов:")
            print("1. Восстановить 'защищаемые сервера' (бекенды) в текущий тенант")
            print("2. Восстановить 'Конфигурацию безопасности' (с выбором версии снапшота)")
            print("3. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-3): ")
            
            if choice == '1':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                self.restore_backends()
            
            elif choice == '2':
                if not self.auth_manager.tenant_id:
                    print("Сначала выберите тенант")
                    continue
                self.restore_security_config()
            
            elif choice == '3':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")

    def get_snapshots_from_cli(self):
        """Получает конфигурации со всех тенантов (для вызова из CLI)"""
        return self.get_all_tenants_snapshots()