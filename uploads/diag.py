from dbfread import DBF
from pathlib import Path

DBF_FILE = Path("mdu0524.DBF")  # путь к вашему файлу

def find_illegal_logicals(dbf_path):
    # raw=True возвращает байты без конвертации
    dbf = DBF(dbf_path, raw=True, char_decode_errors='replace')  

    # имена логических полей
    logical_fields = [f.name for f in dbf.fields if f.type == 'L']
    print(f"Logical fields: {logical_fields}")

    for i, record in enumerate(dbf):
        for field in logical_fields:
            try:
                value = record[field]  # это уже байты
                if value not in (b'T', b'F', b' '):
                    print(f"Illegal logical value at row {i+1}, column '{field}': {value}")
            except Exception as e:
                print(f"Error reading row {i+1}, column '{field}': {e}")

if __name__ == "__main__":
    find_illegal_logicals(DBF_FILE)
