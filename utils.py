import logging
import hashlib
import re
from pathlib import Path
from config import Config
import pyodbc

def save_to_mssql(df, table_name, connection_string, batch_size=1000):
    """
    Универсальная загрузка DataFrame в MSSQL (append с предварительным удалением дублей).
    
    :param df: pandas.DataFrame
    :param table_name: имя таблицы в БД
    :param connection_string: строка подключения pyodbc
    :param batch_size: размер пачки вставки
    """
    if df.empty:
        return

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # формируем список колонок
    cols = list(df.columns)
    col_names = ",".join(cols)
    placeholders = ",".join(["?"] * len(cols))

    # --- Шаг 1. Удаляем записи с совпадающими ключами ---
    unique_keys = df[['nsi_ot_per', 'nsi_number']].drop_duplicates()
    delete_sql = f"DELETE FROM {table_name} WHERE nsi_ot_per = ? AND nsi_number = ?"

    cursor.fast_executemany = True
    cursor.executemany(delete_sql, [tuple(x) for x in unique_keys.to_numpy()])
    conn.commit()

    # --- Шаг 2. Вставляем новые данные ---
    insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
    data = [tuple(x) for x in df.to_numpy()]

    for i in range(0, len(data), batch_size):
        cursor.executemany(insert_sql, data[i:i+batch_size])
        conn.commit()

    cursor.close()
    conn.close()



def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(Config.LOGS_DIR / "nsi_processing.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def validate_filename(filename, pattern):
    return re.fullmatch(pattern, filename, re.IGNORECASE) is not None

#def calculate_sha256(file_obj):
#    hasher = hashlib.sha256()
#    while chunk := file_obj.read(4096):
#        hasher.update(chunk)
#    file_obj.seek(0)
#    return hasher.hexdigest()
    
def calculate_sha256(data: bytes) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()