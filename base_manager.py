# base_manager.py
import json

class BaseManager:
    """Базовый класс для всех менеджеров"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def _select_index(self, items, prompt):
        """Выбор индекса из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return index
                else:
                    print("Некорректный номер")
            except ValueError:
                print("Пожалуйста, введите число")
    
    def _select_multiple_indices(self, items, prompt):
        """Выбор нескольких индексов из списка"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() == 'q':
                    return None
                
                indices = [int(num.strip()) - 1 for num in choice.split(',') if num.strip().isdigit()]
                valid_indices = [i for i in indices if 0 <= i < len(items)]
                
                if not valid_indices:
                    print("Некорректные номера")
                    continue
                
                return valid_indices
                
            except ValueError:
                print("Пожалуйста, введите номера через запятую (например: 1,2,3)")
    
    def _select_item_from_list(self, items, prompt, name_field='name', id_field='id'):
        """Выбор элемента из списка с выводом"""
        if not items:
            print("Список пуст")
            return None
        
        print(f"\n{prompt}:")
        for i, item in enumerate(items, 1):
            name = item.get(name_field, f"Элемент {i}")
            item_id = item.get(id_field, 'Без ID')
            print(f"{i}. {name} (ID: {item_id})")
        
        index = self._select_index(items, "Выберите номер: ")
        if index is None:
            return None
        
        return items[index]
    
    def _confirm_action(self, message):
        """Подтверждение действия"""
        confirm = input(f"\n{message} (y/n): ").lower()
        return confirm == 'y'
    
    def _parse_response_items(self, response):
        """Парсит ответ API для извлечения items"""
        return self.api_client._parse_response_items(response)
    
    def _check_response(self, response, success_codes=(200, 201, 204)):
        """Проверяет успешность ответа"""
        return self.api_client._check_response(response, success_codes)