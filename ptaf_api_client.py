import os
import json
import argparse
from auth import AuthManager
from tenants import TenantManager
from base_client import BaseAPIClient
from api_client import APIClient
from base_manager import BaseManager
from traffic_settings import TrafficSettingsManager
from rules_manager import RulesManager
from policy_template_manager import PolicyTemplateManager
from policies_manager import PoliciesManager
from actions_manager import ActionsManager
from snapshot_manager import SnapshotManager
from roles_manager import RolesManager
from backends_manager import BackendsManager
from backup_manager import BackupManager
from global_lists_manager import GlobalListsManager
from version_utils import (
    get_release_from_versions_response,
    version_gte,
)

class PTAFClient:
    def __init__(self, config_file="ptaf_api_client_config.json", debug=False):
        self.config = self.load_config(config_file)
        self.debug = debug
        
        # Инициализация менеджеров
        self.auth_manager = AuthManager(
            base_url=self.config.get("ptaf_url"),
            username=self.config.get("username"),
            password=self.config.get("password"),
            api_path=self.config.get("api_path", "/api/ptaf/v4"),
            verify_ssl=self.config.get("verify_ssl", False),
            ssl_cert_path=self.config.get("ssl_cert_path")
        )
        
        self.base_client = BaseAPIClient(self.auth_manager, debug)
        self.api_client = APIClient(self.auth_manager, self.base_client.make_request)
        self.traffic_settings_manager = TrafficSettingsManager(self.api_client)
        self.rules_manager = RulesManager(self.api_client)
        self.policy_template_manager = PolicyTemplateManager(self.api_client)
        self.policies_manager = PoliciesManager(self.api_client)
        self.actions_manager = ActionsManager(self.api_client)
        self.global_lists_manager = GlobalListsManager(self.api_client)
        self.snapshot_manager = SnapshotManager(self.api_client)
        self.roles_manager = RolesManager(self.api_client)
        self.backends_manager = BackendsManager(self.api_client)
        self.backup_manager = BackupManager(self.api_client)
        self.tenant_manager = TenantManager(self.auth_manager, self.base_client.make_request)

    def load_config(self, config_file):
        # Если путь относительный — ищем конфиг рядом со скриптом (чтобы работало при запуске из любой директории)
        if not os.path.isabs(config_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            path_next_to_script = os.path.join(script_dir, config_file)
            if os.path.isfile(path_next_to_script):
                config_file = path_next_to_script
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Конфигурационный файл {config_file} не найден")
        except json.JSONDecodeError:
            raise Exception(f"Ошибка при чтении конфигурационного файла {config_file}")

    def select_tenant(self):
        """Позволяет пользователю выбрать тенант"""
        return self.tenant_manager.select_tenant_interactive()

    def manage_traffic_settings(self):
        """Управление настройками traffic_settings"""
        return self.traffic_settings_manager.manage_traffic_settings()

    def export_rules(self, export_dir="exported_rules", preserve_state=False):
        """Экспортирует правила"""
        return self.rules_manager.export_rules(export_dir, preserve_state)

    def export_rules_with_actions(self, export_dir="exported_rules_with_actions", preserve_state=False):
        """Экспортирует правила с сохранением связей с действиями"""
        return self.rules_manager.export_rules_with_actions(export_dir, preserve_state)

    def import_rules(self, directory_path, include_actions=False, preserve_state=False):
        """Импортирует правила из директории"""
        return self.rules_manager.import_rules(directory_path, include_actions, preserve_state)

    def delete_all_user_rules(self):
        """Удаляет все пользовательские правила"""
        return self.rules_manager.delete_all_user_rules()

    def manage_policy_templates_extended(self):
        """Расширенное управление шаблонами политик и политиками безопасности"""
        return self.policy_template_manager.manage_policy_templates_extended()

    def manage_actions_operations(self):
        """Управление операциями с действиями"""
        return self.actions_manager.manage_actions_operations()

    def manage_snapshots(self):
        """Управление получением конфигураций"""
        return self.snapshot_manager.manage_snapshots()

    def manage_restore(self):
        """Управление восстановлением конфигураций"""
        return self.snapshot_manager.manage_restore()

    def manage_tenant_transfer(self):
        """Управление переносом объектов между тенантами"""
        return self.snapshot_manager.manage_tenant_transfer()

    def get_snapshots_from_cli(self):
        """Получает конфигурации со всех тенантов (для CLI)"""
        return self.snapshot_manager.get_snapshots_from_cli()

    def print_failed_files(self):
        """Выводит список проблемных файлов"""
        return self.rules_manager.print_failed_files()

    def manage_dangerous_actions(self):
        """Управление опасными действиями"""
        return self.rules_manager.manage_dangerous_actions()

    def manage_tenants(self):
        """Расширенное управление тенантами"""
        return self.tenant_manager.manage_tenants_extended()

    def manage_global_lists(self):
        """Управление глобальных списков"""
        return self.global_lists_manager.manage_global_lists()

    def fetch_ptaf_release(self):
        """Загружает версию PTAF с сервера (GET about/versions) и сохраняет релиз в self.ptaf_release (например 4.3.0)."""
        if hasattr(self, "_ptaf_release_cached"):
            return self.ptaf_release
        self.ptaf_release = None
        try:
            response = self.api_client.get_versions()
            if response and response.status_code == 200:
                data = response.json()
                payload = data.get("data") if isinstance(data, dict) else None
                self.ptaf_release = get_release_from_versions_response(payload)
                if self.ptaf_release:
                    print(f"Версия PTAF: {self.ptaf_release}")
        except Exception:
            pass
        self._ptaf_release_cached = True
        return self.ptaf_release

    def manage_rules(self):
        """Управление правилами"""
        return self.rules_manager.manage_rules()

def main():
    parser = argparse.ArgumentParser(description="PTAF PRO API Client")
    parser.add_argument(
        "--source",
        help="Путь к директории с JSON файлами правил для импорта"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Экспортировать существующие правила"
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Удалить все пользовательские правила"
    )
    parser.add_argument(
        "--policy-template",
        action="store_true",
        help="Расширенное управление шаблонами политик и политиками безопасности"
    )
    parser.add_argument(
        "--traffic-settings",
        action="store_true",
        help="Управление настройками traffic_settings"
    )
    parser.add_argument(
        "--actions",
        action="store_true",
        help="Управление действиями в правилах"
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Получить конфигурации со всех доступных тенантов"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Восстановление конфигураций тенантов"
    )
    parser.add_argument(
        "--transfer",
        action="store_true",
        help="Копирование объектов между тенантами"
    )
    parser.add_argument(
        "--dangerous",
        action="store_true",
        help="Опасные действия"
    )
    parser.add_argument(
        "--tenants",
        action="store_true",
        help="Работа с тенантами"
    )
    parser.add_argument(
        "--global-lists",
        action="store_true",
        help="Управление глобальных списков"
    )
    parser.add_argument(
        "--rules",
        action="store_true",
        help="Работа с правилами"
    )
    parser.add_argument(
        "--config",
        default="ptaf_api_client_config.json",
        help="Путь к конфигурационному файлу"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить отладочный режим (показывать полные запросы и ответы)"
    )
    args = parser.parse_args()

    try:
        client = PTAFClient(config_file=args.config, debug=args.debug)
        
        # Сначала получаем токены
        if not client.auth_manager.get_jwt_tokens(client.base_client.make_request):
            print("Не удалось получить JWT токены")
            return

        # Загружаем версию PTAF для отображения пунктов меню по релизу
        client.fetch_ptaf_release()

        # Пункты меню: label, min_version (релиз, с которого доступен пункт), need_tenant
        MENU_ITEMS = [
            {"label": "Работа с правилами", "min_version": None, "need_tenant": False, "key": "rules"},
            {"label": "Управление шаблонами и политиками безопасности", "min_version": None, "need_tenant": False, "key": "policy_templates"},
            {"label": "Управление настройками traffic_settings", "min_version": None, "need_tenant": True, "key": "traffic_settings"},
            {"label": "Управление действиями в правилах", "min_version": None, "need_tenant": False, "key": "actions"},
            {"label": "Получение конфигураций тенантов", "min_version": None, "need_tenant": False, "key": "snapshots"},
            {"label": "Восстановление конфигураций тенантов", "min_version": None, "need_tenant": True, "key": "restore"},
            {"label": "Копирование объектов между тенантами", "min_version": None, "need_tenant": False, "key": "transfer"},
            {"label": "Работа с тенантами", "min_version": None, "need_tenant": False, "key": "tenants"},
            {"label": "Управление глобальных списков", "min_version": "4.2.2", "need_tenant": False, "key": "global_lists"},
            {"label": "Выход", "min_version": None, "need_tenant": False, "key": "exit"},
        ]

        def run_menu_action(client, item):
            if item["key"] == "exit":
                return "exit"
            if item["need_tenant"] and not client.select_tenant():
                print("Не удалось выбрать тенант")
                return None
            handlers = {
                "rules": client.manage_rules,
                "policy_templates": client.manage_policy_templates_extended,
                "traffic_settings": client.manage_traffic_settings,
                "actions": client.manage_actions_operations,
                "snapshots": client.manage_snapshots,
                "restore": client.manage_restore,
                "transfer": client.manage_tenant_transfer,
                "tenants": client.manage_tenants,
                "global_lists": client.manage_global_lists,
            }
            fn = handlers.get(item["key"])
            if fn:
                fn()
            return None

        # Если нет аргументов - запускаем интерактивный режим
        if not any([args.source, args.export, args.delete_all, args.policy_template,
                    args.traffic_settings, args.actions, args.snapshot, args.restore,
                    args.transfer, args.dangerous, args.tenants, args.global_lists, args.rules]):
            while True:
                visible = [it for it in MENU_ITEMS if version_gte(client.ptaf_release, it.get("min_version") or "0.0.0")]
                print("\nГлавное меню:")
                for i, it in enumerate(visible, 1):
                    print(f"{i}. {it['label']}")
                choice = input(f"\nВыберите действие (1-{len(visible)}): ")
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(visible):
                        result = run_menu_action(client, visible[idx - 1])
                        if result == "exit":
                            return
                    else:
                        print("Некорректный выбор. Попробуйте снова.")
                except ValueError:
                    print("Некорректный выбор. Попробуйте снова.")
        else:
            # Минимальные версии для пунктов CLI (если None — проверка не выполняется)
            CLI_MIN_VERSIONS = {
                "global_lists": "4.2.2",
            }

            def check_cli_version(feature_key):
                min_ver = CLI_MIN_VERSIONS.get(feature_key)
                if not min_ver:
                    return True
                if not version_gte(client.ptaf_release, min_ver):
                    current = client.ptaf_release or "не определена"
                    print(f"Функция недоступна: требуется PTAF {min_ver} или выше. Текущая версия: {current}.")
                    return False
                return True

            # Обработка аргументов командной строки
            if args.rules:
                client.manage_rules()
            
            elif args.global_lists:
                if not check_cli_version("global_lists"):
                    return
                client.manage_global_lists()
            
            elif args.policy_template:
                client.manage_policy_templates_extended()
            
            elif args.export:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                
                # Спрашиваем, нужно ли сохранить связи с действиями
                include_actions = False
                choice = input("\nСохранить связи с действиями при экспорте? (y/n): ").lower()
                if choice == 'y':
                    include_actions = True
                    
                    # Спрашиваем, нужно ли сохранить состояние
                    preserve_state = False
                    choice = input("\nСохранить исходное состояние правил (включено/выключено)? (y/n): ").lower()
                    if choice == 'y':
                        preserve_state = True
                        client.export_rules_with_actions(preserve_state=preserve_state)
                    else:
                        client.export_rules_with_actions(preserve_state=False)
                else:
                    # Для экспорта без действий не спрашиваем о состоянии
                    export_dir = input("Введите путь для экспорта [exported_rules]: ").strip()
                    if not export_dir:
                        export_dir = "exported_rules"
                    client.export_rules(export_dir=export_dir, preserve_state=False)
            
            elif args.source:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                
                # Спрашиваем, нужно ли сохранить связи с действиями
                include_actions = False
                choice = input("\nСохранить связи с действиями при импорте? (y/n): ").lower()
                if choice == 'y':
                    include_actions = True
                    
                    # Спрашиваем, нужно ли сохранить состояние
                    preserve_state = False
                    choice = input("\nПеренести правила в исходном состоянии (включено/выключено)? (y/n): ").lower()
                    if choice == 'y':
                        preserve_state = True
                        client.import_rules(directory_path=args.source, include_actions=True, preserve_state=True)
                    else:
                        client.import_rules(directory_path=args.source, include_actions=True, preserve_state=False)
                else:
                    client.import_rules(directory_path=args.source, include_actions=False, preserve_state=False)
            
            elif args.delete_all:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.delete_all_user_rules()
            
            elif args.traffic_settings:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.manage_traffic_settings()
            
            elif args.actions:
                client.manage_actions_operations()
            
            elif args.snapshot:
                client.get_snapshots_from_cli()
            
            elif args.restore:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.manage_restore()
            
            elif args.transfer:
                client.manage_tenant_transfer()
            
            elif args.dangerous:
                client.manage_dangerous_actions()
            
            elif args.tenants:
                client.manage_tenants()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        
        if 'client' in locals() and hasattr(client, 'print_failed_files'):
            client.print_failed_files()

if __name__ == "__main__":
    main()
