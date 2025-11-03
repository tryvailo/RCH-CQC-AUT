#!/usr/bin/env python3
"""
Валидация SQL скрипта миграции CQC → Care Homes v2.2
Версия: 1.0
Статический анализ без запуска PostgreSQL
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Результат проверки"""
    check_name: str
    passed: bool
    message: str
    severity: str  # 'critical', 'warning', 'info'

class SQLValidator:
    """Валидатор SQL скриптов"""
    
    def __init__(self, sql_file: Path):
        self.sql_file = sql_file
        self.content = sql_file.read_text(encoding='utf-8')
        self.results: List[ValidationResult] = []
        
    def validate(self) -> List[ValidationResult]:
        """Выполнить все проверки"""
        print("=" * 80)
        print("ВАЛИДАЦИЯ SQL СКРИПТА: CQC → Care Homes v2.2")
        print("=" * 80)
        print(f"Файл: {self.sql_file}")
        print("")
        
        # Группа проверок
        self._check_basic_structure()
        self._check_helper_functions()
        self._check_field_mapping()
        self._check_coordinates_handling()
        self._check_boolean_handling()
        self._check_date_handling()
        self._check_cqc_ratings()
        self._check_transactions()
        self._check_jsonb_structures()
        self._check_v2_2_fields()
        
        return self.results
    
    def _add_result(self, check_name: str, passed: bool, message: str, severity: str = 'info'):
        """Добавить результат проверки"""
        self.results.append(ValidationResult(check_name, passed, message, severity))
    
    def _check_basic_structure(self):
        """Проверка базовой структуры"""
        print("ГРУППА 1: Базовая структура")
        print("-" * 80)
        
        # Проверка версии
        if 'v7.3.1' in self.content or '7.3.1' in self.content:
            self._add_result('version', True, "Версия скрипта найдена", 'info')
            print("✅ Версия скрипта: v7.3.1")
        else:
            self._add_result('version', False, "Версия скрипта не найдена", 'warning')
            print("⚠️  Версия скрипта не указана")
        
        # Проверка ON_ERROR_STOP
        if r'\set ON_ERROR_STOP on' in self.content:
            self._add_result('error_stop', True, "ON_ERROR_STOP включен", 'info')
            print("✅ ON_ERROR_STOP включен")
        else:
            self._add_result('error_stop', False, "ON_ERROR_STOP отсутствует", 'warning')
            print("⚠️  ON_ERROR_STOP отсутствует")
        
        # Проверка транзакций
        if 'BEGIN;' in self.content or 'BEGIN' in self.content:
            self._add_result('transaction', True, "Транзакции используются", 'info')
            print("✅ Транзакции используются")
        else:
            self._add_result('transaction', False, "Транзакции не найдены", 'warning')
            print("⚠️  Транзакции не найдены")
        
        print("")
    
    def _check_helper_functions(self):
        """Проверка helper функций"""
        print("ГРУППА 2: Helper функции (10 функций)")
        print("-" * 80)
        
        required_functions = [
            ('clean_text', r'CREATE.*FUNCTION\s+clean_text'),
            ('safe_integer', r'CREATE.*FUNCTION\s+safe_integer'),
            ('safe_latitude', r'CREATE.*FUNCTION\s+safe_latitude'),
            ('safe_longitude', r'CREATE.*FUNCTION\s+safe_longitude'),
            ('validate_uk_coordinates', r'CREATE.*FUNCTION\s+validate_uk_coordinates'),
            ('safe_boolean', r'CREATE.*FUNCTION\s+safe_boolean'),
            ('safe_date', r'CREATE.*FUNCTION\s+safe_date'),
            ('normalize_cqc_rating', r'CREATE.*FUNCTION\s+normalize_cqc_rating'),
            ('safe_dormant', r'CREATE.*FUNCTION\s+safe_dormant'),
            ('extract_year', r'CREATE.*FUNCTION\s+extract_year'),
        ]
        
        found_count = 0
        for func_name, pattern in required_functions:
            if re.search(pattern, self.content, re.IGNORECASE | re.MULTILINE):
                self._add_result(f'function_{func_name}', True, f"Функция {func_name} найдена", 'info')
                print(f"✅ {func_name}()")
                found_count += 1
            else:
                self._add_result(f'function_{func_name}', False, f"Функция {func_name} отсутствует", 'critical')
                print(f"❌ {func_name}() - ОТСУТСТВУЕТ")
        
        if found_count == 10:
            print(f"✅ Все 10 функций найдены")
        else:
            print(f"⚠️  Найдено {found_count}/10 функций")
        
        print("")
    
    def _check_field_mapping(self):
        """Проверка маппинга полей"""
        print("ГРУППА 3: Маппинг полей")
        print("-" * 80)
        
        # КРИТИЧНО: has_*_license из regulated_activity_*
        critical_checks = [
            ('has_nursing_care_license', r'regulated_activity_nursing_care.*has_nursing_care_license', True),
            ('has_personal_care_license', r'regulated_activity_personal_care.*has_personal_care_license', True),
            ('wrong_service_type_mapping', r'service_type.*has_.*_license', False),  # НЕ должно быть
        ]
        
        for check_name, pattern, should_exist in critical_checks:
            matches = re.findall(pattern, self.content, re.IGNORECASE | re.MULTILINE)
            if should_exist:
                if matches:
                    self._add_result(f'mapping_{check_name}', True, f"Правильный маппинг: {check_name}", 'info')
                    print(f"✅ {check_name}: правильный источник")
                else:
                    self._add_result(f'mapping_{check_name}', False, f"Неправильный маппинг: {check_name}", 'critical')
                    print(f"❌ {check_name}: НЕПРАВИЛЬНЫЙ источник")
            else:
                if matches:
                    self._add_result(f'mapping_{check_name}', False, f"Найдено неправильное использование: {check_name}", 'critical')
                    print(f"❌ {check_name}: НЕ должно использоваться service_type для лицензий")
                else:
                    self._add_result(f'mapping_{check_name}', True, f"Правильно: {check_name} не используется", 'info')
        
        print("")
    
    def _check_coordinates_handling(self):
        """Проверка обработки координат"""
        print("ГРУППА 4: Обработка координат")
        print("-" * 80)
        
        # Проверка использования safe функций
        if re.search(r'safe_latitude\s*\(', self.content):
            self._add_result('coord_latitude', True, "Используется safe_latitude", 'info')
            print("✅ safe_latitude() используется")
        else:
            self._add_result('coord_latitude', False, "safe_latitude не используется", 'critical')
            print("❌ safe_latitude() НЕ используется")
        
        if re.search(r'safe_longitude\s*\(', self.content):
            self._add_result('coord_longitude', True, "Используется safe_longitude", 'info')
            print("✅ safe_longitude() используется")
        else:
            self._add_result('coord_longitude', False, "safe_longitude не используется", 'critical')
            print("❌ safe_longitude() НЕ используется")
        
        # Проверка UK validation
        if re.search(r'49.*61.*-8.*2', self.content) or re.search(r'latitude.*49.*61', self.content):
            self._add_result('coord_validation', True, "UK validation присутствует", 'info')
            print("✅ UK validation (49-61, -8 to 2) присутствует")
        else:
            self._add_result('coord_validation', False, "UK validation отсутствует", 'warning')
            print("⚠️  UK validation может отсутствовать")
        
        print("")
    
    def _check_boolean_handling(self):
        """Проверка обработки boolean"""
        print("ГРУППА 5: Обработка boolean")
        print("-" * 80)
        
        if re.search(r'safe_boolean\s*\(', self.content):
            self._add_result('boolean_safe', True, "Используется safe_boolean", 'info')
            print("✅ safe_boolean() используется")
        else:
            self._add_result('boolean_safe', False, "safe_boolean не используется", 'critical')
            print("❌ safe_boolean() НЕ используется")
        
        print("")
    
    def _check_date_handling(self):
        """Проверка обработки дат"""
        print("ГРУППА 6: Обработка дат")
        print("-" * 80)
        
        if re.search(r'safe_date\s*\(', self.content):
            self._add_result('date_safe', True, "Используется safe_date", 'info')
            print("✅ safe_date() используется")
        else:
            self._add_result('date_safe', False, "safe_date не используется", 'warning')
            print("⚠️  safe_date() может отсутствовать")
        
        # Проверка формата DD/MM/YYYY
        if 'DD/MM/YYYY' in self.content or 'DD-MM-YYYY' in self.content:
            self._add_result('date_format', True, "Формат DD/MM/YYYY поддерживается", 'info')
            print("✅ Формат DD/MM/YYYY поддерживается")
        
        print("")
    
    def _check_cqc_ratings(self):
        """Проверка обработки CQC рейтингов"""
        print("ГРУППА 7: CQC рейтинги")
        print("-" * 80)
        
        if re.search(r'normalize_cqc_rating\s*\(', self.content):
            self._add_result('rating_normalize', True, "Используется normalize_cqc_rating", 'info')
            print("✅ normalize_cqc_rating() используется")
        else:
            self._add_result('rating_normalize', False, "normalize_cqc_rating не используется", 'critical')
            print("❌ normalize_cqc_rating() НЕ используется")
        
        print("")
    
    def _check_transactions(self):
        """Проверка транзакций"""
        print("ГРУППА 8: Транзакции")
        print("-" * 80)
        
        has_begin = 'BEGIN;' in self.content or re.search(r'\bBEGIN\b', self.content)
        has_commit = 'COMMIT;' in self.content or re.search(r'\bCOMMIT\b', self.content)
        has_rollback = 'ROLLBACK' in self.content
        
        if has_begin and has_commit:
            self._add_result('transaction_structure', True, "Транзакции правильно структурированы", 'info')
            print("✅ BEGIN/COMMIT найдены")
        else:
            self._add_result('transaction_structure', False, "Транзакции неправильно структурированы", 'warning')
            print("⚠️  BEGIN/COMMIT могут отсутствовать")
        
        if has_rollback:
            self._add_result('transaction_rollback', True, "ROLLBACK присутствует", 'info')
            print("✅ ROLLBACK присутствует")
        
        print("")
    
    def _check_jsonb_structures(self):
        """Проверка JSONB структур"""
        print("ГРУППА 9: JSONB структуры")
        print("-" * 80)
        
        # Проверка regulated_activities
        if 'regulated_activities' in self.content:
            self._add_result('jsonb_regulated', True, "regulated_activities присутствует", 'info')
            print("✅ regulated_activities найдено")
            
            # Проверка структуры
            if '"activities"' in self.content:
                self._add_result('jsonb_structure', True, "Структура activities присутствует", 'info')
                print("✅ Структура 'activities' найдена")
        else:
            self._add_result('jsonb_regulated', False, "regulated_activities отсутствует", 'critical')
            print("❌ regulated_activities отсутствует")
        
        print("")
    
    def _check_v2_2_fields(self):
        """Проверка полей v2.2"""
        print("ГРУППА 10: Поля v2.2 (7 новых)")
        print("-" * 80)
        
        v2_2_fields = [
            'serves_dementia_band',
            'serves_children',
            'serves_learning_disabilities',
            'serves_detained_mha',
            'serves_substance_misuse',
            'serves_eating_disorders',
            'serves_whole_population',
        ]
        
        found_count = 0
        for field in v2_2_fields:
            if field in self.content:
                self._add_result(f'v2_2_{field}', True, f"Поле v2.2 найдено: {field}", 'info')
                print(f"✅ {field}")
                found_count += 1
            else:
                self._add_result(f'v2_2_{field}', False, f"Поле v2.2 отсутствует: {field}", 'critical')
                print(f"❌ {field} - ОТСУТСТВУЕТ")
        
        if found_count == 7:
            print(f"✅ Все 7 новых полей v2.2 найдены")
        else:
            print(f"⚠️  Найдено {found_count}/7 новых полей v2.2")
        
        print("")
    
    def print_summary(self):
        """Вывести итоговую статистику"""
        print("=" * 80)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        critical_failed = sum(1 for r in self.results if not r.passed and r.severity == 'critical')
        
        print(f"Всего проверок: {total}")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print(f"🔴 Критичных ошибок: {critical_failed}")
        print("")
        
        if critical_failed > 0:
            print("КРИТИЧНЫЕ ОШИБКИ:")
            for r in self.results:
                if not r.passed and r.severity == 'critical':
                    print(f"  ❌ {r.check_name}: {r.message}")
            print("")
        
        score = int((passed / total) * 100) if total > 0 else 0
        print(f"Оценка: {score}%")
        
        if critical_failed == 0 and score >= 95:
            print("✅ ВАЛИДАЦИЯ ПРОЙДЕНА")
        elif critical_failed == 0:
            print("⚠️  Валидация пройдена с предупреждениями")
        else:
            print("❌ ВАЛИДАЦИЯ НЕ ПРОЙДЕНА (критичные ошибки)")
        
        print("=" * 80)

def main():
    script_dir = Path(__file__).parent
    sql_file = script_dir / "step2_run_migration.sql"
    
    if not sql_file.exists():
        print(f"❌ Файл не найден: {sql_file}")
        sys.exit(1)
    
    validator = SQLValidator(sql_file)
    results = validator.validate()
    validator.print_summary()
    
    # Возвращаем код ошибки при критичных ошибках
    critical_failed = sum(1 for r in results if not r.passed and r.severity == 'critical')
    if critical_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

