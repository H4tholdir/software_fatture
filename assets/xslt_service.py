# services/xslt_service.py

import os
import lxml.etree as ET

def genera_html_da_xml(xml_string, xslt_path):
    """
    Applica il FoglioStile.xsl ufficiale di FatturaPA al contenuto XML
    e ritorna l'HTML generato.
    """
    # Convertiamo la stringa in un elemento
    xml_root = ET.fromstring(xml_string.encode("utf-8"))
    # Carichiamo lo XSLT
    xslt_tree = ET.parse(xslt_path)
    transform = ET.XSLT(xslt_tree)
    result = transform(xml_root)
    html_str = str(result)
    return html_str
