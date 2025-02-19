import os
import hashlib
import subprocess
import tempfile
import logging
from datetime import datetime
from lxml import etree

from database.db_session import SessionLocal
from database.models import (
    Fattura,
    RigheFattura,
    DatiRiepilogoIVA,
    DatiPagamento,
    AllegatoFattura,
)

# Configurazione logger
logger = logging.getLogger("fatture_parser")
file_handler = logging.FileHandler("errori_fatture.log")
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def calcola_hash_xml(xml_content):
    """
    Calcola l'hash SHA-256 di un file XML (o XML in memoria).
    """
    return hashlib.sha256(xml_content.encode("utf-8")).hexdigest()

def decode_p7m_to_xml(p7m_content):
    """
    Decodifica un file .p7m contenuto in memoria usando OpenSSL.
    Ritorna l'XML decodificato come stringa.
    """
    try:
        result = subprocess.run(
            ["openssl", "smime", "-verify", "-noverify", "-inform", "DER"],
            input=p7m_content,
            capture_output=True,
            check=True
        )
        return result.stdout.decode("utf-8")  # Ritorna XML come stringa
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore nella decodifica del p7m: {e.stderr}")
        return None

def leggi_file_con_fallback(xml_path):
    """
    Prova a leggere il file con diversi encoding.
    """
    encodings = ["utf-8", "latin-1", "windows-1252"]

    with open(xml_path, "rb") as f:
        raw_bytes = f.read()

    for enc in encodings:
        try:
            return raw_bytes.decode(enc), enc
        except UnicodeDecodeError:
            continue

    logger.error(f"❌ Errore lettura file {xml_path}: impossibile decodificare con {encodings}")
    return None, None

def parse_fattura_xml(xml_source, is_memory=False):
    """
    Parser completo del tracciato FatturaPA con gestione degli encoding.
    """
    if not is_memory:
        ext = os.path.splitext(xml_source)[1].lower()
        
        if ext == ".p7m":
            with open(xml_source, "rb") as f:
                xml_content = decode_p7m_to_xml(f.read())
            if not xml_content:
                logger.error(f"Impossibile decodificare il p7m: {xml_source}")
                return None
        else:
            xml_content, encoding_usato = leggi_file_con_fallback(xml_source)
            if not xml_content:
                logger.error(f"Errore lettura file {xml_source}")
                return None
    else:
        xml_content = xml_source

    hash_val = calcola_hash_xml(xml_content)
    
    try:
        tree = etree.fromstring(xml_content.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        logger.error(f"XML corrotto ({xml_source}): {e}")
        return None

    fattura_obj = Fattura()
    fattura_obj.hash_xml = hash_val
    fattura_obj.xml_raw = xml_content  
    
    numero = tree.xpath("//*[local-name()='Numero']/text()")
    if numero:
        fattura_obj.numero = numero[0]

    data = tree.xpath("//*[local-name()='Data']/text()")
    if data:
        fattura_obj.data = datetime.strptime(data[0], "%Y-%m-%d").date()
    
    fornitore = tree.xpath("//*[local-name()='CedentePrestatore']/*[local-name()='DatiAnagrafici']/*[local-name()='Anagrafica']/*[local-name()='Denominazione']/text()")
    if fornitore:
        fattura_obj.fornitore = fornitore[0]
    
    totale = tree.xpath("//*[local-name()='ImportoTotaleDocumento']/text()")
    if totale:
        fattura_obj.totale = float(totale[0])
    
    linee_nodes = tree.xpath("//*[local-name()='DettaglioLinee']")
    righe_list = []

    for ln in linee_nodes:
        r = RigheFattura()

        descr = ln.xpath("./*[local-name()='Descrizione']/text()")
        r.descrizione = descr[0] if descr else "N/D"

        qty = ln.xpath("./*[local-name()='Quantita']/text()")
        r.quantita = float(qty[0]) if qty else 1.0

        pu = ln.xpath("./*[local-name()='PrezzoUnitario']/text()")
        r.prezzo_unitario = float(pu[0]) if pu else 0.0

        pt = ln.xpath("./*[local-name()='PrezzoTotale']/text()")
        if pt:
            r.importo_riga = float(pt[0])

        righe_list.append(r)

    fattura_obj.righe = righe_list

    rieps = tree.xpath("//*[local-name()='DatiRiepilogo']")
    for rr in rieps:
        dr = DatiRiepilogoIVA()

        aliq = rr.xpath("./*[local-name()='AliquotaIVA']/text()")
        if aliq:
            dr.aliquota_iva = float(aliq[0])

        imp = rr.xpath("./*[local-name()='ImponibileImporto']/text()")
        if imp:
            dr.imponibile_importo = float(imp[0])

        fattura_obj.riepiloghi_iva.append(dr)

    return fattura_obj

def salva_fattura_su_db(fattura_obj):
    """
    Salva l'oggetto Fattura nel DB, controllando i duplicati con hash_xml.
    """
    if not fattura_obj:
        logger.error("Fattura_obj is None, skip saving.")
        return None

    db = SessionLocal()
    existing = db.query(Fattura).filter_by(hash_xml=fattura_obj.hash_xml).first()

    if existing:
        logger.info(f"Fattura con hash {fattura_obj.hash_xml} già in DB, skip.")
        db.close()
        return existing

    db.add(fattura_obj)
    db.commit()
    db.refresh(fattura_obj)
    db.close()

    return fattura_obj
