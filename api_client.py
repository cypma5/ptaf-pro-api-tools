# api_client.py (обновленный с ErrorHandler)
import json
from urllib.parse import urljoin
from error_handler import ErrorHandler

class APIClient:
    def __init__(self, auth_manager, make_request_func):
        self.auth_manager = auth_manager
        self.make_request = make_request_func
        self.error_handler = ErrorHandler(self)
    
    def _make_api_call(self, method, endpoint, **kwargs):
        """Универсальный метод для API вызовов"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/{endpoint}")
        return self.make_request(method, url, **kwargs)
    
    # ==================== ТЕНАНТЫ ====================
    def get_tenants(self):
        """Получить список тенантов"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "auth/account/tenants",
            operation_name="Получение списка тенантов"
        )
    
    def create_tenant(self, tenant_data):
        """Создать тенант"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "auth/tenants", json=tenant_data,
            operation_name="Создание тенанта"
        )
    
    # ==================== ДЕЙСТВИЯ ====================
    def get_actions(self):
        """Получить все действия"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/actions",
            operation_name="Получение списка действий"
        )
    
    def get_action_types(self):
        """Получить типы действий"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/action_types",
            operation_name="Получение типов действий"
        )
    
    def create_action(self, action_data):
        """Создать действие"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "config/actions", json=action_data,
            operation_name="Создание действия"
        )
    
    # ==================== СПИСКИ ====================
    def get_global_lists(self):
        """Получить глобальные списки"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/global_lists",
            operation_name="Получение глобальных списков"
        )
    
    def get_global_list_details(self, list_id):
        """Получить детали глобального списка"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/global_lists/{list_id}",
            operation_name=f"Получение деталей списка {list_id}"
        )
    
    def create_global_list(self, files_data):
        """Создать глобальный список (multipart/form-data)"""
        url = urljoin(self.auth_manager.base_url, f"{self.auth_manager.api_path}/config/global_lists")
        return self.error_handler.safe_api_call(
            self.make_request, "POST", url, files=files_data,
            operation_name="Создание глобального списка"
        )
    
    def get_lists(self):
        """Получить обычные списки"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/lists",
            operation_name="Получение списков"
        )
    
    # ==================== ШАБЛОНЫ ПОЛИТИК ====================
    def get_vendor_templates(self):
        """Получить системные шаблоны (наборы правил)"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/policies/templates/vendor",
            operation_name="Получение системных шаблонов"
        )
    
    def get_user_templates(self):
        """Получить пользовательские шаблоны"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/policies/templates/user",
            operation_name="Получение пользовательских шаблонов"
        )
    
    def get_templates_with_user_rules(self):
        """Получить шаблоны с пользовательскими правилами"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/policies/templates/with_user_rules",
            operation_name="Получение шаблонов с пользовательскими правилами"
        )
    
    def get_template_details(self, template_id):
        """Получить детали шаблона"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/user/{template_id}",
            operation_name=f"Получение деталей шаблона {template_id}"
        )
    
    def create_template(self, template_data):
        """Создать шаблон"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "config/policies/templates/user", json=template_data,
            operation_name="Создание шаблона"
        )
    
    def get_template_rules(self, template_id):
        """Получить правила шаблона"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/user/{template_id}/rules",
            operation_name=f"Получение правил шаблона {template_id}"
        )
    
    def get_template_rule_details(self, template_id, rule_id):
        """Получить детали правила шаблона"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/user/{template_id}/rules/{rule_id}",
            operation_name=f"Получение деталей правила {rule_id}"
        )
    
    def update_template_rule(self, template_id, rule_id, update_data):
        """Обновить правило шаблона"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/templates/user/{template_id}/rules/{rule_id}", json=update_data,
            operation_name=f"Обновление правила {rule_id}"
        )
    
    def get_template_rule_aggregation(self, template_id, rule_id):
        """Получить настройки агрегации правила"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation",
            operation_name=f"Получение агрегации правила {rule_id}"
        )
    
    def update_template_rule_aggregation(self, template_id, rule_id, aggregation_data):
        """Обновить настройки агрегации"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/templates/user/{template_id}/rules/{rule_id}/aggregation", json=aggregation_data,
            operation_name=f"Обновление агрегации правила {rule_id}"
        )
    
    # ==================== ПОЛИТИКИ БЕЗОПАСНОСТИ ====================
    def get_policies(self):
        """Получить политики безопасности"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/policies",
            operation_name="Получение политик безопасности"
        )
    
    def get_policy_details(self, policy_id):
        """Получить детали политики"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/{policy_id}",
            operation_name=f"Получение деталей политики {policy_id}"
        )
    
    def create_policy(self, policy_data):
        """Создать политику"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "config/policies", json=policy_data,
            operation_name="Создание политики"
        )
    
    def get_policy_system_rules(self, policy_id):
        """Получить системные правила политики"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/{policy_id}/rules",
            operation_name=f"Получение системных правил политики {policy_id}"
        )
    
    def get_policy_user_rules(self, policy_id):
        """Получить пользовательские правила политики"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/{policy_id}/user_rules",
            operation_name=f"Получение пользовательских правил политики {policy_id}"
        )
    
    def get_policy_system_rule_details(self, policy_id, rule_id):
        """Получить детали системного правила"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/{policy_id}/rules/{rule_id}",
            operation_name=f"Получение деталей системного правила {rule_id}"
        )
    
    def get_policy_user_rule_details(self, policy_id, rule_id):
        """Получить детали пользовательского правила"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/{policy_id}/user_rules/{rule_id}",
            operation_name=f"Получение деталей пользовательского правила {rule_id}"
        )
    
    def update_policy_system_rule(self, policy_id, rule_id, update_data):
        """Обновить системное правило"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/{policy_id}/rules/{rule_id}", json=update_data,
            operation_name=f"Обновление системного правила {rule_id}"
        )
    
    def update_policy_user_rule(self, policy_id, rule_id, update_data):
        """Обновить пользовательское правило"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/{policy_id}/user_rules/{rule_id}", json=update_data,
            operation_name=f"Обновление пользовательского правила {rule_id}"
        )
    
    # ==================== БЕКЕНДЫ ====================
    def get_backends(self):
        """Получить бекенды"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/backends",
            operation_name="Получение бекендов"
        )
    
    def create_backend(self, backend_data):
        """Создать бекенд"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "config/backends", json=backend_data,
            operation_name="Создание бекенда"
        )
    
    # ==================== РОЛИ ====================
    def get_roles(self):
        """Получить роли"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "auth/roles",
            operation_name="Получение ролей"
        )
    
    def create_role(self, role_data):
        """Создать роль"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "auth/roles", json=role_data,
            operation_name="Создание роли"
        )
    
    # ==================== НАСТРОЙКИ ТРАФИКА ====================
    def get_traffic_settings(self):
        """Получить настройки трафика"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/traffic_settings",
            operation_name="Получение настроек трафика"
        )
    
    def update_traffic_settings(self, settings_data):
        """Обновить настройки трафика"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", "config/traffic_settings", json=settings_data,
            operation_name="Обновление настроек трафика"
        )
    
    # ==================== СНАПШОТЫ ====================
    def get_snapshot(self):
        """Получить снапшот"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", "config/snapshot",
            operation_name="Получение снапшота"
        )
    
    def restore_snapshot(self, snapshot_data):
        """Восстановить снапшот"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", "config/snapshot", json=snapshot_data,
            operation_name="Восстановление снапшота"
        )
    
    # ==================== ПРАВИЛА ====================
    def create_user_rule(self, template_id, rule_data):
        """Создать пользовательское правило"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "POST", f"config/policies/templates/with_user_rules/{template_id}/rules", json=rule_data,
            operation_name=f"Создание пользовательского правила в шаблоне {template_id}"
        )
    
    def get_user_rules(self, template_id):
        """Получить пользовательские правила шаблона"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/with_user_rules/{template_id}/rules",
            operation_name=f"Получение пользовательских правил шаблона {template_id}"
        )
    
    def get_user_rule_details(self, template_id, rule_id):
        """Получить детали пользовательского правила"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "GET", f"config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}",
            operation_name=f"Получение деталей пользовательского правила {rule_id}"
        )
    
    def update_user_rule(self, template_id, rule_id, update_data):
        """Обновить пользовательское правило"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}", json=update_data,
            operation_name=f"Обновление пользовательского правила {rule_id}"
        )
    
    def delete_user_rule(self, template_id, rule_id):
        """Удалить пользовательское правило"""
        return self.error_handler.safe_api_call(
            self._make_api_call, "DELETE", f"config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}",
            operation_name=f"Удаление пользовательского правила {rule_id}"
        )
    
    def enable_user_rule(self, template_id, rule_id, enabled=True):
        """Включить/выключить пользовательское правило"""
        payload = {"enabled": enabled}
        return self.error_handler.safe_api_call(
            self._make_api_call, "PATCH", f"config/policies/templates/with_user_rules/{template_id}/rules/{rule_id}", json=payload,
            operation_name=f"Изменение состояния правила {rule_id}"
        )
    
    # ==================== УТИЛИТНЫЕ МЕТОДЫ ====================
    def _parse_response_items(self, response):
        """Парсит ответ API для извлечения items"""
        return self.error_handler.parse_response_items(response)
    
    def _check_response(self, response, success_codes=(200, 201, 204)):
        """Проверяет успешность ответа"""
        return self.error_handler.check_success(response, success_codes)