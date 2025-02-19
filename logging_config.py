# logging_config.py

import logging
import sys

def setup_logger():
    """
    Crea e configura un logger basico che scrive messaggi sullo schermo (console).
    Puoi anche aggiungere un file di log, se vuoi.
    """
    # 1. Creiamo un logger con un nome a tua scelta
    logger = logging.getLogger("fatture_logger")
    # 2. Impostiamo il livello di log
    logger.setLevel(logging.DEBUG)  # mostra TUTTI i messaggi (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    # 3. Definiamo il formato: data, livello, file, linea, messaggio
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 4. Creiamo un Handler per scrivere su console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 5. (Opzionale) Se vuoi log su file, scommenta queste righe:
    # file_handler = logging.FileHandler("fatture.log", encoding='utf-8')
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    return logger
