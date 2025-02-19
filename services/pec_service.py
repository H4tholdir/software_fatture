# services/pec_service.py

import os
import ssl
from imapclient import IMAPClient
import email
from dotenv import load_dotenv

load_dotenv()

PEC_SERVER = os.getenv("PEC_SERVER")
PEC_USER = os.getenv("PEC_USER")
PEC_PASSWORD = os.getenv("PEC_PASSWORD")

def scarica_allegati_xml(cartella_destinazione="fatture_temp", logger=None):
    if logger:
        logger.info(f"Inizio scaricamento allegati in: {cartella_destinazione}")
        logger.debug(f"Connetto a IMAP: {PEC_SERVER}, utente: {PEC_USER}")

    if not os.path.exists(cartella_destinazione):
        os.makedirs(cartella_destinazione)

    # Crea un contesto SSL che non verifica il certificato (INSICURO!)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with IMAPClient(PEC_SERVER, ssl_context=context) as client:
        client.login(PEC_USER, PEC_PASSWORD)
        
        client.select_folder('INBOX')
        messages = client.search(['UNSEEN'])

        if logger:
            logger.info(f"Trovati {len(messages)} messaggi NON LETTI.")

        for msg_id in messages:
            response = client.fetch(msg_id, ['RFC822'])
            msg = email.message_from_bytes(response[msg_id][b'RFC822'])

            for part in msg.walk():
                filename = part.get_filename()
                if filename and filename.lower().endswith(".xml"):
                    filepath = os.path.join(cartella_destinazione, filename)
                    if logger:
                        logger.info(f"Scarico allegato XML: {filename}")
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

            # Segna il messaggio come letto
            client.set_flags(msg_id, [r'\Seen'])  # ⬅ Ora è correttamente indentato!

        client.logout()

    if logger:
        logger.info("Download da PEC completato con successo.")
    return True
