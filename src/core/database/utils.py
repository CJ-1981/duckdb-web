import duckdb
import logging

logger = logging.getLogger(__name__)

def register_xml_udfs(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Register XML processing UDFs in DuckDB.
    
    @MX:ANCHOR: XML UDF registration entry point (fan_in: workflow worker, workflows API)
    @MX:REASON: Two-tier strategy (official extension -> lxml) must remain consistent across callers.

    Tries to load official 'xml' extension first. 
    Falls back to lxml-based UDFs if extension loading fails.
    
    Provides:
    - xpath_string(xml, xpath): Returns string value of first match
    - xpath(xml, xpath): Returns list of string values of matches (JSON array)
    - xml_extract_string: Alias for xpath_string
    - xml_extract: Alias for xpath
    """
    try:
        # Try official extension first
        conn.execute("INSTALL xml; LOAD xml;")
        return
    except Exception:
        pass

    # Fallback to lxml UDFs
    try:
        from lxml import etree
        from typing import Optional, List

        def xpath_string(xml_text: str, xpath_expr: str) -> Optional[str]:
            if not xml_text or not xpath_expr:
                return None
            try:
                if isinstance(xml_text, str):
                    xml_bytes = xml_text.encode('utf-8')
                else:
                    xml_bytes = xml_text
                
                parser = etree.XMLParser(recover=True, no_network=True)
                root = etree.fromstring(xml_bytes, parser=parser)
                if root is None:
                    return None
                
                results = root.xpath(xpath_expr)
                if not results:
                    return None
                
                result = results[0]
                if hasattr(result, 'text'):
                    if result.text is not None:
                        return result.text
                    return str(result)
                return str(result)
            except Exception:
                return None

        def xpath(xml_text: str, xpath_expr: str) -> List[str]:
            if not xml_text or not xpath_expr:
                return []
            try:
                if isinstance(xml_text, str):
                    xml_bytes = xml_text.encode('utf-8')
                else:
                    xml_bytes = xml_text
                parser = etree.XMLParser(recover=True, no_network=True)
                root = etree.fromstring(xml_bytes, parser=parser)
                if root is None:
                    return []
                
                results = root.xpath(xpath_expr)
                output = []
                for res in results:
                    if hasattr(res, 'text'):
                        if res.text is not None:
                            output.append(res.text)
                        else:
                            output.append(str(res))
                    else:
                        output.append(str(res))
                return output
            except Exception:
                return []

        # Register functions
        conn.create_function("xpath_string", xpath_string, ['VARCHAR', 'VARCHAR'], 'VARCHAR', null_handling='special')
        conn.create_function("xml_extract_string", xpath_string, ['VARCHAR', 'VARCHAR'], 'VARCHAR', null_handling='special')
        conn.create_function("xpath", xpath, ['VARCHAR', 'VARCHAR'], 'VARCHAR[]', null_handling='special')
        conn.create_function("xpath_list", xpath, ['VARCHAR', 'VARCHAR'], 'VARCHAR[]', null_handling='special')
        conn.create_function("xml_extract", xpath, ['VARCHAR', 'VARCHAR'], 'VARCHAR[]', null_handling='special')


        
    except ImportError as e:
        logger.warning(f"lxml not found, xpath_string UDF will not be available. Error: {e}")
    except Exception as e:
        logger.error(f"Failed to register XML UDFs: {e}")

def load_xml_into_table(conn: duckdb.DuckDBPyConnection, file_path: str, table_name: str) -> None:
    """
    Load XML file content into a DuckDB table with a single 'xml_data' column.
    
    @MX:ANCHOR: XML data loading strategy (fan_in: worker.py, workflows.py)
    @MX:REASON: Centralizes single-row DataFrame registration to ensure consistent table schema.
    """
    import pandas as pd
    import os
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"XML file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        xml_content = f.read()
    
    df = pd.DataFrame([{"xml_data": xml_content}])
    conn.register(f'{table_name}_df', df)
    # Use TEMP TABLE for consistency with workflows.py if needed, 
    # but load_xml_into_table was described as CREATE OR REPLACE TABLE.
    # workflows.py uses CREATE OR REPLACE TEMP TABLE. 
    # I will use TEMP TABLE to be safe and consistent with typical node execution.
    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {table_name}_df")
    logger.info(f">>> [DB UTILS] Loaded XML from {file_path} into table {table_name}")


