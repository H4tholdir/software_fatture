# tests/test_dropbox_service.py
import pytest
from unittest.mock import patch, MagicMock
from services.dropbox_service import upload_xml_to_dropbox

@patch("services.dropbox_service.dbx")
def test_upload_xml_to_dropbox(mock_dbx, tmp_path):
    """
    Verifica che upload_xml_to_dropbox chiami correttamente l'API di Dropbox.
    """
    # Creiamo un file finto
    fake_xml = "<Fattura>Test</Fattura>"
    xml_file = tmp_path / "fattura.xml"
    xml_file.write_text(fake_xml, encoding="utf-8")

    # Simuliamo i parametri
    fornitore = "FornitoreTest"
    import datetime
    data_fattura = datetime.date(2023, 3, 1)
    numero_fattura = "FT-2023-001"

    # Chiamiamo la funzione
    path_caricato = upload_xml_to_dropbox(str(xml_file), fornitore, data_fattura, numero_fattura)
    # Verifichiamo che sia tornato un path
    assert "/fatture/2023/03/FornitoreTest/2023-03-01_FT-2023-001.xml" in path_caricato

    # Controlliamo che il mock abbia chiamato dbx.files_upload
    mock_dbx.files_upload.assert_called_once()
