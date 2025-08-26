import json
import os

def convert_dbf_to_mssql(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    table_name = os.path.splitext(os.path.basename(json_path))[0]
    columns_sql = []
    
    for col in data["columns"]:
        name = col["name"]
        col_type = col["type"]
        length = col.get("length", 0)
        decimal = col.get("decimal", 0)
        
        # Преобразование типов
        if col_type == "C":
            sql_type = f"VARCHAR({length})" if length <= 8000 else "VARCHAR(MAX)"
        elif col_type == "N":
            sql_type = f"DECIMAL({length}, {decimal})"
        elif col_type == "L":
            sql_type = "BIT"
        elif col_type == "D":
            sql_type = "DATE"
        elif col_type == "M":
            sql_type = "VARCHAR(MAX)"
        elif col_type == "F":
            sql_type = "FLOAT"
        else:
            sql_type = "VARCHAR(MAX)"  # Тип по умолчанию
        
        columns_sql.append(f"[{name}] {sql_type}")
    
    # Добавляем разделитель между таблицами
    sql_command = f"-- Создание таблицы {table_name}\n"
    sql_command += f"CREATE TABLE [{table_name}] (\n    "
    sql_command += ",\n    ".join(columns_sql)
    sql_command += "\n);\n\n"
    
    return sql_command

# Список JSON файлов для обработки
json_files = [
    "ca.json", "cb.json", "d.json", "g.json", "i.json",
    "k.json", "m.json", "n.json", "p.json", "u.json",
    "x.json", "y.json", "z.json"
]

# Собираем все SQL команды в одну строку
all_sql_commands = ""

# Обрабатываем каждый файл
for json_file in json_files:
    if os.path.exists(json_file):
        try:
            sql_command = convert_dbf_to_mssql(json_file)
            all_sql_commands += sql_command
            print(f"Обработан файл: {json_file}")
        except Exception as e:
            error_msg = f"-- Ошибка обработки файла {json_file}: {str(e)}\n\n"
            all_sql_commands += error_msg
            print(f"Ошибка при обработке {json_file}: {e}")
    else:
        missing_msg = f"-- Файл {json_file} не найден\n\n"
        all_sql_commands += missing_msg
        print(f"Файл {json_file} не найден")

# Записываем все команды в единый файл
output_file = "all_tables.sql"
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(all_sql_commands)
    print(f"\nВсе SQL команды сохранены в файл: {output_file}")
except Exception as e:
    print(f"Ошибка при записи в файл: {e}")

# Также выводим результат в консоль (опционально)
print("\n" + "="*50)
print("Содержимое SQL файла:")
print("="*50)
print(all_sql_commands)