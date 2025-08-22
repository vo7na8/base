import json
import re
from pathlib import Path
from dbfread import DBF
import pandas as pd
from config import Config
from utils import setup_logger, validate_filename

logger = setup_logger(__name__)

def clean_string(value):
    """Очищает строку от переносов и лишних пробелов"""
    if isinstance(value, str):
        # Заменяем переносы строк и возврат каретки на пробелы
        value = re.sub(r'\r\n|\n|\r', ' ', value)
        # Удаляем двойные пробелы, оставшиеся после замены
        value = re.sub(r'\s{2,}', ' ', value)
    return value

def process_dbf(dbf_path):
    try:
        match = re.fullmatch(Config.DBF_FILE_PATTERN, dbf_path.name, re.IGNORECASE)
        if not validate_filename(dbf_path.name, Config.DBF_FILE_PATTERN):
            logger.error(f"Invalid DBF filename: {dbf_path.name}")
            return False

        base_name = match.group(1).lower()
        csv_path = Config.CSV_DIR / f"{base_name}.csv"
        json_path = Config.JSON_DIR / f"{base_name}.json"

        # Читаем DBF с обработкой текстовых полей
        dbf = DBF(dbf_path, char_decode_errors='replace')
        records = []
        for record in dbf:
            cleaned_record = {
                key: clean_string(value) 
                for key, value in record.items()
            }
            records.append(cleaned_record)

        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False)
        
        metadata = {
            "columns": [
                {
                    "name": field.name,
                    "type": field.type,
                    "length": field.length,
                    "decimal": field.decimal_count
                } for field in dbf.fields
            ]
        }
        
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Processed: {dbf_path.name} -> {csv_path.name}, {json_path.name}")
        return True

    except Exception as e:
        logger.error(f"{dbf_path.name} -> DBF processing error: {str(e)}")
        return False

def main():
    for dbf_path in Config.DBF_DIR.glob("*.dbf"):
        process_dbf(dbf_path)

if __name__ == "__main__":
    main()