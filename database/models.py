# software_fatture/database/models.py

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, Float, Date, Boolean,
    ForeignKey, Text
)

Base = declarative_base()

class Fattura(Base):
    """
    Tabella principale che unisce i campi 'storici' (numero, fornitore, ecc.)
    ai campi ufficiali FatturaPA (DatiTrasmissione, CedentePrestatore,
    Cessionario, DatiGenerali, ecc.).
    """
    __tablename__ = "fatture"

    id = Column(Integer, primary_key=True)

    # ----------------------------
    # STORICI (tuoi campi preesistenti)
    # ----------------------------
    numero = Column(String, index=True)    # ex "Numero" di DatiGeneraliDocumento
    data = Column(Date)                    # puoi usarlo come data fattura
    fornitore = Column(String, index=True) # es. per filtri rapidi: copia di Cedente
    totale = Column(Float, default=0.0)
    pagata = Column(Boolean, default=False)
    data_scadenza = Column(Date, nullable=True)
    # Per evitare duplicati
    hash_xml = Column(String, unique=True, nullable=True)

    # Relationship preesistente
    righe = relationship("RigheFattura", back_populates="fattura")

    # ----------------------------
    # NUOVO: Memorizziamo l'XML integrale per XSLT
    # ----------------------------
    xml_raw = Column(Text, nullable=True)

    # ----------------------------
    # FATTURAELETTRONICAHEADER
    # ----------------------------

    # SoggettoEmittente
    soggetto_emittente = Column(String)  # Esempio: "CC", "TZ", "SE"

    # --- DatiTrasmissione
    id_paese_trasmittente = Column(String)
    id_codice_trasmittente = Column(String)
    progressivo_invio = Column(String)
    formato_trasmissione = Column(String)  # es: "FPR12"
    codice_destinatario = Column(String)
    pec_destinatario = Column(String)

    # --- Cedente Prestatore
    cedente_id_paese = Column(String)
    cedente_id_codice = Column(String)
    cedente_codice_fiscale = Column(String)
    cedente_denominazione = Column(String)
    cedente_indirizzo = Column(String)
    cedente_numero_civico = Column(String)
    cedente_cap = Column(String)
    cedente_comune = Column(String)
    cedente_provincia = Column(String)
    cedente_nazione = Column(String)

    # RappresentanteFiscale
    rappresentante_cf = Column(String)
    rappresentante_denominazione = Column(String)

    # --- Cessionario Committente
    cessionario_id_paese = Column(String)
    cessionario_id_codice = Column(String)
    cessionario_codice_fiscale = Column(String)
    cessionario_denominazione = Column(String)
    cessionario_indirizzo = Column(String)
    cessionario_cap = Column(String)
    cessionario_comune = Column(String)
    cessionario_provincia = Column(String)
    cessionario_nazione = Column(String)

    # --- TerzoIntermediarioOSoggettoEmittente
    terzo_id_paese = Column(String)
    terzo_id_codice = Column(String)
    terzo_denominazione = Column(String)

    # ----------------------------
    # FATTURAELETTRONICABODY - DATI GENERALI
    # ----------------------------
    tipo_documento = Column(String)       # es: TD01
    divisa = Column(String)               # es: "EUR"
    data_documento = Column(Date)         # Data fattura
    numero_documento = Column(String)
    importo_totale_documento = Column(Float)
    causale = Column(String)

    # ... se vuoi DatiDDT, DatiTrasporto, DatiContratto, DatiConvenzione, ecc.
    # potresti creare tabelle aggiuntive o campi testuali.

    # ----------------------------
    # DATI BENI SERVIZI (DettaglioLinee -> vedi tabella RigheFattura)
    # e Riepilogo IVA
    # ----------------------------
    riepiloghi_iva = relationship(
        "DatiRiepilogoIVA",
        back_populates="fattura",
        cascade="all, delete-orphan"
    )

    # ----------------------------
    # DATI PAGAMENTO
    # ----------------------------
    pagamenti = relationship(
        "DatiPagamento",
        back_populates="fattura",
        cascade="all, delete-orphan"
    )

    # ----------------------------
    # ALLEGATI
    # ----------------------------
    allegati = relationship(
        "AllegatoFattura",
        back_populates="fattura",
        cascade="all, delete-orphan"
    )

# ----------------------------------------------------------------------------
class RigheFattura(Base):
    """
    Righe “storiche” e rif. a FatturaPA: <DettaglioLinee>
    Ho aggiunto alcuni campi per allinearti a FatturaPA: numero_linea, unita_misura,
    prezzo_totale, natura, ecc.
    """
    __tablename__ = "righe_fattura"

    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey("fatture.id"))

    # Preesistente
    descrizione = Column(Text, nullable=False)
    quantita = Column(Float, default=1.0)
    prezzo_unitario = Column(Float, default=0.0)
    aliquota_iva = Column(Float, default=22.0)
    importo_riga = Column(Float, default=0.0)

    # Nuovi campi da DettaglioLinee
    numero_linea = Column(Integer, nullable=True)
    unita_misura = Column(String)  # es. "PZ", "KG"
    prezzo_totale = Column(Float, default=0.0)  # <PrezzoTotale>
    natura = Column(String)  # “N1”, “N2” ecc.
    codice_articolo = Column(String)  # se ci sono <CodiceArticolo>

    fattura = relationship("Fattura", back_populates="righe")

# ----------------------------------------------------------------------------
class DatiRiepilogoIVA(Base):
    """
    Mappa i <DatiRiepilogo> del body. Indica l’aliquota, imponibile, imposta,
    esigibilita, natura (se presente).
    """
    __tablename__ = "dati_riepilogo_iva"

    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey("fatture.id"))

    aliquota_iva = Column(Float)
    imponibile_importo = Column(Float)
    imposta = Column(Float)
    esigibilita_iva = Column(String)
    natura = Column(String)

    fattura = relationship("Fattura", back_populates="riepiloghi_iva")

# ----------------------------------------------------------------------------
class DatiPagamento(Base):
    """
    Mappa i <DatiPagamento><DettaglioPagamento>
    """
    __tablename__ = "dati_pagamento"

    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey("fatture.id"))

    condizioni_pagamento = Column(String)  # “TP02”
    modalita_pagamento = Column(String)    # “MP05” etc.
    data_scadenza_pagamento = Column(Date)
    importo_pagamento = Column(Float)

    fattura = relationship("Fattura", back_populates="pagamenti")

# ----------------------------------------------------------------------------
class AllegatoFattura(Base):
    """
    Mappa <Allegati>. Può contenere NomeAttachment, FormatoAttachment,
    e l’attachment in base64 (o un path).
    """
    __tablename__ = "allegato_fattura"

    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey("fatture.id"))

    nome_attachment = Column(String)
    formato_attachment = Column(String)
    attachment = Column(Text)  # base64

    fattura = relationship("Fattura", back_populates="allegati")

# ----------------------------------------------------------------------------
class PagamentiExtra(Base):
    """
    Tua tabella personalizzata per spese/pagamenti extra,
    non derivanti da fatture ufficiali.
    """
    __tablename__ = "pagamenti_extra"

    id = Column(Integer, primary_key=True)
    data = Column(Date)
    importo = Column(Float, default=0.0)
    descrizione = Column(Text)
    categoria = Column(String, nullable=True)
