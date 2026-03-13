# version_utils.py — работа с версиями PTAF PRO для отображения пунктов меню по релизу
import re


def parse_release(full_version: str) -> str | None:
    """
    Извлекает релиз из полной версии.
    Пример: "4.3.0.12165" -> "4.3.0", "4.2.2.123" -> "4.2.2".
    """
    if not full_version or not isinstance(full_version, str):
        return None
    # Берём первые три компонента X.Y.Z
    parts = re.split(r"[.\-]", full_version.strip())
    if len(parts) >= 3:
        try:
            return ".".join(parts[:3])
        except Exception:
            pass
    return None


def get_release_from_versions_response(data: dict) -> str | None:
    """
    Из ответа GET /api/ptaf/v4/about/versions извлекает релиз.
    data = response["data"] с полями infra, ptaf_rule_set, ptaf_deploy.
    Используется infra для определения релиза (можно заменить на другой ключ при необходимости).
    """
    if not data or not isinstance(data, dict):
        return None
    # Приоритет: infra, затем ptaf_deploy, затем ptaf_rule_set
    for key in ("infra", "ptaf_deploy", "ptaf_rule_set"):
        raw = data.get(key)
        release = parse_release(raw)
        if release:
            return release
    return None


def version_gte(current: str | None, required: str) -> bool:
    """
    Проверяет, что текущая версия >= требуемой (сравнение по X.Y.Z).
    Если current is None (не удалось получить версию), возвращаем True — показываем пункт.
    """
    if current is None:
        return True
    try:
        c = [int(x) for x in re.split(r"[.\-]", current.strip())[:3]]
        r = [int(x) for x in re.split(r"[.\-]", required.strip())[:3]]
        # Добиваем нулями до длины 3
        while len(c) < 3:
            c.append(0)
        while len(r) < 3:
            r.append(0)
        return c >= r
    except (ValueError, TypeError):
        return True
