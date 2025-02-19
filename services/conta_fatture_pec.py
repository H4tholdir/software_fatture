import os
import ssl
from imapclient import IMAPClient
import email
from dotenv import load_dotenv

# Carichiamo le credenziali dal file .env
load_dotenv()
PEC_SERVER = os.getenv("PEC_SERVER")
PEC_USER = os.getenv("PEC_USER")
PEC_PASSWORD = os.getenv("PEC_PASSWORD")

def conta_fatture_su_pec(stampa_dettagli=False):
    """
    Conta le email nella PEC e verifica quanti allegati XML/P7M ci sono.
    - Esclude `daticert.xml` e `Segnatura.xml` dal conteggio.
    - Evita di contare duplicati `.xml` e `.p7m` nella stessa email.
    - Se `stampa_dettagli=True`, stampa i dettagli di ogni email con gli allegati trovati.
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  

    with IMAPClient(PEC_SERVER, ssl_context=context) as client:
        client.login(PEC_USER, PEC_PASSWORD)
        client.select_folder('INBOX')

        # Troviamo tutte le email
        messages = client.search(['ALL'])
        totale_email = len(messages)

        count_fatture = 0
        dettagli_email = []

        for msg_id in messages:
            response = client.fetch(msg_id, ['RFC822'])
            msg = email.message_from_bytes(response[msg_id][b'RFC822'])

            allegati_validi = []
            xml_trovato = None
            p7m_trovato = None

            for part in msg.walk():
                filename = part.get_filename()
                if filename:
                    filename = filename.lower()

                    # Escludiamo i file di certificazione della PEC
                    if filename in ["daticert.xml", "segnatura.xml"]:
                        continue

                    # Se è un XML/P7M, lo aggiungiamo alla lista
                    if filename.endswith(".xml"):
                        xml_trovato = filename
                    elif filename.endswith(".p7m"):
                        p7m_trovato = filename

            # Se c'è sia XML che P7M, contiamo solo una fattura
            if xml_trovato or p7m_trovato:
                count_fatture += 1
                allegati_validi = [xml_trovato, p7m_trovato]

            # Stampiamo dettagli solo se richiesto
            if stampa_dettagli and allegati_validi:
                dettagli_email.append(f"📩 Email ID {msg_id}: {', '.join(filter(None, allegati_validi))}")

        print(f"📩 Email totali nella PEC: {totale_email}")
        print(f"📬 Totale fatture XML/P7M reali trovate su PEC: {count_fatture}")

        if stampa_dettagli:
            print("\n🔍 Dettagli delle email con fatture XML/P7M:")
            for dettaglio in dettagli_email:
                print(dettaglio)

        return count_fatture
