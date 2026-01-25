# error_handler.py (обновленный)
import time
import json

class ErrorHandler:
    def __init__(self, api_client):
        self.api_client = api_client
    
    def handle_401_error(self, response=None):
        """Обрабатывает ошибку 401 - обновляет токен"""
        print("Получена 401 ошибка, пытаемся обновить токен...")
        if self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
            print("✅ Токен успешно обновлен")
            return True
        else:
            print("❌ Не удалось обновить JWT токены")
            return False
    
    def handle_404_error(self, response=None):
        """Обрабатывает ошибку 404 - обновляет токен для текущего тенанта"""
        print("Обновляем токен для текущего тенанта...")
        
        # Сохраняем текущий тенант
        current_tenant_id = self.api_client.auth_manager.tenant_id
        
        # Получаем новые токены
        if not self.api_client.auth_manager.get_jwt_tokens(self.api_client.make_request):
            print("❌ Не удалось получить новые JWT токены")
            return False
        
        # Обновляем токен для текущего тенанта
        if current_tenant_id:
            self.api_client.auth_manager.tenant_id = current_tenant_id
            if not self.api_client.auth_manager.update_jwt_with_tenant(self.api_client.make_request):
                print("❌ Не удалось обновить токен для тенанта")
                return False
        
        print("✅ Токен успешно обновлен")
        return True
    
    def handle_common_error(self, response, operation_name=""):
        """Обрабатывает общие ошибки HTTP"""
        if not response:
            print(f"{operation_name}: Не удалось получить ответ от сервера")
            return False
        
        if response.status_code == 401:
            return self.handle_401_error(response)
        elif response.status_code == 404:
            return self.handle_404_error(response)
        elif response.status_code >= 400:
            print(f"{operation_name}: Ошибка {response.status_code}")
            if response.text:
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        print(f"Сообщение: {error_data['message']}")
                    elif 'error' in error_data:
                        print(f"Ошибка: {error_data['error']}")
                    else:
                        print(f"Ответ: {response.text[:200]}")
                except:
                    print(f"Ответ: {response.text[:200]}")
            return False
        
        return True
    
    def should_retry(self, response, max_retries=3, current_retry=0):
        """Определяет, нужно ли повторять запрос"""
        if current_retry >= max_retries:
            return False
        
        if response and response.status_code in [401, 404, 429, 500, 502, 503, 504]:
            return True
        
        return False
    
    def execute_with_retry(self, request_func, *args, max_retries=3, **kwargs):
        """Выполняет запрос с повторными попытками при ошибках"""
        for attempt in range(max_retries + 1):
            try:
                response = request_func(*args, **kwargs)
                
                if response and response.status_code < 400:
                    return response
                
                if attempt < max_retries and self.should_retry(response, max_retries, attempt):
                    print(f"⚠️ Попытка {attempt + 1}/{max_retries + 1}")
                    
                    if response.status_code == 401:
                        self.handle_401_error()
                    elif response.status_code == 404:
                        self.handle_404_error()
                    elif response.status_code == 429:
                        print("Слишком много запросов, ждем...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    elif response.status_code >= 500:
                        print("Ошибка сервера, повторяем...")
                        time.sleep(1)
                    
                    continue
                
                return response
                
            except Exception as e:
                print(f"Исключение при выполнении запроса: {e}")
                if attempt < max_retries:
                    print(f"Повторная попытка {attempt + 1}/{max_retries + 1}")
                    time.sleep(1)
                else:
                    return None
        
        return None
    
    def safe_api_call(self, api_method, *args, operation_name="", **kwargs):
        """Безопасный вызов API метода с обработкой ошибок"""
        response = api_method(*args, **kwargs)
        
        if not self.handle_common_error(response, operation_name):
            return None
        
        return response
    
    def parse_response_items(self, response, operation_name=""):
        """Парсит ответ и извлекает items с обработкой ошибок"""
        if not self.handle_common_error(response, operation_name):
            return None
        
        try:
            data = response.json()
            if isinstance(data, dict) and 'items' in data:
                return data['items']
            elif isinstance(data, list):
                return data
            else:
                print(f"{operation_name}: Неподдерживаемый формат ответа")
                return None
        except json.JSONDecodeError as e:
            print(f"{operation_name}: Ошибка декодирования JSON: {e}")
            return None
    
    def check_success(self, response, success_codes=(200, 201, 204), operation_name=""):
        """Проверяет успешность ответа"""
        if not self.handle_common_error(response, operation_name):
            return False
        
        if response.status_code in success_codes:
            return True
        
        return False