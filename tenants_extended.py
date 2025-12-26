from urllib.parse import urljoin

class TenantExtendedManager:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func

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
                from tenants import TenantManager
                tenant_manager = TenantManager(self.auth_manager, self.make_request)
                tenants = tenant_manager.get_available_tenants()
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
                        print(f"   Описание: {description}\n")
                else:
                    print("Не удалось получить список тенантов")
            elif choice == '3':
                return
            else:
                print("Некорректный выбор. Попробуйте снова.")
