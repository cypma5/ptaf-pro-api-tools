from ..base import BaseCommand
from .export_rules import ExportRulesCommand
from .import_rules import ImportRulesCommand
from .delete_rules import DeleteRulesCommand
from .manage_templates import ManageTemplatesCommand
from .manage_traffic import ManageTrafficCommand

class InteractiveCommand(BaseCommand):
    def execute(self):
        while True:
            print("\nГлавное меню:")
            print("1. Импорт правил")
            print("2. Экспорт правил")
            print("3. Удалить все пользовательские правила")
            print("4. Управление шаблонами политик")
            print("5. Управление настройками трафика")
            print("6. Выход")
            
            choice = input("\nВыберите действие (1-6): ")
            
            if choice == '1':
                source_dir = input("Введите путь к директории с JSON файлами: ").strip()
                if source_dir:
                    import_cmd = ImportRulesCommand(self.config, self.http_client, self.auth_manager)
                    import_cmd.execute(source_dir=source_dir)
                else:
                    print("Путь не может быть пустым")
            
            elif choice == '2':
                export_dir = input("Введите путь для экспорта [exported_rules]: ").strip() or "exported_rules"
                export_cmd = ExportRulesCommand(self.config, self.http_client, self.auth_manager)
                export_cmd.execute(export_dir=export_dir)
            
            elif choice == '3':
                delete_cmd = DeleteRulesCommand(self.config, self.http_client, self.auth_manager)
                delete_cmd.execute()
            
            elif choice == '4':
                template_cmd = ManageTemplatesCommand(self.config, self.http_client, self.auth_manager)
                template_cmd.execute()
            
            elif choice == '5':
                traffic_cmd = ManageTrafficCommand(self.config, self.http_client, self.auth_manager)
                traffic_cmd.execute()
            
            elif choice == '6':
                return
            
            else:
                print("Некорректный выбор. Попробуйте снова.")