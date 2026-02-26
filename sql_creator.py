import os
import csv
import json
import xml.etree.ElementTree as ET

def generate_sql_from_xsd(xsd_path, csv_path, output_dir):
    # Извлечь имя таблицы из пути к файлу
    table_name = os.path.splitext(os.path.basename(xsd_path))[0]
    output_path = os.path.join(output_dir, f"{table_name}.sql")
    
    # Прочитать заголовки из CSV
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    # Сгенерировать SQL
    columns = [f"[{header}] NVARCHAR(MAX)" for header in headers]
    sql = f"CREATE TABLE [{table_name}] (\n    " + ",\n    ".join(columns) + "\n);"
    
    # Сохранить результат
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sql)

def generate_sql_from_json(json_path, output_dir):
    # Извлечь имя таблицы из пути к файлу
    table_name = os.path.splitext(os.path.basename(json_path))[0]
    output_path = os.path.join(output_dir, f"{table_name}.sql")
    
    # Прочитать и парсить JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Сгенерировать SQL-колонки
    columns = []
    for col in schema["columns"]:
        name = col["name"]
        if col["type"] == "C":
            col_type = f"NVARCHAR({col['length']})"
        elif col["type"] == "N":
            col_type = f"DECIMAL({col['length']}, {col['decimal']})"
        elif col["type"] == "L":
            col_type = f"NVARCHAR(MAX)"
        elif col["type"] == "D":
            col_type = f"DATE"
        else:
            raise ValueError(f"Unknown type: {col['type']}")
        columns.append(f"[{name}] {col_type}")
    
    # Создать SQL
    sql = f"CREATE TABLE [{table_name}] (\n    " + ",\n    ".join(columns) + "\n);"
    
    # Сохранить результат
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sql)

def process_all_schemas(base_dir):
    # Создать выходную директорию
    output_dir = os.path.join(base_dir, "sql")
    os.makedirs(output_dir, exist_ok=True)
    
    # Обработать XSD схемы
    xsd_dir = os.path.join(base_dir, "xsd")
    csv_dir = os.path.join(base_dir, "csv")
    for xsd_file in os.listdir(xsd_dir):
        if xsd_file.endswith(".xsd"):
            xsd_path = os.path.join(xsd_dir, xsd_file)
            csv_path = os.path.join(csv_dir, xsd_file.replace(".xsd", ".csv"))
            if os.path.exists(csv_path):
                generate_sql_from_xsd(xsd_path, csv_path, output_dir)
    
    # Обработать JSON схемы
    json_dir = os.path.join(base_dir, "json")
    for json_file in os.listdir(json_dir):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_dir, json_file)
            generate_sql_from_json(json_path, output_dir)

if __name__ == "__main__":
    base_dir = "nsi"  # Корневая директория проекта
    process_all_schemas(base_dir)