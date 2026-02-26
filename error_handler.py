# error_handler.py (обновленный)
import time
import json

class ErrorHandler:
    def __init__(self, api_client):
        self.api_client = api_client
        self.last_error = None  # Сохраняем детали последней ошибки
    
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
        """Обрабатывает общие ошибки HTTP и сохраняет детали"""
        
        # Случай 1: Нет ответа от сервера (response is None)
        if response is None:
            error_msg = f"{operation_name}: Не удалось получить ответ от сервера"
            print(error_msg)
            
            # Сохраняем детали ошибки
            self.last_error = {
                'error': error_msg,
                'status_code': None,
                'response_body': None,
                'error_message': "Нет ответа от сервера",
                'operation': operation_name
            }
            return False
        
        # Получаем тело ответа для ВСЕХ случаев (даже для успешных)
        response_body = None
        response_json = None
        
        if hasattr(response, 'text') and response.text:
            response_body = response.text
            # Пробуем распарсить JSON для детальной информации
            try:
                response_json = json.loads(response.text)
            except:
                pass
        
        # Сохраняем детали ответа для ВСЕХ случаев (включая успешные)
        self.last_error = {
            'status_code': response.status_code,
            'response_body': response_body,
            'response_body_preview': response_body[:500] if response_body else None,
            'response_json': response_json,
            'operation': operation_name,
            'headers': dict(response.headers) if hasattr(response, 'headers') else None
        }
        
        # Случай 2: Ошибка авторизации
        if response.status_code == 401:
            self.last_error['error_message'] = "Unauthorized - требуется обновление токена"
            result = self.handle_401_error(response)
            if not result:
                self.last_error['handled'] = False
            return result
        
        # Случай 3: Ошибка 404 - тенант или ресурс не найден
        elif response.status_code == 404:
            self.last_error['error_message'] = "Not Found - ресурс не найден"
            result = self.handle_404_error(response)
            if not result:
                self.last_error['handled'] = False
            return result
        
        # Случай 4: Ошибка 422 - Validation Error (особенно важна для правил)
        elif response.status_code == 422:
            error_msg = f"{operation_name}: Ошибка валидации 422"
            print(error_msg)
            
            # Извлекаем детали ошибки из JSON
            if response_json and isinstance(response_json, dict):
                self.last_error['error_message'] = "Validation Error"
                self.last_error['validation_errors'] = response_json
                
                # Пытаемся найти понятное сообщение об ошибке
                if 'message' in response_json:
                    self.last_error['error_message'] = response_json['message']
                    print(f"Сообщение: {response_json['message']}")
                elif 'error' in response_json:
                    self.last_error['error_message'] = response_json['error']
                    print(f"Ошибка: {response_json['error']}")
                elif 'detail' in response_json:
                    self.last_error['error_message'] = response_json['detail']
                    print(f"Детали: {response_json['detail']}")
                elif 'errors' in response_json:
                    self.last_error['error_message'] = "Ошибки валидации"
                    errors = response_json['errors']
                    print(f"Ошибки валидации: {json.dumps(errors, ensure_ascii=False)[:200]}")
                else:
                    # Если не нашли стандартные поля, показываем весь JSON
                    print(f"Ответ: {response_body[:500] if response_body else ''}")
            else:
                # Если не JSON, показываем текст
                self.last_error['error_message'] = response_body[:200] if response_body else f"HTTP {response.status_code}"
                if response_body:
                    print(f"Ответ: {response_body[:500]}")
            
            return False
        
        # Случай 5: Другие HTTP ошибки (4xx, 5xx)
        elif response.status_code >= 400:
            error_msg = f"{operation_name}: Ошибка {response.status_code}"
            print(error_msg)
            
            # Пытаемся распарсить JSON ответ
            if response_json and isinstance(response_json, dict):
                if 'message' in response_json:
                    self.last_error['error_message'] = response_json['message']
                    print(f"Сообщение: {response_json['message']}")
                elif 'error' in response_json:
                    self.last_error['error_message'] = response_json['error']
                    print(f"Ошибка: {response_json['error']}")
                elif 'detail' in response_json:
                    self.last_error['error_message'] = response_json['detail']
                    print(f"Детали: {response_json['detail']}")
                else:
                    self.last_error['error_message'] = response_body[:200] if response_body else ""
                    if response_body:
                        print(f"Ответ: {response_body[:500]}")
                
                # Сохраняем полные данные ошибки
                self.last_error['error_data'] = response_json
            else:
                self.last_error['error_message'] = response_body[:200] if response_body else f"HTTP {response.status_code}"
                if response_body:
                    print(f"Ответ: {response_body[:500]}")
            
            return False
        
        # Успешный ответ (2xx) - очищаем last_error
        self.last_error = None
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
                    
                    if response and response.status_code == 401:
                        self.handle_401_error()
                    elif response and response.status_code == 404:
                        self.handle_404_error()
                    elif response and response.status_code == 429:
                        print("Слишком много запросов, ждем...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    elif response and response.status_code >= 500:
                        print("Ошибка сервера, повторяем...")
                        time.sleep(1)
                    
                    continue
                
                return response
                
            except Exception as e:
                print(f"Исключение при выполнении запроса: {e}")
                self.last_error = {
                    'error': str(e),
                    'exception_type': type(e).__name__,
                    'exception': str(e),
                    'operation': kwargs.get('operation_name', 'unknown')
                }
                if attempt < max_retries:
                    print(f"Повторная попытка {attempt + 1}/{max_retries + 1}")
                    time.sleep(1)
                else:
                    return None
        
        return None
    
    def safe_api_call(self, api_method, *args, operation_name="", **kwargs):
        """Безопасный вызов API метода с обработкой ошибок"""
        try:
            response = api_method(*args, **kwargs)
            
            # Всегда обрабатываем ответ, даже если это ошибка
            self.handle_common_error(response, operation_name)
            
            # Возвращаем ответ в любом случае, чтобы вызывающий код мог его проверить
            return response
            
        except Exception as e:
            # Обрабатываем исключения, которые могли возникнуть при вызове метода
            error_msg = f"{operation_name}: Исключение при вызове API: {str(e)}"
            print(error_msg)
            self.last_error = {
                'error': error_msg,
                'exception': str(e),
                'exception_type': type(e).__name__,
                'operation': operation_name
            }
            return None
    
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
                error_msg = f"{operation_name}: Неподдерживаемый формат ответа"
                print(error_msg)
                self.last_error = {
                    'error': error_msg,
                    'response_data': str(data)[:500] if data else None
                }
                return None
        except json.JSONDecodeError as e:
            error_msg = f"{operation_name}: Ошибка декодирования JSON: {e}"
            print(error_msg)
            self.last_error = {
                'error': error_msg,
                'json_error': str(e),
                'response_body': response.text[:500] if hasattr(response, 'text') else None
            }
            return None
    
    def check_success(self, response, success_codes=(200, 201, 204), operation_name=""):
        """Проверяет успешность ответа"""
        if not self.handle_common_error(response, operation_name):
            return False
        
        if response.status_code in success_codes:
            return True
        
        return False
    
    def get_last_error_info(self):
        """Возвращает форматированную информацию о последней ошибке"""
        if not self.last_error:
            return "Нет информации об ошибке"
        
        info = []
        if 'operation' in self.last_error:
            info.append(f"Операция: {self.last_error['operation']}")
        if 'status_code' in self.last_error:
            info.append(f"Код: {self.last_error['status_code']}")
        if 'error_message' in self.last_error:
            info.append(f"Сообщение: {self.last_error['error_message']}")
        if 'error' in self.last_error:
            info.append(f"Ошибка: {self.last_error['error']}")
        if 'exception' in self.last_error:
            info.append(f"Исключение: {self.last_error['exception']}")
        if 'validation_errors' in self.last_error:
            info.append(f"Ошибки валидации: {json.dumps(self.last_error['validation_errors'], ensure_ascii=False, indent=2)}")
        if 'response_body_preview' in self.last_error and self.last_error['response_body_preview']:
            info.append(f"Тело ответа: {self.last_error['response_body_preview']}")
        elif 'response_body' in self.last_error and self.last_error['response_body']:
            body = self.last_error['response_body']
            if len(body) > 500:
                body = body[:500] + "..."
            info.append(f"Тело ответа: {body}")
        
        return "\n".join(info)