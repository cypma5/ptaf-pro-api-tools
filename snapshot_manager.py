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
        
        snapshot = self.get_tenant_snapshot()
        if not snapshot:
            print("Не удалось получить конфигурацию")
            return False
        
        # Сохраняем в файл
        filepath = self.save_snapshot_to_file(snapshot, self.auth_manager.tenant_id)
        if filepath:
            print("Конфигурация успешно сохранена")
            return True
        else:
            print("Не удалось сохранить конфигурацию")
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
                # Сохраняем в файл
                filepath = self.save_snapshot_to_file(snapshot, tenant_id)
                if filepath:
                    success_count += 1
                    print(f"Конфигурация тенанта {tenant_name} успешно сохранена")
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

    def get_snapshots_from_cli(self):
        """Получает конфигурации со всех тенантов (для вызова из CLI)"""
        return self.get_all_tenants_snapshots()