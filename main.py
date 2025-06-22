from pathlib import Path
import sys
from config import Config
from utils import setup_logger
import nsimp
import xml_to_csv
import dbf_to_csv_json
import pack_csv

logger = setup_logger("main")

def process_nsi(zip_path: Path) -> bool:
    # Обрабатываем входящий архив
    processing_result = nsimp.process_package(zip_path)
    if not processing_result:
        return False
    
    mmyy, nn, original_zip = processing_result
    
    # Конвертируем данные
    xml_to_csv.main()
    dbf_to_csv_json.main()
    
    # Упаковываем результат
    converted_zip = pack_csv.pack_converted_data(mmyy, nn, original_zip)
    if not converted_zip:
        return False
    
    # Очищаем временные данные
    return pack_csv.cleanup_temp_data()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main.py <path_to_nsi_zip>")
        sys.exit(1)
        
    success = process_nsi(Path(sys.argv[1]))
    sys.exit(0 if success else 1)