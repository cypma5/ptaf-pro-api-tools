# base_client.py
import json
import requests
from urllib.parse import urljoin

class BaseAPIClient:
    def __init__(self, auth_manager, debug=False):
        self.auth_manager = auth_manager
        self.debug = debug
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

    def _debug_request(self, method, url, **kwargs):
        """Выводит отладочную информацию о запросе"""
        if not self.debug:
            return
        
        print("\n=== DEBUG REQUEST ===")
        print(f"{method} {url}")
        headers_to_show = self.headers.copy()
        if 'Authorization' in headers_to_show:
            headers_to_show['Authorization'] = 'Bearer ***'
        print("Headers:", json.dumps(headers_to_show, indent=2, ensure_ascii=False))
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

    def make_request(self, method, url, max_retries=2, **kwargs):
        """Универсальный метод для выполнения запросов с обработкой 401 ошибки"""
        # Обновляем заголовки с актуальным токеном
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

                # Если получили 401 и это не первая попытка - обновляем токен
                if response.status_code == 401 and attempt < max_retries:
                    print("Получена 401 ошибка, пытаемся обновить токен...")
                    if not self.auth_manager.get_jwt_tokens(self.make_request):
                        print("Не удалось обновить JWT токены")
                        return None
                    continue
                
                return response

            except requests.exceptions.RequestException as e:
                print(f"Ошибка при выполнении запроса: {e}")
                return None
        
        return None  # Все попытки исчерпаны