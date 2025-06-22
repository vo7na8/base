import zipfile
import logging
import shutil
from pathlib import Path
from config import Config
from utils import setup_logger

logger = setup_logger(__name__)

def pack_converted_data(period: str, update: str, original_zip: Path) -> Path:
    """
    Упаковывает все артефакты обработки в архив формата NSIMMYYNN_CONVERTED.zip
    """
    zip_name = Config.get_csv_zip_name(period, update)
    zip_path = Config.REPORTS_DIR / zip_name

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Добавляем CSV файлы
            for csv_file in Config.CSV_DIR.glob("*.csv"):
                zipf.write(csv_file, f"csv/{csv_file.name}")
                logger.debug(f"Added CSV: {csv_file.name}")

            # Добавляем JSON схемы
            for json_file in Config.JSON_DIR.glob("*.json"):
                zipf.write(json_file, f"json/{json_file.name}")
                logger.debug(f"Added JSON: {json_file.name}")

            # Добавляем XSD схемы
            for xsd_file in Config.XSD_DIR.glob("*.xsd"):
                zipf.write(xsd_file, f"xsd/{xsd_file.name}")
                logger.debug(f"Added XSD: {xsd_file.name}")

            # Добавляем исходный архив
            zipf.write(original_zip, f"source/{original_zip.name}")
            logger.debug(f"Added source: {original_zip.name}")

        logger.info(f"Created conversion package: {zip_path.name}")
        return zip_path

    except Exception as e:
        logger.error(f"Packaging failed: {str(e)}")
        return None

def cleanup_temp_data():
    """Очищает временные директории"""
    try:
        shutil.rmtree(Config.CSV_DIR)
        shutil.rmtree(Config.DBF_DIR)
        shutil.rmtree(Config.XML_DIR)
        shutil.rmtree(Config.JSON_DIR)
        
        Config.CSV_DIR.mkdir()
        Config.DBF_DIR.mkdir()
        Config.XML_DIR.mkdir()
        Config.JSON_DIR.mkdir()
        
        logger.info("Cleaned temporary directories")
        return True
    
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return False