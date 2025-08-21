import requests
import json
from urllib.parse import urljoin

class HttpClient:
    def __init__(self, config, debug=False):
        self.config = config
        self.debug = debug
        self.auth_token = None
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
    
    def set_auth_token(self, token):
        self.auth_token = token
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        elif "Authorization" in self.headers:
            del self.headers["Authorization"]
    
    def _debug_request(self, method, url, **kwargs):
        if not self.debug:
            return
        
        print("\n=== DEBUG REQUEST ===")
        print(f"{method} {url}")
        print("Headers:", json.dumps(self.headers, indent=2, ensure_ascii=False))
        if 'json' in kwargs:
            print("Body:", json.dumps(kwargs['json'], indent=2, ensure_ascii=False))
        print("====================\n")
    
    def _debug_response(self, response):
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
    
    def request(self, method, url, max_retries=2, **kwargs):
        for attempt in range(max_retries + 1):
            try:
                self._debug_request(method, url, **kwargs)
                response = requests.request(
                    method,
                    url,
                    headers=self.headers,
                    verify=self.config.ssl_cert_path if self.config.ssl_cert_path else self.config.verify_ssl,
                    **kwargs
                )
                self._debug_response(response)

                if response.status_code == 401 and attempt < max_retries:
                    print("Получена 401 ошибка, требуется обновление токена")
                    return None
                
                return response

            except requests.exceptions.RequestException as e:
                print(f"Ошибка при выполнении запроса: {e}")
                return None
        
        return None
    
    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)
    
    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)
    
    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)
    
    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)