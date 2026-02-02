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
        help="Перенос объектов между тенантами"
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

        # Если нет аргументов - запускаем интерактивный режим
        if not any([args.source, args.export, args.delete_all, args.policy_template,
                    args.traffic_settings, args.actions, args.snapshot, args.restore, 
                    args.transfer, args.dangerous, args.tenants, args.global_lists, args.rules]):
            while True:
                print("\nГлавное меню:")
                print("1. Работа с правилами")
                print("2. Управление шаблонами и политиками безопасности")
                print("3. Управление настройками traffic_settings")
                print("4. Управление действиями в правилах")
                print("5. Получение конфигураций тенантов")
                print("6. Восстановление конфигураций тенантов")
                print("7. Перенос объектов между тенантами")
                print("8. Работа с тенантами")
                print("9. Управление глобальных списков")
                print("10. Выход")
                
                choice = input("\nВыберите действие (1-10): ")
                
                if choice == '1':
                    client.manage_rules()
                
                elif choice == '2':
                    client.manage_policy_templates_extended()
                
                elif choice == '3':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_traffic_settings()
                
                elif choice == '4':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_actions_operations()
                
                elif choice == '5':
                    client.manage_snapshots()
                
                elif choice == '6':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_restore()
                
                elif choice == '7':
                    client.manage_tenant_transfer()
                
                elif choice == '8':
                    client.manage_tenants()
                
                elif choice == '9':
                    client.manage_global_lists()
                
                elif choice == '10':
                    return
                
                else:
                    print("Некорректный выбор. Попробуйте снова.")
        
        # Обработка аргументов командной строки
        else:
            if args.rules:
                client.manage_rules()
            
            elif args.global_lists:
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
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
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
            
            elif args.global_lists:
                client.manage_global_lists()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        
        if 'client' in locals() and hasattr(client, 'print_failed_files'):
            client.print_failed_files()

if __name__ == "__main__":
    main()
