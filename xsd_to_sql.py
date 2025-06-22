#xml_to_sql.py
import logging
from pathlib import Path
from collections import deque
import xml.etree.ElementTree as ET
from config import Config
from utils import setup_logger

logger = setup_logger(__name__)

# Соответствие типов XSD и SQL Server
XSD_TO_SQL_TYPE = {
    'xs:string': 'NVARCHAR(MAX)',
    'xs:integer': 'INT',
    'xs:int': 'INT',
    'xs:long': 'BIGINT',
    'xs:decimal': 'DECIMAL(18,2)',
    'xs:double': 'FLOAT',
    'xs:date': 'DATE',
    'xs:dateTime': 'DATETIME2',
    'xs:boolean': 'BIT',
    'xs:base64Binary': 'VARBINARY(MAX)',
}

def get_element_type(elem, ns):
    """Определяет тип элемента XSD с учетом вложенных simpleType."""
    if 'type' in elem.attrib:
        return elem.attrib['type']
    
    # Поиск вложенного simpleType
    simple_type = elem.find(".//xs:simpleType", ns)
    if simple_type is not None:
        restriction = simple_type.find(".//xs:restriction", ns)
        if restriction is not None and 'base' in restriction.attrib:
            return restriction.attrib['base']
    
    return 'xs:string'  # Тип по умолчанию

def parse_xsd_schema(xsd_path):
    """Парсит XSD и возвращает структуру для SQL таблицы."""
    try:
        tree = ET.parse(xsd_path)
        root = tree.getroot()
        ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

        # Поиск корневого элемента
        root_element = root.find(".//xs:element", ns)
        root_name = root_element.get("name") if root_element else None

        # Поиск элементов с maxOccurs="unbounded"
        target_elements = [
            elem.get("name")
            for elem in root.findall(".//xs:element[@maxOccurs='unbounded']", ns)
        ]
        if not target_elements:
            return None, None, None
        target_element = target_elements[0]

        # Сбор структуры с типами данных
        columns = []
        queue = deque([(root.find(f".//xs:element[@name='{target_element}']", ns), [])])

        while queue:
            current_elem, current_path = queue.popleft()
            complex_type = current_elem.find(".//xs:complexType", ns)
            if complex_type is None:
                continue

            sequence = complex_type.find(".//xs:sequence", ns)
            if sequence is None:
                continue

            for elem in sequence.findall("xs:element", ns):
                name = elem.get("name")
                new_path = current_path + [name]
                
                # Обработка комплексных элементов
                if elem.find(".//xs:complexType", ns) is not None:
                    queue.append((elem, new_path))
                else:
                    elem_type = get_element_type(elem, ns)
                    full_path = "/".join(new_path)
                    columns.append((full_path, elem_type))

        return root_name, target_element, columns

    except Exception as e:
        logger.error(f"XSD parse error: {str(e)}", exc_info=True)
        return None, None, None

def map_xsd_to_sql_type(xsd_type):
    """Преобразует тип XSD в тип SQL Server."""
    return XSD_TO_SQL_TYPE.get(xsd_type, 'NVARCHAR(MAX)')

def generate_sql_schema(xsd_path, sql_path):
    """Генерирует SQL скрипт создания таблицы."""
    _, target_element, columns = parse_xsd_schema(xsd_path)
    if not target_element or not columns:
        logger.error(f"Не удалось извлечь структуру из XSD: {xsd_path.name}")
        return False

    # Формирование SQL колонок
    sql_columns = []
    for path, xsd_type in columns:
        col_name = path.replace('/', '_')
        sql_type = map_xsd_to_sql_type(xsd_type)
        sql_columns.append(f"[{col_name}] {sql_type}")

    # 2. Добавляем новые колонки периода (всегда после оригинальных)
    sql_columns.append("[OT_PER_Y] NVARCHAR(2)")  # Год периода
    sql_columns.append("[OT_PER_M] NVARCHAR(2)")  # Месяц периода
    sql_columns.append("[OT_PER_N] NVARCHAR(4)")  # Номер пакета загрузки

    # Генерация CREATE TABLE
    table_name = target_element
    sql_statement = (
        f"CREATE TABLE [{table_name}] (\n"
        "    " + ",\n    ".join(sql_columns) + "\n"
        ");"
    )

    # Сохранение в файл
    with sql_path.open('w', encoding='utf-8') as sql_file:
        sql_file.write(sql_statement)
    
    logger.info(f"Сгенерирован SQL: {sql_path.name}")
    return True

def main_sql():
    """Обрабатывает все XSD файлы в директории."""
    Config.SQL_DIR.mkdir(exist_ok=True, parents=True)
    
    for xsd_path in Config.XSD_DIR.glob("*.xsd"):
        sql_filename = f"{xsd_path.stem}.sql"
        sql_path = Config.SQL_DIR / sql_filename
        generate_sql_schema(xsd_path, sql_path)

if __name__ == "__main__":
    main_sql()