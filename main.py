# main.py

import sys
from PySide6.QtWidgets import QApplication
import logging

# Import DB
from database.db_session import init_db, SessionLocal
from database.models import Fattura

# Import della MainWindow
from ui.main_window import MainWindow

# Import dei servizi
from logging_config import setup_logger
from services.dropbox_service import scarica_tutti_xml_memoria
from services.parser_fatture import parse_fattura_xml, salva_fattura_su_db

# Configura log dettagliato per gli errori di parsing
PARSING_ERROR_LOG = "logs/parsing_errors.log"


def main():
    # 1) Inizializza il logger
    logger = setup_logger()
    logger.info("🚀 Avvio dell'applicazione Gestione Fatture...")

    # 2) Inizializza il DB
    init_db()
    logger.info("✅ Database inizializzato (o già esistente).")

    # 3) Controllo se il DB è vuoto
    db = SessionLocal()
    count_f = db.query(Fattura).count()
    db.close()

    if count_f == 0:
        logger.warning("⚠️ DB vuoto, avvio resync rapido da Dropbox...")
        resync_from_dropbox_memoria(logger)

    # 4) Avvio l'app PySide6
    app = QApplication(sys.argv)
    window = MainWindow(logger)
    window.show()

    # 5) Avvio il loop dell’app
    logger.info("🎨 Interfaccia grafica avviata.")
    sys.exit(app.exec())


def resync_from_dropbox_memoria(logger):
    """
    Scarica tutte le fatture XML da Dropbox **direttamente in memoria**
    ed esegue il parsing senza scrivere su disco.
    """
    logger.info("📡 Inizio resync rapido da Dropbox...")

    # Scarica tutti gli XML direttamente in memoria
    xml_dict = scarica_tutti_xml_memoria(logger)

    if not xml_dict:
        logger.warning("⚠️ Nessun file XML trovato su Dropbox!")
        return

    logger.info(f"📄 {len(xml_dict)} file XML ricevuti, avvio il parsing...")

    errori = []

    for i, (filename, xml_content) in enumerate(xml_dict.items(), 1):
        logger.info(f"🔍 [{i}/{len(xml_dict)}] Parsing file: {filename}")

        try:
            # Parsing dell'XML direttamente in memoria
            fattura_obj = parse_fattura_xml(xml_content, is_memory=True)

            if fattura_obj:
                salva_fattura_su_db(fattura_obj)
                logger.info(f"✅ Fattura {fattura_obj.numero} importata nel database.")
            else:
                error_message = f"⚠️ Problema nel parsing del file: {filename}"
                logger.warning(error_message)
                errori.append(error_message)

        except Exception as e:
            error_message = f"❌ Errore nel parsing di {filename}: {e}"
            logger.error(error_message)
            errori.append(error_message)

    # Salvataggio degli errori in un file di log dettagliato
    if errori:
        with open(PARSING_ERROR_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(errori))
        logger.error(f"❌ Parsing completato con errori. Dettagli salvati in {PARSING_ERROR_LOG}")
    else:
        logger.info("✅ Resync rapido COMPLETATO senza errori!")


if __name__ == "__main__":
    main()
