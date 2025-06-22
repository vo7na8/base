import json
import re
from pathlib import Path
from dbfread import DBF
import pandas as pd
from config import Config
from utils import setup_logger, validate_filename

logger = setup_logger(__name__)

def process_dbf(dbf_path):
    try:
        match = re.fullmatch(Config.DBF_FILE_PATTERN, dbf_path.name, re.IGNORECASE)
        if not validate_filename(dbf_path.name, Config.DBF_FILE_PATTERN):
            logger.error(f"Invalid DBF filename: {dbf_path.name}")
            return False

        base_name = match.group(1).lower()
        csv_path = Config.CSV_DIR / f"{base_name}.csv"
        json_path = Config.JSON_DIR / f"{base_name}.json"

        dbf = DBF(dbf_path)
        pd.DataFrame(dbf).to_csv(csv_path, index=False)
        
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
        logger.error(f"DBF processing error: {str(e)}")
        return False

def main():
    for dbf_path in Config.DBF_DIR.glob("*.dbf"):
        process_dbf(dbf_path)

if __name__ == "__main__":
    main()