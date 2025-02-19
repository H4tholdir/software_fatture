import os
import ssl
from imapclient import IMAPClient
from dotenv import load_dotenv

load_dotenv()

PEC_SERVER = os.getenv("PEC_SERVER")
PEC_USER = os.getenv("PEC_USER")
PEC_PASSWORD = os.getenv("PEC_PASSWORD")

def test_list_folders():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with IMAPClient(PEC_SERVER, ssl_context=context) as client:
        client.login(PEC_USER, PEC_PASSWORD)
        # Proviamo a vedere le capabilities
        print("Capabilities:", client.capabilities)

        # Ora list_folders
        folders = client.list_folders()
        print("Cartelle trovate (list_folders):", folders)

        # Se arrivi qui senza errori, dovrebbe stamparti una lista di tuple
        # Esempio: [('\\HasNoChildren', '/', 'INBOX'), ...]

if __name__ == "__main__":
    test_list_folders()
