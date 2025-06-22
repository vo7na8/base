# json_to_sql.py
import json
import logging
from pathlib import Path
from config import Config
from utils import setup_logger

logger = setup_logger(__name__)

# Соответствие типов DBF и SQL Server
DBF_TYPE_TO_SQL = {
    'C': lambda col: f"NVARCHAR({col['length']})" if col['length'] <= 4000 else "NVARCHAR(MAX)",
    'N': lambda col: (
        f"DECIMAL({col['length']}, {col['decimal']})" 
        if col['decimal'] > 0 
        else "INT" if col['length'] <= 9 
        else "BIGINT" if col['length'] <= 18 
        else f"DECIMAL({col['length']}, 0)"
    ),
    'L': lambda col: "BIT",
    'D': lambda col: "DATE",
    'F': lambda col: "FLOAT",
    'M': lambda col: "NVARCHAR(MAX)",
}

def map_dbf_to_sql_type(col_def):
    """Преобразует тип DBF в тип SQL Server."""
    dbf_type = col_def['type']
    if mapper := DBF_TYPE_TO_SQL.get(dbf_type):
        return mapper(col_def)
    logger.warning(f"Unknown type '{dbf_type}'. Using NVARCHAR(MAX)")
    return "NVARCHAR(MAX)"

def generate_sql_from_json(json_path, sql_dir):
    """Генерирует SQL-скрипт из JSON-описания структуры DBF."""
    try:
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"JSON read error ({json_path.name}): {str(e)}")
        return False

    if 'columns' not in data:
        logger.error(f"Missing 'columns' key in {json_path.name}")
        return False

    table_name = json_path.stem
    sql_columns = []
    
    # 1. Добавляем оригинальные колонки
    for col in data['columns']:
        col_name = col['name']
        sql_type = map_dbf_to_sql_type(col)
        sql_columns.append(f"[{col_name}] {sql_type}")

    # 2. Добавляем новые колонки периода (всегда после оригинальных)
    sql_columns.append("[OT_PER_Y] NVARCHAR(2)")  # Год периода
    sql_columns.append("[OT_PER_M] NVARCHAR(2)")  # Месяц периода
    sql_columns.append("[OT_PER_N] NVARCHAR(4)")  # Номер пакета загрузки

    sql_statement = (
        f"CREATE TABLE [{table_name}] (\n"
        "    " + ",\n    ".join(sql_columns) + "\n"
        ");"
    )

    sql_path = sql_dir / f"{table_name}.sql"
    try:
        with sql_path.open('w', encoding='utf-8') as sql_file:
            sql_file.write(sql_statement)
        logger.info(f"Generated SQL: {sql_path.name}")
        return True
    except Exception as e:
        logger.error(f"SQL write error: {str(e)}")
        return False

def main():
    """Обрабатывает все JSON файлы в директории."""
    Config.SQL_DIR.mkdir(exist_ok=True, parents=True)
    
    for json_path in Config.JSON_DIR.glob("*.json"):
        generate_sql_from_json(json_path, Config.SQL_DIR)

if __name__ == "__main__":
    main()