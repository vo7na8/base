# nsimp.py
import re
import zipfile
import csv
from datetime import datetime
from pathlib import Path
import shutil
from config import Config
from utils import setup_logger, validate_filename, calculate_sha256

logger = setup_logger(__name__)

def process_package(zip_path: Path):
    try:
        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error(f"File not found: {zip_path}")
            return False

        filename = zip_path.name
        if not validate_filename(filename, Config.NSI_ZIP_PATTERN):
            logger.error(f"Invalid NSI filename: {filename}")
            return False

        mmyy, nn = re.match(Config.NSI_ZIP_PATTERN, filename).groups()
        report_path = Config.REPORTS_DIR / f"NSI_report_{mmyy}_{nn}.csv"

        original_copy = Config.NSI_DIR / filename
        shutil.copy(zip_path, original_copy)

        with zipfile.ZipFile(zip_path, "r") as zip_ref, \
             report_path.open("w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)
            writer.writerow([
                "Package", "Period", "Update", 
                "Filename", "Basename", "Type", "SHA-256", "Modified"
            ])

            for file_info in zip_ref.infolist():
                file_name = file_info.filename
                file_path = Path(file_name)
                ext = file_path.suffix[1:].lower()
                if ext not in ("xml", "dbf"):
                    continue

                # Извлекаем basename (имя без последних 4 цифр и расширения)
                basename = (file_path.stem[:-4] if file_path.stem[-4:].isdigit() else file_path.stem).upper()

                target_dir = Config.XML_DIR if ext == "xml" else Config.DBF_DIR
                target_path = target_dir / Path(file_name).name

                with zip_ref.open(file_name) as f:
                    file_hash = calculate_sha256(f)
                    target_path.write_bytes(f.read())

                modified = datetime(*file_info.date_time).strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    filename, 
                    mmyy, 
                    nn, 
                    target_path.name, 
                    basename,
                    ext.upper(), 
                    file_hash, 
                    modified
                ])
                logger.info(f"Extracted: {target_path.name}")

        logger.info(f"Processing complete: {report_path}")
        
        return (mmyy, nn, original_copy)

    except Exception as e:
        logger.error(f"Error processing package: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    import sys
    process_package(sys.argv[1]) if len(sys.argv) > 1 else print("Usage: imp.py <zip_path>")