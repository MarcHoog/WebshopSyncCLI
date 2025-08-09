from typing import Dict, Any
import xml.etree.ElementTree as ET

def perfion_resp_to_dict(soap_response: str) -> Dict[str, Any]:
    """
    Returns a dictionary version of the perfion responds
    """
    root = ET.fromstring(soap_response)
    ns = {'soap': 'http://www.w3.org/2003/05/soap-envelope'}
    result_elem = root.find('.//soap:Body//{http://perfion.com/}ExecuteQueryResult', ns)

    if result_elem is None or not result_elem.text:
        raise ValueError("No ExecuteQueryResult content found")

    inner_root = ET.fromstring(result_elem.text)

    total_count = inner_root.get("totalCount")
    if not total_count:
        raise ValueError("Total Count is expected to exist as attribute in data")

    products = []
    for product in inner_root.findall('./Product'):
        products.append({
            'id': product.attrib.get('id'),
            **{child.tag: child.text for child in product}
        })

    return {
        "totalCount": int(total_count),
        "products": products
    }
