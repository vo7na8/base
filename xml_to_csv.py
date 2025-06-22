# xml_to_csv.py
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

def get_namespaces(xml_root):
    """Извлекает пространства имен из корня XML"""
    return {k.split('}')[-1]: v for k, v in xml_root.attrib.items() if k.startswith('xmlns:')}

def parse_xsd_schema(xsd_path):
    """Восстановленная оригинальная логика парсинга XSD"""
    try:
        tree = ET.parse(xsd_path)
        root = tree.getroot()
        ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

        # Поиск корневого элемента
        root_element = root.find(".//xs:element", ns)
        root_name = root_element.get("name") if root_element else None

        # Находим все элементы с maxOccurs="unbounded"
        target_elements = [
            elem.get("name")
            for elem in root.findall(".//xs:element[@maxOccurs='unbounded']", ns)
        ]

        if not target_elements:
            return None, None, None

        # Берем первый подходящий элемент
        target_element = target_elements[0]
        target_node = root.find(f".//xs:element[@name='{target_element}']", ns)

        # Рекурсивный сбор структуры данных
        columns = []
        queue = deque([(target_node, [])])

        while queue:
            current_element, current_path = queue.popleft()
            complex_type = current_element.find(".//xs:complexType", ns)
            
            if complex_type:
                sequence = complex_type.find(".//xs:sequence", ns)
                if sequence:
                    for elem in sequence.findall("xs:element", ns):
                        name = elem.get("name")
                        new_path = current_path + [name]
                        
                        if elem.find(".//xs:complexType", ns):
                            queue.append((elem, new_path))
                        else:
                            columns.append("/".join(new_path))

        return root_name, target_element, columns

    except Exception as e:
        logger.error(f"XSD parse error: {str(e)}")
        return None, None, None

def process_xml(xml_path, xsd_path):
    """Оригинальная обработка XML"""
    try:
        
        match = re.fullmatch(Config.XML_FILE_PATTERN, xml_path.name, re.IGNORECASE)
        base_name = match.group(1).lower()
        
        xml_filename = xml_path.name
        tree = ET.parse(xml_path)
        xml_root = tree.getroot()

        # Получаем метаданные из XSD
        root_name, target_element, columns = parse_xsd_schema(xsd_path)
        if not all([root_name, target_element, columns]):
            logger.error(f"Invalid XSD structure: {xsd_path.name}")
            return False

        # Проверка корневого элемента
        namespaces = get_namespaces(xml_root)
        expected_root_tag = f"{{{namespaces.get('ns', '')}}}{root_name}" if 'ns' in namespaces else root_name
        
        if xml_root.tag != expected_root_tag:
            logger.error(f"Root element mismatch. Expected: {expected_root_tag}, Actual: {xml_root.tag}")
            return False

        # Создаем CSV файл
        csv_filename = f"{base_name}.csv"
        
        csv_path = Config.CSV_DIR / csv_filename
        
        with csv_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(columns)

            # Поиск целевых элементов с учетом namespace
            for record in xml_root.findall(f".//{target_element}", namespaces):
                row = []
                for col in columns:
                    parts = col.split('/')
                    element = record
                    value = ""
                    
                    try:
                        for part in parts:
                            element = element.find(part, namespaces)
                            if element is None:
                                break
                        
                        value = element.text.strip() if element is not None and element.text else ""
                    except AttributeError:
                        pass
                    
                    row.append(value)
                
                writer.writerow(row)

        logger.info(f"Converted: {xml_filename} -> {csv_filename}")
        return True

    except Exception as e:
        logger.error(f"XML processing failed: {str(e)}", exc_info=True)
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