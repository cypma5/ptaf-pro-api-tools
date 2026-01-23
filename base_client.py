# base_client.py
import json
import requests
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseAPIClient:
    def __init__(self, auth_manager, debug=False):
        self.auth_manager = auth_manager
        self.debug = debug
        self.headers = {
            "User-Agent": "PTAF-API-Client/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _debug_request(self, method, url, **kwargs):
        """Выводит отладочную информацию о запросе"""
        if not self.debug:
            return
        
        print(f"\n=== {method} {url} ===")
        if 'json' in kwargs:
            print(f"Body: {json.dumps(kwargs['json'], indent=2, ensure_ascii=False)[:500]}")

    def _debug_response(self, response):
        """Выводит отладочную информацию о ответе"""
        if not self.debug:
            return
        
        print(f"Status: {response.status_code}")
        if response.text:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:500]}")
            except:
                print(f"Response: {response.text[:500]}")

    def make_request(self, method, url, max_retries=2, **kwargs):
        """Универсальный метод для выполнения запросов"""
        auth_headers = self.auth_manager.get_auth_headers()
        headers = {**self.headers, **auth_headers}
        
        for attempt in range(max_retries + 1):
            try:
                self._debug_request(method, url, **kwargs)
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    verify=self.auth_manager.ssl_verify,
                    **kwargs
                )
                self._debug_response(response)

                # Если получили 401 и это не последняя попытка - обновляем токен
                if response.status_code == 401 and attempt < max_retries:
                    print("Получена 401 ошибка, пытаемся обновить токен...")
                    if self.auth_manager.get_jwt_tokens(self.make_request):
                        auth_headers = self.auth_manager.get_auth_headers()
                        headers = {**self.headers, **auth_headers}
                        continue
                    else:
                        print("Не удалось обновить JWT токены")
                        return None
                
                return response

            except requests.exceptions.RequestException as e:
                print(f"Ошибка при выполнении запроса: {e}")
                if attempt < max_retries:
                    time.sleep(1)
                else:
                    return None
        
        return None