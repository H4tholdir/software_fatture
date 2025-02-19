# services/notifications.py

from datetime import date, timedelta
from database.db_session import SessionLocal
from database.models import Fattura

def check_scadenze_imminenti(giorni_avviso=7):
    """
    Ritorna due liste:
    - scadute: Fatture con data_scadenza < oggi e non pagate
    - imminenti: Fatture con data_scadenza entro X giorni e non pagate
    """
    db = SessionLocal()
    oggi = date.today()
    limite = oggi + timedelta(days=giorni_avviso)

    scadute = db.query(Fattura).filter(
        Fattura.pagata == False,
        Fattura.data_scadenza != None,
        Fattura.data_scadenza < oggi
    ).all()

    imminenti = db.query(Fattura).filter(
        Fattura.pagata == False,
        Fattura.data_scadenza != None,
        Fattura.data_scadenza >= oggi,
        Fattura.data_scadenza <= limite
    ).all()

    db.close()
    return scadute, imminenti
