import os
from typing import Any, Dict, List, Optional

DEFAULT_FORMATS_FILE = os.path.join("config", "nginx_access_log_formats.yaml")

DEFAULT_FORMATS: List[Dict[str, Any]] = [
    {
        "name": "Combined (стандартный)",
        "format": (
            '$remote_addr - $remote_user [$time_local] "$request" $status '
            '$body_bytes_sent "$http_referer" "$http_user_agent"'
        ),
    },
    {
        "name": "Extended (с X-Forwarded-For)",
        "format": (
            '$remote_addr - $remote_user [$time_local] "$request" $status '
            '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"'
        ),
    },
    {
        "name": "Minimal (основные поля)",
        "format": '$remote_addr [$time_local] "$request" $status $body_bytes_sent',
    },
    {
        "name": "Пользовательский формат",
        "custom": True,
    },
]


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, path)


def _validate_formats(raw_formats: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_formats, list):
        return []

    validated: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_formats, 1):
        if not isinstance(item, dict) or "name" not in item:
            print(f"Пропущен формат #{index}: требуется поле name")
            continue

        if item.get("custom"):
            validated.append({"name": item["name"], "custom": True})
        elif item.get("format"):
            validated.append({"name": item["name"], "format": item["format"]})
        else:
            print(
                f"Пропущен формат '{item['name']}': укажите format или custom: true"
            )

    return validated


def load_access_log_formats(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Загружает список форматов access log из YAML-файла."""
    path = _resolve_path(config_path or DEFAULT_FORMATS_FILE)

    if not os.path.isfile(path):
        print(
            f"Файл форматов access log не найден ({path}), "
            "используются встроенные форматы"
        )
        return [item.copy() for item in DEFAULT_FORMATS]

    try:
        import yaml
    except ImportError:
        print("Пакет PyYAML не установлен, используются встроенные форматы")
        return [item.copy() for item in DEFAULT_FORMATS]

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except Exception as error:
        print(f"Ошибка чтения {path}: {error}, используются встроенные форматы")
        return [item.copy() for item in DEFAULT_FORMATS]

    validated = _validate_formats(data.get("formats") if isinstance(data, dict) else None)
    if not validated:
        print(f"Некорректная структура {path}, используются встроенные форматы")
        return [item.copy() for item in DEFAULT_FORMATS]

    return validated
