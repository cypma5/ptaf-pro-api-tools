# tenants.py (объединенный)
import json
from urllib.parse import urljoin
import requests

class TenantManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

    # ==================== ПОЛУЧЕНИЕ ТЕНАНТОВ ====================

    def get_available_tenants(self):
        """Получает список доступных тенантов для текущего пользователя"""
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

    def select_tenant_interactive(self):
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
                    self.auth_manager.tenant_id = selected_tenant.get("id")
                    if self.auth_manager.tenant_id:
                        return self.auth_manager.update_jwt_with_tenant(self.make_request)
                    print("У выбранного тенанта отсутствует ID")
                else:
                    print("Некорректный выбор. Попробуйте снова.")
            except ValueError:
                print("Пожалуйста, введите число или 'q' для выхода.")
        return False

    def select_single_tenant(self, prompt="Выберите тенант:"):
        """Выбирает один тенант и возвращает его данные"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return None
        
        print(f"\n{prompt}")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(tenants):
                    return tenants[index]
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        return None

    def select_source_and_target_tenants(self):
        """Выбирает исходный и целевой тенанты для копирования"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return None, None
        
        # Выбор исходного тенанта
        print("\nВыберите исходный тенант (откуда копировать):")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер исходного тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None, None
                
                source_index = int(choice) - 1
                if 0 <= source_index < len(tenants):
                    source_tenant = tenants[source_index]
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        # Выбор целевого тенанта
        print("\nВыберите целевой тенант (куда копировать):")
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")
            tenant_id = tenant.get("id", "Без ID")
            print(f"{i}. {name} (ID: {tenant_id})")
        
        while True:
            try:
                choice = input("\nВыберите номер целевого тенанта (или 'q' для отмены): ")
                if choice.lower() == 'q':
                    return None, None
                
                target_index = int(choice) - 1
                if 0 <= target_index < len(tenants):
                    target_tenant = tenants[target_index]
                    break
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
        
        return source_tenant, target_tenant

    # ==================== СОЗДАНИЕ ТЕНАНТОВ ====================

    def create_tenant(self):
        """Создает новый тенант"""
        print("\n=== СОЗДАНИЕ НОВОГО ТЕНАНТА ===\n")
        
        # Получаем данные для нового тенанта
        name = input("Введите имя тенанта: ").strip()
        if not name:
            print("Имя тенанта не может быть пустым")
            return False
        
        username = input("Введите имя администратора: ").strip()
        if not username:
            print("Имя администратора не может быть пустым")
            return False
        
        # Создаем email на основе имени администратора
        email = f"{username}@test.ru"
        print(f"Email администратора будет: {email}")
        
        # Запрашиваем пароль
        password = input("Введите пароль для администратора: ").strip()
        if not password:
            print("Пароль не может быть пустым")
            return False
        
        # Подтверждение пароля
        password_confirm = input("Подтвердите пароль: ").strip()
        if password != password_confirm:
            print("Пароли не совпадают")
            return False
        
        # Формируем данные для создания тенанта
        tenant_data = {
            "name": name,
            "is_active": True,
            "traffic_processing": {
                "traffic_processing_type": "ptaf",
                "zone": "default",
                "core_type": "PTAF_NGINX",
                "pod_size": "base",
                "min_pods_per_node": 1,
                "max_pods_per_node": 1,
                "min_pods": 1,
                "max_pods": 1
            },
            "administrator": {
                "username": username,
                "email": email,
                "password": password,
                "is_active": True,
                "password_change_required": False,
                "invite_current_user": True
            }
        }
        
        # Показываем пользователю, что будет отправлено
        print("\nБудут отправлены следующие данные:")
        print(f"Имя тенанта: {name}")
        print(f"Администратор:")
        print(f"  - Имя пользователя: {username}")
        print(f"  - Email: {email}")
        print(f"  - Пароль: {'*' * len(password)}")
        
        # Подтверждение
        confirm = input("\nВы уверены, что хотите создать тенант? (y/n): ").lower()
        if confirm != 'y':
            print("Создание тенанта отменено")
            return False
        
        # Отправляем запрос на создание тенанта
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/auth/tenants")
        
        print(f"\nОтправка запроса на создание тенанта...")
        print(f"URL: {url}")
        
        response = self.make_request("POST", url, json=tenant_data)
        if not response:
            print("Не удалось выполнить запрос на создание тенанта")
            print("Причина: запрос вернул None (возможно, проблема с сетью или авторизацией)")
            return False
        
        # Выводим полную информацию об ответе
        print(f"\n=== ОТВЕТ СЕРВЕРА ===")
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nТело ответа:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print("=" * 40)
        
        if response.status_code == 201:
            tenant_info = response.json()
            print("\n✅ Тенант успешно создан!")
            print(f"ID: {tenant_info.get('id')}")
            print(f"Имя: {tenant_info.get('name')}")
            print(f"Статус: {'Активен' if tenant_info.get('is_active') else 'Неактивен'}")
            
            # Если есть информация об администраторе
            if 'administrator' in tenant_info:
                admin = tenant_info['administrator']
                print(f"\nАдминистратор создан:")
                print(f"  Имя пользователя: {admin.get('username')}")
                print(f"  Email: {admin.get('email')}")
            
            return True
        else:
            print(f"\n❌ Ошибка при создании тенанта!")
            print(f"Код ошибки: {response.status_code}")
            
            # Пытаемся получить детали ошибки из JSON
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    print("Детали ошибки:")
                    print(json.dumps(error_data['errors'], indent=2, ensure_ascii=False))
                elif 'message' in error_data:
                    print(f"Сообщение: {error_data['message']}")
                elif 'error' in error_data:
                    print(f"Ошибка: {error_data['error']}")
                elif 'detail' in error_data:
                    print(f"Детали: {error_data['detail']}")
            except:
                print(f"Ответ сервера (текст): {response.text}")
            
            return False

    # ==================== РАСШИРЕННОЕ УПРАВЛЕНИЕ ====================

    def manage_tenants_extended(self):
        """Расширенное управление тенантами"""
        while True:
            print("\n=== РАБОТА С ТЕНАНТАМИ ===")
            print("1. Создать тенант")
            print("2. Показать список доступных тенантов")
            print("3. Вернуться в главное меню")
            
            choice = input("\nВыберите действие (1-3): ")
            
            if choice == '1':
                self.create_tenant()
            elif choice == '2':
                tenants = self.get_available_tenants()
                if tenants:
                    print("\nДоступные тенанты:")
                    for i, tenant in enumerate(tenants, 1):
                        name = tenant.get("name", "Без названия")
                        tenant_id = tenant.get("id", "Без ID")
                        is_default = tenant.get("is_default", False)
                        description = tenant.get("description", "Без описания")
                        
                        default_marker = " (по умолчанию)" if is_default else ""
                        print(f"{i}. {name}{default_marker}")
                        print(f"   ID: {tenant_id}")
                        print(f"   Описание: {description}")
                else:
                    print("Не удалось получить список тенантов")
            elif choice == '3':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def get_tenant_by_id(self, tenant_id):
        """Получает информацию о тенанте по ID"""
        tenants = self.get_available_tenants()
        if not tenants:
            return None
        
        for tenant in tenants:
            if tenant.get('id') == tenant_id:
                return tenant
        
        return None

    def get_tenant_by_name(self, tenant_name):
        """Получает информацию о тенанте по имени"""
        tenants = self.get_available_tenants()
        if not tenants:
            return None
        
        for tenant in tenants:
            if tenant.get('name') == tenant_name:
                return tenant
        
        return None

    def print_tenants_table(self):
        """Выводит таблицу с информацией о тенантах"""
        tenants = self.get_available_tenants()
        if not tenants:
            print("Не удалось получить список тенантов")
            return
        
        print("\n" + "=" * 80)
        print(f"{'№':<3} {'Имя тенанта':<30} {'ID':<36} {'По умолчанию':<12} {'Описание'}")
        print("=" * 80)
        
        for i, tenant in enumerate(tenants, 1):
            name = tenant.get("name", "Без названия")[:28]
            tenant_id = tenant.get("id", "Без ID")[:34]
            is_default = "✓" if tenant.get("is_default", False) else ""
            description = tenant.get("description", "Без описания")[:30]
            
            print(f"{i:<3} {name:<30} {tenant_id:<36} {is_default:<12} {description}")
        
        print("=" * 80)

    def switch_to_tenant(self, tenant_id):
        """Переключается на указанный тенант"""
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            print(f"Тенант с ID {tenant_id} не найден")
            return False
        
        self.auth_manager.tenant_id = tenant_id
        if self.auth_manager.update_jwt_with_tenant(self.make_request):
            print(f"✅ Переключились на тенант: {tenant.get('name', 'Без названия')}")
            return True
        else:
            print(f"❌ Не удалось переключиться на тенант")
            return False