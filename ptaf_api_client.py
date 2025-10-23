# ptaf_api_client.py
import os
import json
import argparse
from auth import AuthManager
from tenants import TenantManager
from base_client import BaseAPIClient
from traffic_settings import TrafficSettingsManager
from rules_manager import RulesManager
from policy_templates import PolicyTemplatesManager
from actions_manager import ActionsManager
from snapshot_manager import SnapshotManager

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
        self.tenant_manager = TenantManager(self.auth_manager, self.base_client.make_request)
        self.traffic_settings_manager = TrafficSettingsManager(self.auth_manager, self.base_client.make_request)
        self.rules_manager = RulesManager(self.auth_manager, self.base_client.make_request)
        self.policy_templates_manager = PolicyTemplatesManager(self.auth_manager, self.base_client.make_request)
        self.actions_manager = ActionsManager(self.auth_manager, self.base_client.make_request)
        self.snapshot_manager = SnapshotManager(self.auth_manager, self.base_client.make_request)

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

    def export_rules(self, export_dir="exported_rules"):
        """Экспортирует правила"""
        return self.rules_manager.export_rules(export_dir)

    def import_rules(self, directory_path):
        """Импортирует правила из директории"""
        return self.rules_manager.import_rules(directory_path)

    def delete_all_user_rules(self):
        """Удаляет все пользовательские правила"""
        return self.rules_manager.delete_all_user_rules()

    def manage_policy_templates(self):
        """Управление шаблонами политик"""
        return self.policy_templates_manager.manage_policy_templates()

    def manage_actions_replacement(self):
        """Управление заменой действий в шаблоне политики"""
        return self.actions_manager.manage_actions_replacement()

    def manage_actions_replacement_policy(self):
        """Управление заменой действий в политиках веб приложений"""
        return self.actions_manager.replace_actions_in_policy()

    def manage_snapshots(self):
        """Управление получением конфигураций"""
        return self.snapshot_manager.manage_snapshots()

    def get_snapshots_from_cli(self):
        """Получает конфигурации со всех тенантов (для CLI)"""
        return self.snapshot_manager.get_snapshots_from_cli()

    def print_failed_files(self):
        """Выводит список проблемных файлов"""
        return self.rules_manager.print_failed_files()

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
        "--policy",
        action="store_true",
        help="Управление шаблонами политик"
    )
    parser.add_argument(
        "--traffic-settings",
        action="store_true",
        help="Управление настройками traffic_settings"
    )
    parser.add_argument(
        "--replace-actions",
        action="store_true",
        help="Замена действий в шаблоне политики"
    )
    parser.add_argument(
        "--replace-actions-policy",
        action="store_true",
        help="Замена действий в политике веб приложения"
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Получить конфигурации со всех доступных тенантов"
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
        if not any([args.source, args.export, args.delete_all, args.policy, args.traffic_settings, args.replace_actions, args.replace_actions_policy, args.snapshot]):
            while True:
                print("\nГлавное меню:")
                print("1. Импорт правил")
                print("2. Экспорт правил")
                print("3. Удалить все пользовательские правила")
                print("4. Управление шаблонами политик")
                print("5. Управление настройками traffic_settings")
                print("6. Замена действий в шаблоне политики")
                print("7. Замена действий в политике веб приложения")
                print("8. Получение конфигураций тенантов")
                print("9. Выход")
                
                choice = input("\nВыберите действие (1-9): ")
                
                if choice == '1':
                    source_dir = input("Введите путь к директории с JSON файлами: ").strip()
                    if source_dir and os.path.isdir(source_dir):
                        if not client.select_tenant():
                            print("Не удалось выбрать тенант")
                            continue
                        client.import_rules(directory_path=source_dir)
                    else:
                        print("Указанная директория не существует")
                
                elif choice == '2':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    export_dir = input("Введите путь для экспорта [exported_rules]: ").strip()
                    if not export_dir:
                        export_dir = "exported_rules"
                    client.export_rules(export_dir)
                
                elif choice == '3':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.delete_all_user_rules()
                
                elif choice == '4':
                    client.manage_policy_templates()
                
                elif choice == '5':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_traffic_settings()
                
                elif choice == '6':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_actions_replacement()
                
                elif choice == '7':
                    if not client.select_tenant():
                        print("Не удалось выбрать тенант")
                        continue
                    client.manage_actions_replacement_policy()
                
                elif choice == '8':
                    client.manage_snapshots()
                
                elif choice == '9':
                    return
                
                else:
                    print("Некорректный выбор. Попробуйте снова.")
        
        # Обработка аргументов командной строки
        else:
            if args.export:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.export_rules()
            
            elif args.source:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.import_rules(directory_path=args.source)
            
            elif args.delete_all:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.delete_all_user_rules()
            
            elif args.policy:
                client.manage_policy_templates()
            
            elif args.traffic_settings:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.manage_traffic_settings()
            
            elif args.replace_actions:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.manage_actions_replacement()
            
            elif args.replace_actions_policy:
                if not client.select_tenant():
                    print("Не удалось выбрать тенант")
                    return
                client.manage_actions_replacement_policy()
            
            elif args.snapshot:
                # При использовании --snapshot получаем конфигурации со всех тенантов
                client.get_snapshots_from_cli()

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        if hasattr(client, 'print_failed_files'):
            client.print_failed_files()

if __name__ == "__main__":
    main()