# snapshot_parser.py
# Парсинг файла снапшота PTAF (GET /api/ptaf/v4/config/snapshot).
#
# Структура снапшота:
#   applications: [{ name, policy: { name }, hosts, locations, protection_mode }]
#   policies: [{ name, system_rules, user_rules, user_template: { name } }]
#   user_templates: [{ name, has_user_rules, system_rules: [{ name, enabled, actions, params }], system_template: { name }, user_rules: [...] }]
#
# Связь: application.policy.name -> policies[].name -> policies[].user_template.name -> user_templates[].name

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def load_snapshot_from_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Загружает JSON снапшота из файла. При ошибке возвращает None."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения снапшота из {filepath}: {e}")
        return None


def _root(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Корень данных: snapshot или snapshot['data']."""
    if not snapshot:
        return {}
    if "data" in snapshot and isinstance(snapshot["data"], dict):
        return snapshot["data"]
    return snapshot


def get_applications_from_snapshot(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Возвращает список приложений из снапшота.
    Каждый элемент: { name, policy_name, hosts, locations, protection_mode }.
    """
    root = _root(snapshot)
    apps = root.get("applications") or []
    result = []
    for a in apps:
        policy = a.get("policy") or {}
        policy_name = policy.get("name") if isinstance(policy, dict) else None
        result.append({
            "name": a.get("name", "Без названия"),
            "policy_name": policy_name or a.get("name"),
            "hosts": a.get("hosts") or [],
            "locations": a.get("locations") or ["/"],
            "protection_mode": a.get("protection_mode", "ACTIVE_PREVENTION"),
        })
    return result


def get_template_name_for_application(snapshot: Dict[str, Any], app_policy_name: str) -> Optional[str]:
    """
    По имени приложения (policy.name) возвращает имя шаблона политики (user_template.name).
    Связь: policies[].name == app_policy_name -> policies[].user_template.name.
    """
    root = _root(snapshot)
    policies = root.get("policies") or []
    for p in policies:
        if p.get("name") == app_policy_name:
            ut = p.get("user_template") or {}
            if isinstance(ut, dict):
                return ut.get("name")
            break
    return None


def _normalize_system_rule_override(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Поля переназначения системного правила: enabled, actions, variables (params в снапшоте)."""
    override: Dict[str, Any] = {}
    if rule.get("enabled") is not None:
        override["enabled"] = rule["enabled"]
    if rule.get("actions") is not None:
        override["actions"] = rule["actions"]
    variables = rule.get("variables")
    if variables is None and rule.get("params") is not None:
        variables = rule["params"]
    if variables is not None:
        override["variables"] = variables
    return override


def _merge_rule_overrides(
    base: Dict[str, Dict[str, Any]], extra: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Сливает оверрайды по имени правила; поля из extra перекрывают base."""
    merged = {name: dict(data) for name, data in base.items()}
    for name, fields in extra.items():
        merged.setdefault(name, {})
        merged[name].update(fields)
    return merged


def _merge_user_rules_by_name(
    base: List[Dict[str, Any]], extra: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Сливает пользовательские правила по name; поля из extra перекрывают base."""
    by_name: Dict[str, Dict[str, Any]] = {}
    for rule in base:
        name = rule.get("name")
        if name:
            by_name[name] = dict(rule)
    for rule in extra:
        name = rule.get("name")
        if not name:
            continue
        if name not in by_name:
            by_name[name] = dict(rule)
        else:
            existing = by_name[name]
            for key, value in rule.items():
                if value is not None:
                    if key == "configuration" and isinstance(value, dict):
                        cfg = dict(existing.get("configuration") or {})
                        cfg.update(value)
                        existing["configuration"] = cfg
                    else:
                        existing[key] = value
    return list(by_name.values())


def get_system_rule_overrides_from_snapshot(
    snapshot: Dict[str, Any], template_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Переназначения системных правил в шаблоне политики (user_templates).
    Ключ — имя правила; значение — enabled?, actions?, variables? (params в снапшоте).
    null в снапшоте = «как в базовом шаблоне».
    """
    root = _root(snapshot)
    templates = root.get("user_templates") or []
    for t in templates:
        if t.get("name") != template_name:
            continue
        overrides: Dict[str, Dict[str, Any]] = {}
        for r in t.get("system_rules") or []:
            name = r.get("name")
            if not name:
                continue
            normalized = _normalize_system_rule_override(r)
            if normalized:
                overrides[name] = normalized
        return overrides
    return {}


def get_policy_system_rule_overrides_from_snapshot(
    snapshot: Dict[str, Any], policy_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Локальные переназначения системных правил на уровне политики приложения (policies[]).
    Именно они соответствуют UI: application_policy / rules / rule / params.
    """
    root = _root(snapshot)
    for policy in root.get("policies") or []:
        if policy.get("name") != policy_name:
            continue
        overrides: Dict[str, Dict[str, Any]] = {}
        for r in policy.get("system_rules") or []:
            name = r.get("name")
            if not name:
                continue
            normalized = _normalize_system_rule_override(r)
            if normalized:
                overrides[name] = normalized
        return overrides
    return {}


def get_policy_user_rules_from_snapshot(
    snapshot: Dict[str, Any], policy_name: str
) -> List[Dict[str, Any]]:
    """Локальные переназначения пользовательских правил на уровне политики приложения."""
    root = _root(snapshot)
    for policy in root.get("policies") or []:
        if policy.get("name") == policy_name:
            return list(policy.get("user_rules") or [])
    return []


def get_user_rules_from_snapshot(
    snapshot: Dict[str, Any], template_name: str
) -> List[Dict[str, Any]]:
    """
    Возвращает пользовательские правила шаблона из снапшота (все, они считаются переназначениями).
    """
    root = _root(snapshot)
    templates = root.get("user_templates") or []
    for t in templates:
        if t.get("name") == template_name:
            return list(t.get("user_rules") or [])
    return []


def get_app_and_overrides_from_snapshot(
    snapshot: Dict[str, Any], app_name: str
) -> Optional[Dict[str, Any]]:
    """
    По имени приложения возвращает данные для переноса из снапшота:
    - name, policy_name, hosts, locations, protection_mode
    - template_name (имя шаблона политики)
    - system_rule_overrides: шаблон + локальные оверрайды политики (enabled, actions, variables)
    - user_rules: шаблон + локальные оверрайды политики
    Если приложение не найдено, возвращает None.
    """
    apps = get_applications_from_snapshot(snapshot)
    app = None
    for a in apps:
        if a.get("name") == app_name:
            app = dict(a)
            break
    if not app:
        return None
    policy_name = app.get("policy_name") or app.get("name")
    template_name = get_template_name_for_application(snapshot, policy_name)
    if not template_name:
        app["template_name"] = None
        app["system_rule_overrides"] = {}
        app["user_rules"] = []
        return app
    app["template_name"] = template_name
    template_overrides = get_system_rule_overrides_from_snapshot(snapshot, template_name)
    policy_overrides = get_policy_system_rule_overrides_from_snapshot(snapshot, policy_name)
    app["system_rule_overrides"] = _merge_rule_overrides(template_overrides, policy_overrides)
    template_user_rules = get_user_rules_from_snapshot(snapshot, template_name)
    policy_user_rules = get_policy_user_rules_from_snapshot(snapshot, policy_name)
    app["user_rules"] = _merge_user_rules_by_name(template_user_rules, policy_user_rules)
    return app


def get_meta_from_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Возвращает meta из снапшота (tenant.id, rule_set_version, created_at и т.д.)."""
    root = _root(snapshot)
    return dict(root.get("meta") or {})
