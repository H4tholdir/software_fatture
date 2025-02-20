# tests/test_db_session.py

import pytest
from database.db_session import init_db, SessionLocal
from database.models import Fattura

@pytest.fixture(scope="module")
def setup_test_db():
    """
    Fixture che inizializza il DB in memoria (in SQLite) per i test.
    """
    init_db()  # Crea le tabelle (percorso di default: fatture.db)
    yield
    # Teoricamente potresti cancellare il file DB qui, se preferisci pulire.

def test_inserisci_fattura(setup_test_db):
    """
    Testa l'inserimento di una fattura nel DB.
    """
    db = SessionLocal()
    nuova_fattura = Fattura(numero="TST-001", totale=123.45)
    db.add(nuova_fattura)
    db.commit()

    # Verifichiamo se esiste
    fatture = db.query(Fattura).all()
    assert len(fatture) == 1
    assert fatture[0].numero == "TST-001"
    db.close()
