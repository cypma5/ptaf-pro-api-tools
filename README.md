# PTAF PRO API Client

Утилита для работы с API PTAF PRO 4.2.1, позволяющая:
- Сохраять экспортировать конфигурацию тенанта
- Менять параметры traffic_settings
- Массовое изменение действий
- Массовая замена действий



## Установка
Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/ptaf-api-client.git
cd ptaf-api-client
```


3.Измените конфигурационный файл ptaf_api_client_config.json

```
{
  "ptaf_url": "https://your-ptaf-server",
  "username": "login",
  "password": "password",
  "api_path": "/api/ptaf/v4",
  "verify_ssl": false,
  "ssl_cert_path": null
}
```

# Использование
```
python3 ptaf_api_client.py [опции]

Без опции интерактивный режим

--source DIR - Импорт правил из указанной директории
--export - Экспорт правил
--delete-all - Удалить все пользовательские правила
--config FILE - Указать альтернативный конфигурационный файл
--debug - Включить отладочный режим
--snapshot - создать бекап конфигурации всех доступных изолированные пространств

```

# Ограничения
#### Не работает экспорт\импорт правил использующих динамические списки
