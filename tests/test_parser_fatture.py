# tests/test_parser_fatture.py

import os
import pytest
from services.parser_fatture import parse_fattura_xml

def test_parse_fattura_xml_inexistent():
    """
    Se il file XML non esiste, parse_fattura_xml() dovrebbe restituire None o generare errore.
    """
    fattura = parse_fattura_xml("file_non_esistente.xml")
    assert fattura is None

def test_parse_fattura_xml_minimal(tmp_path):
    """
    Test con un semplice file XML minimale per verificare il parsing base.
    """
    # Creiamo un contenuto XML minimal (puoi arricchirlo con i tag reali di FatturaPA).
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<FatturaElettronica>
    <FatturaElettronicaBody>
        <DatiGenerali>
            <DatiGeneraliDocumento>
                <Numero>123</Numero>
                <Data>2023-01-15</Data>
                <ImportoTotaleDocumento>100.50</ImportoTotaleDocumento>
            </DatiGeneraliDocumento>
        </DatiGenerali>
        <DatiBeniServizi>
            <DettaglioLinee>
                <Descrizione>Servizio di prova</Descrizione>
                <Quantita>2.0</Quantita>
                <PrezzoUnitario>50.25</PrezzoUnitario>
                <PrezzoTotale>100.50</PrezzoTotale>
            </DettaglioLinee>
        </DatiBeniServizi>
    </FatturaElettronicaBody>
</FatturaElettronica>
"""

    # Scriviamo un file temporaneo in tmp_path (funzione di pytest).
    xml_file = tmp_path / "test_fattura.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    # Usiamo parse_fattura_xml
    fattura = parse_fattura_xml(str(xml_file))

    assert fattura is not None, "Il parsing non dovrebbe restituire None con XML valido"
    assert fattura.numero == "123"
    assert fattura.totale == 100.50
    assert len(fattura.righe) == 1
    assert fattura.righe[0].descrizione == "Servizio di prova"
