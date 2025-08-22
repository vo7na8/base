import csv
import re
import logging
from pathlib import Path
from collections import deque
import xml.etree.ElementTree as ET
from config import Config
from utils import setup_logger, validate_filename

logger = setup_logger(__name__)

def find_xsd(xml_filename):
    """Находит соответствующий XSD файл"""
    if not validate_filename(xml_filename, Config.XML_FILE_PATTERN):
        logger.error(f"Invalid XML filename: {xml_filename}")
        return None
    return Config.XSD_DIR / f"{xml_filename[:4].lower()}.xsd"

# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============

def get_namespaces(xml_root):
    """Извлекает пространства имён из корня XML (если нужно где-то ещё)."""
    return {k.split('}')[-1]: v for k, v in xml_root.attrib.items() if k.startswith('xmlns:')}


def find_child_ignore_case(element, tag):
    """Поиск дочернего элемента по localname без учёта регистра."""
    if element is None:
        return None
    tgt = tag.lower()
    for child in element:
        localname = child.tag.split('}')[-1].lower()
        if localname == tgt:
            return child
    return None


def iter_elements_ignore_case(root, tag):
    """Итерирует элементы с данным localname без учёта регистра (аналог .//tag)."""
    tgt = tag.lower()
    for elem in root.iter():
        localname = elem.tag.split('}')[-1].lower()
        if localname == tgt:
            yield elem


# ============== XSD-ПАРСИНГ С НОРМАЛИЗАЦИЕЙ РЕГИСТРА ==============

def parse_xsd_schema(xsd_path):
    """Возвращает (root_name, target_element, columns) в НИЖНЕМ регистре.
    Колонки собираются через '-', т.к. '_' встречается в названиях самих полей.
    """
    try:
        tree = ET.parse(xsd_path)
        root = tree.getroot()
        ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

        # Корневой элемент XSD
        root_element = root.find(".//xs:element", ns)
        root_name = root_element.get("name") if root_element is not None else None
        root_name = root_name.lower() if root_name else None

        # Целевой элемент (первый с maxOccurs="unbounded")
        target_elements = [elem.get("name") for elem in root.findall(".//xs:element[@maxOccurs='unbounded']", ns)]
        if not target_elements:
            return None, None, None

        target_element_original = target_elements[0]
        target_element = target_element_original.lower()
        target_node = root.find(f".//xs:element[@name='{target_element_original}']", ns)

        # Рекурсивный сбор листовых колонок
        from collections import deque
        columns = []
        queue = deque([(target_node, [])])

        while queue:
            current_element, current_path = queue.popleft()
            complex_type = current_element.find(".//xs:complexType", ns)
            if complex_type is not None:
                sequence = complex_type.find(".//xs:sequence", ns)
                if sequence is not None:
                    for elem in sequence.findall("xs:element", ns):
                        name = elem.get("name")
                        if not name:
                            continue
                        new_path = current_path + [name]
                        if elem.find(".//xs:complexType", ns) is not None:
                            queue.append((elem, new_path))
                        else:
                            # ВНИМАНИЕ: используем '-' как разделитель и приводим к lower
                            columns.append("-".join(new_path).lower())

        return root_name, target_element, columns

    except Exception as e:
        logger.error(f"XSD parse error: {str(e)}")
        return None, None, None

# ============== ОСНОВНАЯ ОБРАБОТКА XML → CSV ==============

def process_xml(xml_path, xsd_path):
    """Обработка XML с CSV-выводом и логированием проблем по одному разу на колонку.
    - Имя корня, target_element и колонки приводятся к нижнему регистру.
    - Поиск элементов (записей и полей) — без учёта регистра по localname.
    - Пути колонок разделены через '-'.
    """
    try:
        match = re.fullmatch(Config.XML_FILE_PATTERN, xml_path.name, re.IGNORECASE)
        base_name = match.group(1).lower()

        xml_filename = xml_path.name
        tree = ET.parse(xml_path)
        xml_root = tree.getroot()

        root_name, target_element, columns = parse_xsd_schema(xsd_path)
        if not all([root_name, target_element, columns]):
            logger.error(f"Invalid XSD structure: {xsd_path.name}")
            return False

        # Нормализуем в нижний регистр для надёжности
        root_name_l = root_name.lower()
        target_element_l = target_element.lower()
        columns_l = [c.lower() for c in columns]

        # Проверка корня без учёта регистра (по localname)
        actual_root_local = xml_root.tag.split('}')[-1].lower()
        if actual_root_local != root_name_l:
            logger.error(
                f"Root element mismatch (case-insensitive). {xml_filename} -> Expected(localname): {root_name_l}, Actual: {actual_root_local}"
            )
            return False

        # CSV-файл
        csv_filename = f"{base_name}.csv"
        csv_path = Config.CSV_DIR / csv_filename

        reported_issues = set()  # (xml_filename, column)

        with csv_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(columns_l)  # заголовки в нижнем регистре

            # Ищем записи по localname без учёта регистра
            for row_index, record in enumerate(iter_elements_ignore_case(xml_root, target_element_l)):
                row = []
                for col in columns_l:
                    parts = col.split('-')  # важный разделитель: '-'
                    element = record
                    value = ""
                    issue = None

                    try:
                        for part in parts:
                            element = find_child_ignore_case(element, part)
                            if element is None:
                                issue = f"NOT_FOUND: {part}"
                                break

                        if element is not None and element.text and element.text.strip():
                            value = element.text.strip()
                        #else:
                        #    if issue is None:
                        #        issue = "EMPTY"
                    except Exception as e:
                        issue = f"ERROR: {e.__class__.__name__}"

                    if issue and (xml_filename, col) not in reported_issues:
                        logger.warning(
                            f"File={xml_filename}, Column={col}, First occurrence at Row={row_index}, Issue={issue}"
                        )
                        reported_issues.add((xml_filename, col))

                    row.append(value)

                writer.writerow(row)

        logger.info(f"Converted: {xml_filename} -> {csv_filename}")
        return True

    except Exception as e:
        logger.error(f"XML processing failed: {xml_filename} -> {str(e)}", exc_info=True)
        return False



def main():
    for xml_path in Config.XML_DIR.glob("*.xml"):
        if xsd_path := find_xsd(xml_path.name):
            if xsd_path.exists():
                process_xml(xml_path, xsd_path)
            else:
                logger.warning(f"XSD not found: {xsd_path.name}")
        else:
            logger.warning(f"Skipping invalid XML file: {xml_path.name}")

if __name__ == "__main__":
    main()