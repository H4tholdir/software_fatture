# services/dropbox_service.py

import os
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode, FileMetadata
from dotenv import load_dotenv

# Carichiamo le variabili d'ambiente dal file .env
load_dotenv()

# Leggiamo i dati necessari per l'OAuth con refresh token
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Creiamo l'istanza "globale" di Dropbox con i parametri OAuth (refresh token)
dbx = dropbox.Dropbox(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    oauth2_refresh_token=REFRESH_TOKEN
)

def upload_xml_to_dropbox(local_path, fornitore, data_fattura, numero_fattura, logger=None):
    """
    Carica il file XML su Dropbox, nella cartella:
      /fatture/anno/mese/fornitore/datafattura_numerofattura.xml
    """
    # Prepara i componenti del path su Dropbox
    anno = data_fattura.year
    mese = str(data_fattura.month).zfill(2)
    fornitore_sanitizzato = fornitore.replace(" ", "_")

    filename = f"{data_fattura}_{numero_fattura}.xml"
    dropbox_path = f"/fatture/{anno}/{mese}/{fornitore_sanitizzato}/{filename}"

    # Controlliamo se esiste già
    try:
        dbx.files_get_metadata(dropbox_path)
        if logger:
            logger.info(f"Fattura '{dropbox_path}' già presente in Dropbox. Skip upload.")
        return dropbox_path
    except ApiError:
        pass  # Se non esiste, prosegui con l'upload

    # Se non esiste, procediamo all'upload
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))

    if logger:
        logger.info(f"Fattura caricata su Dropbox: {dropbox_path}")

    return dropbox_path


# 🔹 NUOVA FUNZIONE: Scaricare tutti gli XML direttamente in memoria con gestione degli encoding
def scarica_tutti_xml_memoria(logger=None):
    """
    Scarica **tutte** le fatture XML da Dropbox in memoria con gestione della paginazione.
    Se un file non è in UTF-8, tenta altre codifiche senza interrompere il processo.
    Ritorna un dizionario {nome_file: contenuto_xml}
    """
    dropbox_root = "/fatture"
    xml_files = {}
    has_more = True
    cursor = None
    total_files = 0

    try:
        logger.info("📡 Inizio download XML da Dropbox in memoria...")

        while has_more:
            if cursor:
                response = dbx.files_list_folder_continue(cursor)
            else:
                response = dbx.files_list_folder(dropbox_root, recursive=True)

            # Processa i file XML
            for entry in response.entries:
                if isinstance(entry, FileMetadata) and entry.name.endswith(".xml"):
                    try:
                        _, res = dbx.files_download(entry.path_lower)
                        file_content = res.content  # Legge i byte grezzi

                        # 🔹 Tenta la decodifica con UTF-8
                        try:
                            xml_text = file_content.decode("utf-8")
                        except UnicodeDecodeError:
                            logger.warning(f"⚠️ File {entry.name} non in UTF-8, provo ISO-8859-1...")
                            try:
                                xml_text = file_content.decode("ISO-8859-1")
                            except UnicodeDecodeError:
                                logger.warning(f"⚠️ File {entry.name} non leggibile, provo cp1252...")
                                try:
                                    xml_text = file_content.decode("cp1252")
                                except UnicodeDecodeError:
                                    logger.error(f"❌ File {entry.name} NON DECODIFICABILE. Saltato.")
                                    continue  # Salta il file e passa al successivo

                        # Se la decodifica è riuscita, aggiungi al dizionario
                        xml_files[entry.name] = xml_text
                        total_files += 1

                    except Exception as e:
                        logger.error(f"❌ Errore nel download di {entry.name}: {e}")

            # Aggiorna il cursore e verifica se ci sono altre pagine
            cursor = response.cursor
            has_more = response.has_more
            logger.info(f"🔄 Scaricati finora: {total_files} file XML...")

        logger.info(f"📦 Totale file XML scaricati: {total_files}")
        return xml_files

    except ApiError as e:
        logger.error(f"❌ Errore API Dropbox: {e}")
        return {}


def conta_fatture_su_dropbox(logger=None):
    """
    Conta tutti i file XML presenti nella cartella /fatture di Dropbox.
    """
    dropbox_root = "/fatture"
    file_count = 0
    has_more = True
    cursor = None

    try:
        logger.info("📡 Inizio conteggio delle fatture su Dropbox...")

        while has_more:
            if cursor:
                results = dbx.files_list_folder_continue(cursor)
            else:
                results = dbx.files_list_folder(dropbox_root, recursive=True)

            for entry in results.entries:
                if isinstance(entry, FileMetadata) and entry.name.endswith(".xml"):
                    file_count += 1

            cursor = results.cursor
            has_more = results.has_more  # Se ci sono altri file, continua

        logger.info(f"🔍 Fatture trovate su Dropbox: {file_count}")
        return file_count

    except Exception as e:
        logger.error(f"❌ Errore nel conteggio delle fatture: {e}")
        return 0
