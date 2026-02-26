import re
import zipfile
import csv
from datetime import datetime
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from lxml import etree
from config import Config
from utils import setup_logger, validate_filename, calculate_sha256, save_to_mssql
import pandas as pd

logger = setup_logger(__name__)

def count_dbf_records(path: Path) -> int:
    try:
        from dbfread import DBF
        return len(DBF(str(path), encoding="cp1251", char_decode_errors="ignore"))
    except Exception as e:
        logger.warning(f"Cannot count DBF records for {path}: {e}")
        return -1


def count_xml_records(xml_path: Path, xsd_path: Path) -> int:
    try:
        # Загружаем XSD
        with open(xsd_path, "rb") as f:
            xsd_tree = etree.parse(f)
        xsd_root = xsd_tree.getroot()
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

        # Ищем первый элемент с maxOccurs="unbounded"
        first_unbounded = xsd_root.xpath(".//xs:element[@maxOccurs='unbounded']", namespaces=ns)
        if not first_unbounded:
            return len(etree.parse(str(xml_path)).getroot())
        
        elem_name = first_unbounded[0].get("name")
        # Считаем количество таких элементов в XML
        xml_tree = etree.parse(str(xml_path))
        count = len(xml_tree.findall(f".//{elem_name}"))
        return count

    except Exception as e:
        logger.warning(f"Cannot count XML records for {xml_path}: {e}")
        return -1

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
        report_path = Config.LOGS_DIR / f"NSI_report_{mmyy}_{nn}.csv"

        original_copy = Config.NSI_DIR / filename
        shutil.copy(zip_path, original_copy)

        rows = []  # будем копить данные для MSSQL + DataFrame

        with zipfile.ZipFile(zip_path, "r") as zip_ref, \
             report_path.open("w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)
            writer.writerow([
                "package_name", "nsi_ot_per", "nsi_number", 
                "filename", "basename", "ext", 
                "sha256", "modified", "records_read"
            ])

            for file_info in zip_ref.infolist():
                file_name = file_info.filename
                file_path = Path(file_name)
                ext = file_path.suffix[1:].lower()
                if ext not in ("xml", "dbf"):
                    continue

                basename = (file_path.stem[:-4] if file_path.stem[-4:].isdigit() else file_path.stem).lower()
                target_dir = Config.XML_DIR if ext == "xml" else Config.DBF_DIR
                target_path = target_dir / Path(file_name).name

                try:
                    with zip_ref.open(file_name) as f:
                        content = f.read()
                except zipfile.BadZipFile as e:
                    logger.error(f"Failed to read {file_name} from {zip_path}: {e}")
                    continue   # пропускаем этот файл

                file_hash = calculate_sha256(content)
                target_path.write_bytes(content)

                modified = datetime(*file_info.date_time).strftime("%Y-%m-%d %H:%M:%S")

                # считаем количество строк (только если файл успешно извлечён)
                if ext == "dbf":
                    records = count_dbf_records(target_path)
                else:
                    records = count_xml_records(target_path, Config.XSD_DIR / (basename + ".xsd"))

                # добавляем запись в отчёт
                row = [filename, mmyy, nn, target_path.name, basename, ext.lower(),
                       file_hash, modified, records]
                rows.append(row)
                writer.writerow(row)
                logger.info(f"Extracted: {target_path.name}, records={records}")

        # формируем DataFrame и грузим в MSSQL
        df = pd.DataFrame(rows, columns=[
            "package_name", "nsi_ot_per", "nsi_number", 
            "filename", "basename", "ext", 
            "sha256", "modified", "records_read"
        ])

        # строка подключения (лучше вынести в Config)
        conn_str = Config.MSSQL_CONN_STR
        logger.info(f"Start upload to MSSQL")
        #save_to_mssql(df, "nsi_reports", conn_str)
        logger.info(f"Upload completed!")
        
        logger.info(f"Processing complete: {report_path}")
        return (mmyy, nn, original_copy)

    except Exception as e:
        logger.error(f"Error processing package: {str(e)}", exc_info=True)
        return None
