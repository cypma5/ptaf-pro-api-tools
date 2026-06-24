# web_app_copy.py
# Копирование веб приложения (политики безопасности) в другой тенант (экспериментально).
#
# Структура данных для переноса и недостающая информация об API — см. WEB_APP_COPY_STRUCTURE ниже.

from __future__ import annotations

import copy
import os
import re
import shutil
import tempfile
from typing import Any, Dict, List, Optional

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _select_tenant(tenant_manager, prompt: str) -> Optional[Dict[str, Any]]:
    tenants = tenant_manager.get_available_tenants()
    if not tenants:
        print("Не удалось получить список тенантов")
        return None
    print(f"\n{prompt}")
    for i, tenant in enumerate(tenants, 1):
        name = tenant.get("name", "Без названия")
        tenant_id = tenant.get("id", "Без ID")
        is_default = tenant.get("is_default", False)
        default_marker = " (по умолчанию)" if is_default else ""
        print(f"{i}. {name}{default_marker} ({tenant_id})")
    while True:
        choice = input("\nВыберите номер тенанта (или 'q' для отмены): ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Введите номер из списка.")
            continue
        if 0 <= idx < len(tenants):
            return tenants[idx]
        print("Некорректный номер, попробуйте снова.")


def _select_application(applications: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not applications:
        print("В тенанте нет веб приложений.")
        return None
    print("\nДоступные веб приложения:")
    for i, app in enumerate(applications, 1):
        name = app.get("name", "Без названия")
        app_id = app.get("id", "Без ID")
        print(f"{i}. {name} ({app_id})")
    while True:
        choice = input("\nВыберите номер веб приложения (или 'q' для отмены): ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Введите номер из списка.")
            continue
        if 0 <= idx < len(applications):
            return applications[idx]
        print("Некорректный номер, попробуйте снова.")


def _is_uuid(value: Any) -> bool:
    return isinstance(value, str) and bool(_UUID_RE.match(value))


def _collect_source_rules_for_reference_mapping(
    source_rule_details_by_name: Dict[str, List[Dict[str, Any]]],
    source_user_rule_details_by_name: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for rule_list in source_rule_details_by_name.values():
        rules.extend(rule_list)
    for rule_list in source_user_rule_details_by_name.values():
        rules.extend(rule_list)
    return rules


def _build_global_list_mapping_for_policy_copy(
    api_client,
    rules_data: List[Dict[str, Any]],
    source_tenant_id: str,
    target_tenant_id: str,
) -> Dict[str, str]:
    """
    Маппинг ссылок на глобальные списки (UUID или имя из снапшота) -> UUID в целевом тенанте.
    """
    from global_lists_manager import GlobalListsManager
    from policy_template_manager import PolicyTemplateManager

    template_mgr = PolicyTemplateManager(api_client)
    refs: set[str] = set()
    for rule_data in rules_data:
        refs.update(str(ref) for ref in template_mgr._collect_rule_global_list_ids(rule_data))
    if not refs:
        return {}

    original_tenant_id = api_client.auth_manager.tenant_id
    source_by_id: Dict[str, Dict[str, Any]] = {}
    source_by_name: Dict[str, Dict[str, Any]] = {}

    try:
        if source_tenant_id:
            api_client.auth_manager.tenant_id = source_tenant_id
            if api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
                source_lists = GlobalListsManager(api_client).get_global_lists() or []
                for lst in source_lists:
                    list_id = lst.get("id")
                    list_name = lst.get("name")
                    if list_id:
                        source_by_id[str(list_id)] = lst
                    if list_name:
                        source_by_name[list_name] = lst

        api_client.auth_manager.tenant_id = target_tenant_id
        if not api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
            print("⚠️ Не удалось переключиться на целевой тенант для маппинга глобальных списков")
            return {}

        lists_manager = GlobalListsManager(api_client)
        mapping: Dict[str, str] = {}
        print(f"\nМаппинг глобальных списков для переноса правил политики ({len(refs)} ссылок)...")

        for ref in sorted(refs):
            list_name = ref
            list_type = "DYNAMIC"
            if _is_uuid(ref):
                source_list = source_by_id.get(ref)
                if source_list:
                    list_name = source_list.get("name") or ref
                    list_type = source_list.get("type") or list_type
                else:
                    target_by_id = next(
                        (
                            lst
                            for lst in (lists_manager.get_global_lists() or [])
                            if str(lst.get("id")) == ref
                        ),
                        None,
                    )
                    if target_by_id:
                        mapping[ref] = target_by_id.get("id")
                        print(f"  {ref} -> {mapping[ref]} (тот же UUID в целевом тенанте)")
                        continue
                    print(f"  ⚠️ Список с ID {ref} не найден в исходном тенанте")
                    continue
            else:
                source_list = source_by_name.get(ref)
                if source_list:
                    list_type = source_list.get("type") or list_type

            target_list = lists_manager.find_list_by_name_and_type_including_system(list_name, list_type)
            if not target_list and list_type == "DYNAMIC":
                target_list = lists_manager.find_list_by_name_and_type_including_system(list_name, "STATIC")
            if target_list and target_list.get("id"):
                mapping[ref] = target_list["id"]
                print(f"  '{list_name}' -> {target_list['id']}")
            else:
                print(f"  ⚠️ Глобальный список '{list_name}' ({list_type}) не найден в целевом тенанте")

        return mapping
    finally:
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)


def _apply_global_list_mapping_to_rule_details(
    details: Dict[str, Any],
    global_list_mapping: Dict[str, str],
    template_mgr,
) -> Dict[str, Any]:
    if not global_list_mapping:
        return details
    mapped = copy.deepcopy(details)
    template_mgr._apply_reference_mappings_to_rule_data(mapped, {}, global_list_mapping)
    return mapped


def _build_system_rule_policy_update(
    source_details: Dict[str, Any], target_details: Dict[str, Any]
) -> Dict[str, Any]:
    """PATCH config/policies/{id}/rules/{rule_id}: enabled, actions, variables (params в UI)."""
    update_data: Dict[str, Any] = {}
    if "enabled" in source_details and source_details.get("enabled") != target_details.get("enabled"):
        update_data["enabled"] = source_details.get("enabled")
    if "actions" in source_details and source_details.get("actions") != target_details.get("actions"):
        update_data["actions"] = source_details.get("actions", [])
    source_vars = source_details.get("variables")
    if source_vars is not None and source_vars != target_details.get("variables"):
        update_data["variables"] = source_vars
    return update_data


def _build_user_rule_policy_update(
    source_details: Dict[str, Any], target_details: Dict[str, Any]
) -> Dict[str, Any]:
    """PATCH config/policies/{id}/user_rules/{rule_id}: enabled, variables, configuration."""
    update_data: Dict[str, Any] = {}
    if "enabled" in source_details and source_details.get("enabled") != target_details.get("enabled"):
        update_data["enabled"] = source_details.get("enabled")
    source_vars = source_details.get("variables")
    if source_vars is not None and source_vars != target_details.get("variables"):
        update_data["variables"] = source_vars

    source_cfg = source_details.get("configuration") or {}
    target_cfg = target_details.get("configuration") or {}
    cfg_update: Dict[str, Any] = {}
    if source_cfg.get("actions") is not None and source_cfg.get("actions") != target_cfg.get("actions"):
        cfg_update["actions"] = source_cfg.get("actions", [])
    if source_cfg.get("parameters") is not None and source_cfg.get("parameters") != target_cfg.get("parameters"):
        cfg_update["parameters"] = source_cfg.get("parameters", [])
    if cfg_update:
        update_data["configuration"] = cfg_update

    # Обратная совместимость: actions на верхнем уровне снапшота
    if (
        not cfg_update.get("actions")
        and "actions" in source_details
        and source_details.get("actions") != target_details.get("actions")
    ):
        update_data["actions"] = source_details.get("actions", [])

    return update_data


def _compare_app_snapshots(
    source_snapshot: Dict[str, Any],
    target_snapshot: Dict[str, Any],
    app_name: str,
) -> None:
    """
    Сравнивает данные приложения в снапшотах исходного и целевого тенанта.
    Выводит отличия: приложение не найдено, параметры приложения, системные и пользовательские правила.
    """
    from snapshot_parser import get_app_and_overrides_from_snapshot

    src = get_app_and_overrides_from_snapshot(source_snapshot, app_name)
    tgt = get_app_and_overrides_from_snapshot(target_snapshot, app_name)

    print("\n" + "=" * 60)
    print(f"Сравнение снапшотов по приложению: {app_name}")
    print("=" * 60)

    if not src:
        print("  ⚠ В исходном снапшоте приложение не найдено.")
        return
    if not tgt:
        print("  ⚠ В целевом снапшоте приложение не найдено.")
        return

    diffs: List[str] = []

    # Параметры приложения
    for key in ("hosts", "locations", "protection_mode"):
        sv = src.get(key)
        tv = tgt.get(key)
        if sv != tv:
            diffs.append(f"  Приложение.{key}: в источнике {sv!r}, в целевом {tv!r}")

    # Системные правила (оверрайды)
    src_sys = src.get("system_rule_overrides") or {}
    tgt_sys = tgt.get("system_rule_overrides") or {}
    for name, s_data in src_sys.items():
        t_data = tgt_sys.get(name)
        if t_data is None:
            diffs.append(f"  Системное правило '{name}': есть в источнике (enabled={s_data.get('enabled')}, actions=...), в целевом — нет оверрайда")
        elif s_data != t_data:
            s_vars = s_data.get("variables")
            t_vars = t_data.get("variables")
            vars_note = ""
            if s_vars != t_vars:
                vars_note = f", variables отличаются"
            diffs.append(
                f"  Системное правило '{name}': отличается "
                f"(источник: enabled={s_data.get('enabled')}, actions={s_data.get('actions')}{vars_note}; "
                f"целевой: enabled={t_data.get('enabled')}, actions={t_data.get('actions')})"
            )
    for name in tgt_sys:
        if name not in src_sys:
            diffs.append(f"  Системное правило '{name}': оверрайд только в целевом (в источнике нет)")

    # Пользовательские правила (по имени)
    src_users = {r.get("name"): r for r in (src.get("user_rules") or []) if r.get("name")}
    tgt_users = {r.get("name"): r for r in (tgt.get("user_rules") or []) if r.get("name")}
    for name, s_r in src_users.items():
        t_r = tgt_users.get(name)
        if t_r is None:
            diffs.append(f"  Пользовательское правило '{name}': есть в источнике, в целевом отсутствует")
        else:
            if s_r.get("enabled") != t_r.get("enabled"):
                diffs.append(f"  Пользовательское правило '{name}': enabled в источнике {s_r.get('enabled')}, в целевом {t_r.get('enabled')}")
            s_actions = s_r.get("actions") or s_r.get("configuration", {}).get("actions") or []
            t_actions = t_r.get("actions") or t_r.get("configuration", {}).get("actions") or []
            if s_actions != t_actions:
                diffs.append(f"  Пользовательское правило '{name}': действия отличаются (источник: {len(s_actions)}, целевой: {len(t_actions)})")
            s_params = (s_r.get("configuration") or {}).get("parameters")
            t_params = (t_r.get("configuration") or {}).get("parameters")
            if s_params is not None and s_params != t_params:
                diffs.append(f"  Пользовательское правило '{name}': parameters отличаются")
            if s_r.get("variables") != t_r.get("variables"):
                diffs.append(f"  Пользовательское правило '{name}': variables отличаются")
    for name in tgt_users:
        if name not in src_users:
            diffs.append(f"  Пользовательское правило '{name}': только в целевом (в источнике нет)")

    if not diffs:
        print("  ✓ Отличий не найдено — объекты перенесены полностью.")
    else:
        print("  Объекты, не перенесённые или отличающиеся:")
        for line in diffs:
            print(line)
    print("=" * 60)


def _print_http_error(response, context: str, request_payload: Optional[Dict[str, Any]] = None) -> None:
    if response is None:
        print(f"{context}: нет ответа от сервера")
        return
    code = getattr(response, "status_code", None)
    body = getattr(response, "text", "") or "(пусто)"
    print(f"{context}: HTTP {code}")
    # Пытаемся вытащить METHOD и URI из объекта запроса
    req = getattr(response, "request", None)
    method = getattr(req, "method", None) if req is not None else None
    url = getattr(req, "url", None) if req is not None else None
    if method or url:
        print(f"  REQUEST: {method or 'UNKNOWN'} {url or ''}")
    # Тело запроса: либо явно переданный payload, либо фактически отправленное body
    if request_payload is not None:
        try:
            import json as _json

            req_body_str = _json.dumps(request_payload, ensure_ascii=False)
        except Exception:
            req_body_str = str(request_payload)
        print(f"  Request body: {req_body_str}")
    else:
        sent_body = getattr(req, "body", None) if req is not None else None
        if sent_body is not None:
            if isinstance(sent_body, (bytes, bytearray)):
                try:
                    sent_body_str = sent_body.decode("utf-8", errors="replace")
                except Exception:
                    sent_body_str = repr(sent_body)
            else:
                sent_body_str = str(sent_body)
            print(f"  Request body: {sent_body_str}")
    print(f"  Тело ответа: {body}")


def _select_application_from_snapshot(snapshot_apps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Выбор приложения из списка, полученного из снапшота (без id)."""
    if not snapshot_apps:
        print("В снапшоте нет приложений.")
        return None
    print("\nПриложения из снапшота:")
    for i, app in enumerate(snapshot_apps, 1):
        name = app.get("name", "Без названия")
        print(f"  {i}. {name}")
    while True:
        choice = input("\nВыберите номер приложения (или 'q' для отмены): ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(snapshot_apps):
                return snapshot_apps[idx]
        except ValueError:
            pass
        print("Некорректный ввод.")


def run_copy_web_app_flow(api_client, snapshot_manager) -> None:
    """
    Копирование одного веб приложения (application + policy) из одного тенанта в другой.

    Опционально: данные приложения и переназначения правил можно взять из файла снапшота —
    тогда в целевой тенант переносятся только переназначенные от дефолта изменения (из снапшота).
    """
    from tenants import TenantManager

    print("\n=== Копирование веб приложения в другой тенант (Экспериментальное) ===")

    tenant_manager = TenantManager(api_client.auth_manager, api_client.make_request)

    # 1. Исходный тенант
    source_tenant = _select_tenant(tenant_manager, "Выберите исходный тенант (где находится веб приложение):")
    if not source_tenant:
        return
    source_tenant_id = source_tenant.get("id")
    source_tenant_name = source_tenant.get("name", "Без названия")

    # 2. Переключаемся на исходный тенант
    original_tenant_id = api_client.auth_manager.tenant_id
    api_client.auth_manager.tenant_id = source_tenant_id
    if not api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
        print(f"Не удалось переключиться на исходный тенант {source_tenant_id}")
        api_client.auth_manager.tenant_id = original_tenant_id
        return

    # 2.1 Данные приложения и переназначения всегда из снапшота (GET /api/ptaf/v4/config/snapshot)
    from snapshot_parser import (
        get_applications_from_snapshot,
        get_app_and_overrides_from_snapshot,
    )
    print("Получение снапшота конфигурации (GET config/snapshot)...")
    snapshot_data = snapshot_manager.get_tenant_snapshot(source_tenant_id)
    if not snapshot_data:
        print("Не удалось получить снапшот конфигурации. Копирование отменено.")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    snapshot_apps = get_applications_from_snapshot(snapshot_data)
    chosen = _select_application_from_snapshot(snapshot_apps)
    if not chosen:
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    app_from_snapshot = get_app_and_overrides_from_snapshot(snapshot_data, chosen["name"])
    if not app_from_snapshot:
        print("Не удалось извлечь данные приложения из снапшота. Копирование отменено.")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    print(
        f"Из снапшота: приложение '{app_from_snapshot['name']}', шаблон '{app_from_snapshot.get('template_name')}', "
        f"оверрайдов системных правил: {len(app_from_snapshot.get('system_rule_overrides') or {})}, "
        f"пользовательских правил: {len(app_from_snapshot.get('user_rules') or [])}."
    )

    source_app = None
    source_policy_id = None
    source_template_id = None
    source_template_name = None
    source_rule_details_by_name: Dict[str, List[Dict[str, Any]]] = {}
    source_user_rule_details_by_name: Dict[str, List[Dict[str, Any]]] = {}

    app_name = app_from_snapshot.get("name", "Без названия")
    protection_mode = app_from_snapshot.get("protection_mode", "ACTIVE_PREVENTION")
    hosts = app_from_snapshot.get("hosts", []) or []
    locations = app_from_snapshot.get("locations", []) or ["/"]
    source_template_name = app_from_snapshot.get("template_name")
    overrides = app_from_snapshot.get("system_rule_overrides") or {}
    for rule_name, override in overrides.items():
        source_rule_details_by_name.setdefault(rule_name, []).append(dict(override))
    for ur in app_from_snapshot.get("user_rules") or []:
        name = ur.get("name")
        if name:
            source_user_rule_details_by_name.setdefault(name, []).append(dict(ur))
    if not source_template_name:
        print("В снапшоте не найден шаблон политики для приложения. Копирование отменено.")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    templates_resp = api_client.get_user_templates()
    templates = api_client._parse_response_items(templates_resp) or []
    for t in templates:
        if t.get("name") == source_template_name:
            source_template_id = t.get("id")
            break
    if not source_template_id:
        print(f"Шаблон '{source_template_name}' не найден в исходном тенанте по API. Копирование отменено.")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return

    source_apps_resp = api_client.get_applications()
    source_apps_list = api_client._parse_response_items(source_apps_resp) or []
    for app in source_apps_list:
        if app.get("name") == app_name:
            source_app = app
            source_policy_id = app.get("policy_id")
            break
    if source_policy_id:
        print(f"Политика безопасности исходного приложения: policy_id={source_policy_id}")
    else:
        print(
            f"⚠️ Не удалось определить policy_id исходного приложения '{app_name}' — "
            "экспорт шаблона будет без локальных переназначений политики."
        )

    print(f"\nВыбрано веб приложение '{app_name}' в тенанте '{source_tenant_name}'.")

    if not source_template_id or not source_template_name:
        print("Не удалось определить шаблон политики — копирование невозможно.")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return

    # 4.2. Экспортируем шаблон в исходном тенанте заранее (для копирования без переключения обратно на источник)
    template_export_file = None
    temp_export_dir = None
    try:
        from policy_template_manager import PolicyTemplateManager
        _template_mgr = PolicyTemplateManager(api_client)
        temp_export_dir = tempfile.mkdtemp()
        template_export_file = _template_mgr.export_template(
            source_template_id,
            temp_export_dir,
            include_user_rules=True,
            policy_id=source_policy_id,
        )
    except Exception as e:
        print(f"Предэкспорт шаблона не удался (будет использовано переключение на исходный тенант при копировании): {e}")
        template_export_file = None
        if temp_export_dir and os.path.isdir(temp_export_dir):
            shutil.rmtree(temp_export_dir, ignore_errors=True)
            temp_export_dir = None

    # 6. Целевой тенант
    target_tenant = _select_tenant(tenant_manager, "Выберите целевой тенант (куда копируем веб приложение):")
    if not target_tenant:
        # Возвращаемся в исходный тенант
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    target_tenant_id = target_tenant.get("id")
    target_tenant_name = target_tenant.get("name", "Без названия")

    if target_tenant_id == source_tenant_id:
        print("Исходный и целевой тенанты совпадают, копирование отменено.")
        api_client.auth_manager.tenant_id = original_tenant_id
        api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return

    # 6.1. Режим переноса правил, включённых в наборах пользовательских правил (глобально)
    print("\nПравила, включённые в наборах пользовательских правил (глобально):")
    print("  1. Перенести в том же состоянии (как в источнике)")
    print("  2. Перенести выключенными в наборе, но включить в политике этого приложения (защита от глобального включения в тенанте)")
    while True:
        choice = input("Выберите 1 или 2 [1]: ").strip() or "1"
        if choice == "1":
            preserve_user_rules_global_state = True
            break
        if choice == "2":
            preserve_user_rules_global_state = False
            break
        print("Введите 1 или 2.")
    if preserve_user_rules_global_state:
        print("Режим: перенос в том же состоянии.")
    else:
        print("Режим: в наборе — выключены, в политике приложения — включены по источнику.")

    # 7. Переключаемся на целевой тенант
    api_client.auth_manager.tenant_id = target_tenant_id
    print(f"DEBUG: переключаемся на целевой тенант {target_tenant_id}")
    if not api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
        print(f"Не удалось переключиться на целевой тенант {target_tenant_id}")
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return
    print(f"DEBUG: активный tenant_id после переключения на целевой: {api_client.auth_manager.tenant_id}")

    # 7.1. Ищем шаблон политики в целевом тенанте по имени (Policy Template ID берём по имени)
    target_templates_resp = api_client.get_user_templates()
    target_templates = api_client._parse_response_items(target_templates_resp) or []
    print(f"DEBUG: в целевом тенанте найдено {len(target_templates)} пользовательских шаблонов политик")
    target_template_id: Optional[str] = None
    for tpl in target_templates:
        if tpl.get("name") == source_template_name:
            target_template_id = tpl.get("id")
            break

    if not target_template_id:
        print(
            f"Не найден шаблон политики с именем '{source_template_name}' в целевом тенанте "
            f"'{target_tenant_name}'. Пытаемся автоматически скопировать шаблон в целевой тенант..."
        )
        from policy_template_manager import PolicyTemplateManager
        template_manager = PolicyTemplateManager(api_client)

        if template_export_file and os.path.isfile(template_export_file):
            # Импорт из заранее экспортированного файла — без переключения на исходный тенант
            copy_result = template_manager.copy_template_to_another_tenant(
                source_template_id, target_tenant_id, preserve_state=preserve_user_rules_global_state, export_file=template_export_file
            )
            template_export_file = None  # copy_template_to_another_tenant уже удалил файл
        else:
            # Fallback: переключаемся на исходный тенант и копируем (экспорт + импорт внутри copy)
            api_client.auth_manager.tenant_id = source_tenant_id
            if not api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
                print("Не удалось переключиться на исходный тенант для копирования шаблона")
                api_client.auth_manager.tenant_id = original_tenant_id
                if original_tenant_id:
                    api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
                return
            copy_result = template_manager.copy_template_to_another_tenant(
                source_template_id, target_tenant_id, preserve_state=preserve_user_rules_global_state
            )
            api_client.auth_manager.tenant_id = target_tenant_id
            if not api_client.auth_manager.update_jwt_with_tenant(api_client.make_request):
                print(f"Не удалось вернуться в целевой тенант {target_tenant_id} после копирования шаблона")
                api_client.auth_manager.tenant_id = original_tenant_id
                if original_tenant_id:
                    api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
                return

        if not copy_result:
            print(
                f"Автоматическое копирование шаблона '{source_template_name}' в целевой тенант "
                f"'{target_tenant_name}' завершилось неуспешно."
            )
            api_client.auth_manager.tenant_id = original_tenant_id
            if original_tenant_id:
                api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
            return

        print(
            f"Шаблон политики '{source_template_name}' успешно скопирован в целевой тенант "
            f"'{target_tenant_name}'. Повторно ищем его ID..."
        )
        target_templates_resp = api_client.get_user_templates()
        target_templates = api_client._parse_response_items(target_templates_resp) or []
        print(f"DEBUG: после копирования в целевом тенанте найдено {len(target_templates)} пользовательских шаблонов политик")
        for tpl in target_templates:
            if tpl.get("name") == source_template_name:
                target_template_id = tpl.get("id")
                break

        if not target_template_id:
            print(
                f"Не удалось найти скопированный шаблон политики '{source_template_name}' "
                f"в целевом тенанте '{target_tenant_name}' после копирования."
            )
            api_client.auth_manager.tenant_id = original_tenant_id
            if original_tenant_id:
                api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
            return

    # Очистка временного экспорта, если файл не был передан в copy (шаблон уже был в целевом тенанте)
    if template_export_file and os.path.isfile(template_export_file):
        try:
            os.remove(template_export_file)
        except Exception:
            pass
    if temp_export_dir and os.path.isdir(temp_export_dir):
        try:
            shutil.rmtree(temp_export_dir, ignore_errors=True)
        except Exception:
            pass

    # Тело запроса для создания/обновления приложения
    app_payload = {
        "name": app_name,
        "policy_template_id": target_template_id,
        "traffic_profiles": [],
        "proxy_ssl_verify": {"enabled": False},
        "enable_websockets": False,
        "protection_mode": protection_mode,
        "hosts": hosts,
        "locations": locations,
        "load_balancer": {"enabled": False},
        "ssl_options_reloaded": None,
    }

    # Сначала проверяем, есть ли в целевом тенанте приложение с таким именем — тогда делаем PATCH, а не POST
    target_apps_resp = api_client.get_applications()
    target_apps_list = api_client._parse_response_items(target_apps_resp) or []
    existing_app = next((a for a in target_apps_list if a.get("name") == app_name), None)

    created_app = None
    if existing_app:
        # Приложение уже есть — сразу обновляем (PATCH), в этом суть переноса
        print(
            f"\nВ целевом тенанте уже есть приложение с именем '{app_name}' — обновляем (PATCH)."
        )
        app_id = existing_app.get("id")
        print(f"Обновляем приложение (PATCH), ID: {app_id}...")
        patch_resp = api_client.update_application(app_id, app_payload)
        if not patch_resp or patch_resp.status_code not in (200, 204):
            _print_http_error(patch_resp, "Ошибка при обновлении веб приложения (PATCH)", app_payload)
            api_client.auth_manager.tenant_id = original_tenant_id
            if original_tenant_id:
                api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
            return
        if patch_resp.status_code == 200 and getattr(patch_resp, "text", None):
            try:
                created_app = patch_resp.json()
            except Exception:
                created_app = dict(existing_app)
        else:
            created_app = dict(existing_app)
        if not created_app.get("policy_id") and existing_app.get("policy_id"):
            created_app["policy_id"] = existing_app["policy_id"]
    else:
        # Приложения нет — создаём POST
        print(
            f"\nСоздаём веб приложение '{app_name}' в тенанте '{target_tenant_name}' "
            f"с шаблоном политики '{source_template_name}' (ID в целевом тенанте: {target_template_id})..."
        )
        print(f"DEBUG: создаём приложение под tenant_id={api_client.auth_manager.tenant_id}")
        create_app_resp = api_client.create_application(app_payload)
        if create_app_resp and create_app_resp.status_code in (200, 201):
            created_app = create_app_resp.json()
        else:
            # Возможно 422 must_be_unique (появилось с момента проверки) — предлагаем PATCH
            is_422_unique = (
                create_app_resp
                and getattr(create_app_resp, "status_code", None) == 422
                and getattr(create_app_resp, "text", None)
                and "must_be_unique" in (create_app_resp.text or "")
            )
            if is_422_unique:
                print(f"\nВ целевом тенанте уже существует приложение с именем '{app_name}' — обновляем (PATCH).")
                apps_resp = api_client.get_applications()
                target_apps_list = api_client._parse_response_items(apps_resp) or []
                existing_app = next((a for a in target_apps_list if a.get("name") == app_name), None)
                if not existing_app:
                    print(f"Не удалось найти приложение '{app_name}' в целевом тенанте.")
                    api_client.auth_manager.tenant_id = original_tenant_id
                    if original_tenant_id:
                        api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
                    return
                app_id = existing_app.get("id")
                print(f"Обновляем приложение (PATCH), ID: {app_id}...")
                patch_resp = api_client.update_application(app_id, app_payload)
                if not patch_resp or patch_resp.status_code not in (200, 204):
                    _print_http_error(patch_resp, "Ошибка при обновлении веб приложения (PATCH)", app_payload)
                    api_client.auth_manager.tenant_id = original_tenant_id
                    if original_tenant_id:
                        api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
                    return
                created_app = patch_resp.json() if (patch_resp.status_code == 200 and patch_resp.text) else dict(existing_app)
                if not created_app.get("policy_id"):
                    created_app["policy_id"] = existing_app.get("policy_id")
            else:
                _print_http_error(create_app_resp, "Ошибка при создании веб приложения в целевом тенанте", app_payload)
                api_client.auth_manager.tenant_id = original_tenant_id
                if original_tenant_id:
                    api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
                return

    if not created_app:
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return

    target_policy_id = created_app.get("policy_id")
    print(f"Веб приложение создано/обновлено. ID приложения: {created_app.get('id')}, policy_id: {target_policy_id}")

    if not target_policy_id:
        print("В ответе не найден policy_id, перенос настроек политики пропущен.")
        api_client.auth_manager.tenant_id = original_tenant_id
        api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
        return

    from policy_template_manager import PolicyTemplateManager

    _template_mgr = PolicyTemplateManager(api_client)
    rules_for_mapping = _collect_source_rules_for_reference_mapping(
        source_rule_details_by_name, source_user_rule_details_by_name
    )
    global_list_mapping = _build_global_list_mapping_for_policy_copy(
        api_client, rules_for_mapping, source_tenant_id, target_tenant_id
    )

    # 8. Переносим локальные переназначения системных правил политики (enabled, actions, variables/params)
    target_system_rules_resp = api_client.get_policy_system_rules(target_policy_id)
    target_system_rules = api_client._parse_response_items(target_system_rules_resp) or []

    updated_count = 0
    sys_no_source = 0
    sys_no_change = 0
    error_count = 0

    for rule in target_system_rules:
        rule_id = rule.get("id")
        rule_name = rule.get("name", "Без названия")

        source_rules_with_name = source_rule_details_by_name.get(rule_name) or []
        if not source_rules_with_name:
            sys_no_source += 1
            continue

        source_details = source_rules_with_name[0]
        source_details = _apply_global_list_mapping_to_rule_details(
            source_details, global_list_mapping, _template_mgr
        )

        target_details_resp = api_client.get_policy_system_rule_details(target_policy_id, rule_id)
        if not target_details_resp or target_details_resp.status_code != 200:
            _print_http_error(target_details_resp, f"Не удалось получить детали целевого правила '{rule_name}'")
            error_count += 1
            continue
        target_details = target_details_resp.json()

        update_data = _build_system_rule_policy_update(source_details, target_details)

        if not update_data:
            sys_no_change += 1
            continue

        update_resp = api_client.update_policy_system_rule(target_policy_id, rule_id, update_data)
        if update_resp and update_resp.status_code in (200, 204):
            fields = ", ".join(update_data.keys())
            print(f"Перенесены изменения для правила '{rule_name}' (системное): {fields}.")
            updated_count += 1
        else:
            _print_http_error(update_resp, f"Ошибка при обновлении правила '{rule_name}' в целевом тенанте")
            error_count += 1

    total_sys = len(target_system_rules)
    print(
        f"\nСистемные правила политики (всего в целевой политике: {total_sys}): "
        f"обновлено {updated_count}, нет в источнике {sys_no_source}, без изменений {sys_no_change}, ошибок {error_count}."
    )

    # 9. Перенос локальных переназначений пользовательских правил политики
    target_user_rules_resp = api_client.get_policy_user_rules(target_policy_id)
    target_user_rules = api_client._parse_response_items(target_user_rules_resp) or []
    user_updated = 0
    user_no_source = 0
    user_no_change = 0
    user_errors = 0
    for rule in target_user_rules:
        rule_id = rule.get("id")
        rule_name = rule.get("name", "Без названия")
        source_list = source_user_rule_details_by_name.get(rule_name) or []
        if not source_list:
            user_no_source += 1
            continue
        source_details = source_list[0]
        source_details = _apply_global_list_mapping_to_rule_details(
            source_details, global_list_mapping, _template_mgr
        )
        target_details_resp = api_client.get_policy_user_rule_details(target_policy_id, rule_id)
        if not target_details_resp or target_details_resp.status_code != 200:
            _print_http_error(target_details_resp, f"Детали пользовательского правила '{rule_name}'")
            user_errors += 1
            continue
        target_details = target_details_resp.json()
        update_data = _build_user_rule_policy_update(source_details, target_details)
        if not update_data:
            user_no_change += 1
            continue
        patch_resp = api_client.update_policy_user_rule(target_policy_id, rule_id, update_data)
        if patch_resp and patch_resp.status_code in (200, 204):
            fields = ", ".join(update_data.keys())
            print(f"Перенесены изменения для пользовательского правила '{rule_name}': {fields}.")
            user_updated += 1
        else:
            _print_http_error(patch_resp, f"Ошибка обновления пользовательского правила '{rule_name}'")
            user_errors += 1
    total_user = len(target_user_rules)
    print(
        f"Пользовательские правила политики (всего в целевой политике: {total_user}): "
        f"обновлено {user_updated}, нет в источнике {user_no_source}, без изменений {user_no_change}, ошибок {user_errors}."
    )

    print("\nПеренос веб приложения завершён.")
    print(
        f"  Системных правил: всего {total_sys}, обновлено {updated_count}, нет в источнике {sys_no_source}, без изменений {sys_no_change}, ошибок {error_count}"
    )
    print(
        f"  Пользовательских правил: всего {total_user}, обновлено {user_updated}, нет в источнике {user_no_source}, без изменений {user_no_change}, ошибок {user_errors}"
    )

    # Сравнение снапшотов по приложению (исходный vs целевой тенант)
    if input(f"\nСравнить снапшоты исходного и целевого тенанта по приложению '{app_name}'? (y/n): ").strip().lower() == "y":
        print("Получение снапшота целевого тенанта...")
        target_snapshot_resp = api_client.get_snapshot()
        target_snapshot = (target_snapshot_resp.json() if target_snapshot_resp and target_snapshot_resp.status_code == 200 else None)
        if not target_snapshot:
            print("  Не удалось получить снапшот целевого тенанта.")
        else:
            print("Получение снапшота исходного тенанта...")
            source_snapshot = snapshot_manager.get_tenant_snapshot(source_tenant_id)
            if not source_snapshot:
                print("  Не удалось получить снапшот исходного тенанта.")
            else:
                _compare_app_snapshots(source_snapshot, target_snapshot, app_name)
        # get_tenant_snapshot(source_tenant_id) переключил на исходный тенант — возвращаемся к original
        api_client.auth_manager.tenant_id = original_tenant_id
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)
    else:
        # Остаёмся в целевом тенанте до возврата ниже
        pass

    # Возвращаемся в исходный тенант (если ещё не вернулись после сравнения)
    if api_client.auth_manager.tenant_id != original_tenant_id:
        api_client.auth_manager.tenant_id = original_tenant_id
        print(f"DEBUG: возвращаемся к исходному tenant_id={original_tenant_id}")
        if original_tenant_id:
            api_client.auth_manager.update_jwt_with_tenant(api_client.make_request)

    # Предложить скопировать ещё одно веб приложение
    if input("\nСкопировать ещё одно веб приложение в другой тенант? (y/n): ").strip().lower() == "y":
        run_copy_web_app_flow(api_client, snapshot_manager)
