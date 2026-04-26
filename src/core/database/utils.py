import duckdb
import logging

logger = logging.getLogger(__name__)

def register_xml_udfs(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Register XML processing UDFs in DuckDB.
    
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

