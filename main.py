#!/usr/bin/env python3
import argparse
import sys
import os

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ptaf_api_client.config import Config
from ptaf_api_client.http_client import HttpClient
from ptaf_api_client.auth import AuthManager
from ptaf_api_client.commands import (
    ExportRulesCommand,
    ImportRulesCommand,
    DeleteRulesCommand,
    ManageTemplatesCommand,
    ManageTrafficCommand,
    InteractiveCommand
)

def main():
    parser = argparse.ArgumentParser(description="PTAF PRO API Client")
    parser.add_argument("--config", default="ptaf_api_client_config.json", help="Путь к конфигурационному файлу")
    parser.add_argument("--debug", action="store_true", help="Включить отладочный режим")
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # Парсер для экспорта
    export_parser = subparsers.add_parser("export", help="Экспорт правил")
    export_parser.add_argument("--output", "-o", default="exported_rules", help="Директория для экспорта")
    
    # Парсер для импорта
    import_parser = subparsers.add_parser("import", help="Импорт правил")
    import_parser.add_argument("--input", "-i", required=True, help="Директория с файлами правил")
    
    # Парсер для удаления
    delete_parser = subparsers.add_parser("delete", help="Удалить все пользовательские правила")
    
    # Парсер для управления шаблонами
    template_parser = subparsers.add_parser("templates", help="Управление шаблонами политик")
    
    # Парсер для управления настройками трафика
    traffic_parser = subparsers.add_parser("traffic", help="Управление настройками трафика")
    
    # Парсер для интерактивного режима
    subparsers.add_parser("interactive", help="Интерактивный режим")
    
    args = parser.parse_args()
    
    try:
        # Инициализация конфигурации и клиентов
        config = Config(args.config)
        http_client = HttpClient(config, debug=args.debug)
        auth_manager = AuthManager(config, http_client)
        
        # Выбор команды
        if args.command == "export":
            command = ExportRulesCommand(config, http_client, auth_manager)
            command.execute(export_dir=args.output)
        
        elif args.command == "import":
            command = ImportRulesCommand(config, http_client, auth_manager)
            command.execute(source_dir=args.input)
        
        elif args.command == "delete":
            command = DeleteRulesCommand(config, http_client, auth_manager)
            command.execute()
        
        elif args.command == "templates":
            command = ManageTemplatesCommand(config, http_client, auth_manager)
            command.execute()
        
        elif args.command == "traffic":
            command = ManageTrafficCommand(config, http_client, auth_manager)
            command.execute()
        
        elif args.command == "interactive" or not args.command:
            command = InteractiveCommand(config, http_client, auth_manager)
            command.execute()
        
        else:
            print("Неизвестная команда")
            parser.print_help()
    
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()