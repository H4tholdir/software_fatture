# tests/test_pec_service.py
import pytest
from unittest.mock import patch, MagicMock
from services.pec_service import scarica_allegati_xml

@patch("services.pec_service.IMAPClient")
def test_scarica_allegati_xml(mock_imap_class, tmp_path):
    """
    Testa scarica_allegati_xml simulando la connessione IMAP:
    - Nessun errore
    - Creazione della cartella destinazione
    - Download di allegati XML finti
    """

    # Setup mock: finto messaggio con un allegato .xml
    mock_imap = MagicMock()
    mock_imap_class.return_value = mock_imap

    mock_imap.search.return_value = [1]  # un messaggio
    mock_fetch_data = {
        1: {b'RFC822': b"Content of the email in bytes"}
    }
    mock_imap.fetch.return_value = mock_fetch_data

    # Creiamo un finto email.message
    import email
    from email.message import EmailMessage
    msg = EmailMessage()
    msg.set_content("Finto contenuto test")
    msg.add_attachment(b"<xml>AllegatoTest</xml>", maintype='text', subtype='xml', filename="test.xml")
    # Converte a bytes
    msg_bytes = msg.as_bytes()

    # Ora, facciamo in modo che fetch(...) simuli il retrieve di msg_bytes
    def fetch_side_effect(msg_id, data):
        return {1: {b'RFC822': msg_bytes}}
    mock_imap.fetch.side_effect = fetch_side_effect

    # Eseguiamo la funzione
    output_dir = tmp_path / "pec_downloads"
    scarica_allegati_xml(str(output_dir))

    # Verifichiamo che esista il file test.xml
    files = list(output_dir.glob("*.xml"))
    assert len(files) == 1
    assert files[0].name == "test.xml"

    # Controlliamo che il mock abbia contrassegnato l'email come letta
    mock_imap.set_flags.assert_called()
