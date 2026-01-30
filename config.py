import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent
    NSI_DIR = BASE_DIR / "temp" / "nsi"
    XML_DIR = BASE_DIR / "temp" / "xml"
    DBF_DIR = BASE_DIR / "temp" / "dbf"
    CSV_DIR = BASE_DIR / "temp" / "csv"
    JSON_DIR = BASE_DIR / "temp" / "json"
    XSD_DIR = BASE_DIR / "src" / "xsd"
    REPORTS_DIR = BASE_DIR / "reports"
    LOGS_DIR = BASE_DIR / "reports" / "logs"
    SQL_DIR = BASE_DIR / "src" / "sql"
    
    MSSQL_CONN_STR = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.26.56.7;DATABASE=nsi;UID=EVO_Admin;PWD=Dfyznrf_070106"

    NSI_ZIP_PATTERN = r"^NSI(\d{4})(\d{1,3})\.zip$"
    XML_FILE_PATTERN = r"^([A-Za-z0-9]{4})(\d{4})\.xml$"
    DBF_FILE_PATTERN = r"^([A-Za-z0-9]{3,6})(\d{4})\.dbf$"
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