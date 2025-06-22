#config.py
import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent
    NSI_DIR = BASE_DIR / "nsi"
    XML_DIR = BASE_DIR / "xml"
    DBF_DIR = BASE_DIR / "dbf"
    CSV_DIR = BASE_DIR / "csv"
    JSON_DIR = BASE_DIR / "json"
    XSD_DIR = BASE_DIR / "xsd"
    SQL_DIR = BASE_DIR / "sql"

    REPORTS_DIR = BASE_DIR / "reports"
    LOGS_DIR = BASE_DIR / "logs"

    NSI_ZIP_PATTERN = r"^NSI(\d{4})(\d{1,3})\.zip$"
    
    XML_FILE_PATTERN = r"^([A-Za-z0-9]{4})(\d{4})\.xml$"
    DBF_FILE_PATTERN = r"^([A-Za-z0-9]{3,4})(\d{4})\.dbf$"
    CSV_ZIP_PATTERN = "NSI{period}{update}_CONVERTED.zip"

    @classmethod
    def setup_directories(cls):
        for d in [
            cls.NSI_DIR,
            cls.XML_DIR,
            cls.DBF_DIR,
            cls.CSV_DIR,
            cls.JSON_DIR,
            cls.XSD_DIR,
            cls.REPORTS_DIR,
            cls.LOGS_DIR,
        ]:
            d.mkdir(exist_ok=True)

    @classmethod
    def get_csv_zip_name(cls, period: str, update: str) -> str:
        return cls.CSV_ZIP_PATTERN.format(
            period=period,
            update=update
        )

Config.setup_directories()