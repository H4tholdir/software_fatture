# tests/test_notifications.py
import pytest
import datetime
from database.db_session import init_db, SessionLocal
from database.models import Fattura
from services.notifications import check_scadenze_imminenti

@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

def test_check_scadenze_imminenti(db_session):
    # Puliamo eventuali fatture esistenti
    db_session.query(Fattura).delete()

    # Creiamo fatture, una scaduta, una imminente, una a lunga scadenza
    today = datetime.date.today()
    fatt_scaduta = Fattura(numero="SCAD1", data_scadenza=today - datetime.timedelta(days=1), pagata=False)
    fatt_imminente = Fattura(numero="IMM1", data_scadenza=today + datetime.timedelta(days=3), pagata=False)
    fatt_lontana = Fattura(numero="LONG1", data_scadenza=today + datetime.timedelta(days=30), pagata=False)
    db_session.add_all([fatt_scaduta, fatt_imminente, fatt_lontana])
    db_session.commit()

    scadute, imminenti = check_scadenze_imminenti(giorni_avviso=7)
    # scaduta deve stare in scadute
    assert len(scadute) == 1
    assert scadute[0].numero == "SCAD1"

    # fatt_imminente deve stare in imminenti
    assert len(imminenti) == 1
    assert imminenti[0].numero == "IMM1"
