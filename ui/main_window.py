# ui/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QComboBox, QLineEdit, QPushButton, QListWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
import os
from datetime import date, timedelta

# Import servizi e DB
from services.pec_service import scarica_allegati_xml
from services.parser_fatture import parse_fattura_xml, salva_fattura_su_db
from services.dropbox_service import upload_xml_to_dropbox
from services.notifications import check_scadenze_imminenti  # se usi
from database.db_session import SessionLocal
from database.models import Fattura

# Per le query e filtri
from sqlalchemy import or_, extract

# IMPORTA la funzione per la trasformazione XSLT
# (Assumendo che xslt_service.py si trovi in /assets)
from assets.xslt_service import genera_html_da_xml

class MainWindow(QMainWindow):
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger  # Logger passato dal main

        self.setWindowTitle("Gestione Fatture - Stile AssoInvoice")

        # Widget centrale + layout verticale
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # ----------------- PARTE 1: Barra in alto (Header) con filtri e pulsanti
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)

        # Combobox Anno
        self.combo_anno = QComboBox()
        self.combo_anno.addItem("Tutti gli anni")
        for y in range(2020, 2027):
            self.combo_anno.addItem(str(y))

        # Combobox Mese
        self.combo_mese = QComboBox()
        self.combo_mese.addItem("Tutti i mesi")
        mesi_label = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                      "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        for m in mesi_label:
            self.combo_mese.addItem(m)

        # Barra di Ricerca Globale
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Ricerca globale...")

        # Pulsante Applica Filtri
        self.btn_applica_filtri = QPushButton("Applica Filtri")
        self.btn_applica_filtri.clicked.connect(self.on_applica_filtri)

        # Pulsante Scarica da PEC
        self.btn_scarica_pec = QPushButton("Scarica Fatture da PEC")
        self.btn_scarica_pec.clicked.connect(self.on_scarica_pec_clicked)

        # Aggiungiamo al layout
        self.header_layout.addWidget(self.combo_anno)
        self.header_layout.addWidget(self.combo_mese)
        self.header_layout.addWidget(self.search_line)
        self.header_layout.addWidget(self.btn_applica_filtri)
        self.header_layout.addWidget(self.btn_scarica_pec)

        self.header_widget.setLayout(self.header_layout)
        self.main_layout.addWidget(self.header_widget)

        # ----------------- PARTE 2: Splitter orizzontale con 3 pannelli
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Pannello sinistro: Lista Cedenti
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.list_cedenti = QListWidget()
        self.list_cedenti.itemSelectionChanged.connect(self.on_cedente_selected)
        self.left_layout.addWidget(self.list_cedenti)
        self.left_panel.setLayout(self.left_layout)

        # Pannello centrale: Tabella Fatture
        self.center_panel = QWidget()
        self.center_layout = QVBoxLayout(self.center_panel)

        self.table_fatture = QTableWidget()
        self.table_fatture.setColumnCount(6)
        self.table_fatture.setHorizontalHeaderLabels(
            ["ID","Numero","Data","Fornitore","Totale","Pagata"]
        )

        # Impostiamo selezione per riga singola
        self.table_fatture.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_fatture.setSelectionMode(QTableWidget.SingleSelection)

        # Evento su doppio click -> viewer separato
        self.table_fatture.itemDoubleClicked.connect(self.on_fattura_double_clicked)
        # Evento su selezione -> anteprima sul pannello destro
        self.table_fatture.itemSelectionChanged.connect(self.on_fattura_selected)

        self.center_layout.addWidget(self.table_fatture)
        self.center_panel.setLayout(self.center_layout)

        # Pannello destro: Anteprima/Dettaglio
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Un QTextEdit per anteprima (in HTML)
        self.text_anteprima = QTextEdit()
        self.text_anteprima.setReadOnly(True)
        self.right_layout.addWidget(self.text_anteprima)

        # Pulsante per segnare la fattura come saldata
        self.btn_saldata = QPushButton("Segna come Saldata")
        self.btn_saldata.clicked.connect(self.on_segna_saldata)
        self.right_layout.addWidget(self.btn_saldata)

        self.right_panel.setLayout(self.right_layout)

        # Aggiungiamo i pannelli al QSplitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.center_panel)
        self.splitter.addWidget(self.right_panel)

        # Carichiamo la lista di cedenti e la tabella iniziale
        self.load_cedenti()
        self.load_fatture_table()

        # Check scadenze 30gg (opzionale)
        self.check_scadenze_30gg()

    # ----------------------------------------------------------------
    # PARTE 3: Metodi di caricamento e filtri
    # ----------------------------------------------------------------

    def load_cedenti(self):
        """
        Carica la lista dei fornitori (cedenti) e li mostra nella list_cedenti.
        """
        db = SessionLocal()
        # Distinct dei fornitori
        fornitori = db.query(Fattura.fornitore).distinct().all()
        db.close()

        self.list_cedenti.clear()
        self.list_cedenti.addItem("Tutti i cedenti")
        for (f_name,) in fornitori:
            if f_name:
                self.list_cedenti.addItem(f_name)

    def load_fatture_table(self, filters=None):
        """
        Carica la tabella delle fatture in base ai filtri specificati.
        Filtri: { anno, mese, cedente, search }
        """
        db = SessionLocal()
        query = db.query(Fattura)

        if filters:
            # Filtro Anno
            if filters.get("anno") and filters["anno"] != "Tutti gli anni":
                try:
                    anno_int = int(filters["anno"])
                    query = query.filter(extract("year", Fattura.data) == anno_int)
                except:
                    pass
            # Filtro Mese
            if filters.get("mese") and filters["mese"] != "Tutti i mesi":
                mesi_map = {
                    "Gennaio":1,"Febbraio":2,"Marzo":3,"Aprile":4,"Maggio":5,"Giugno":6,
                    "Luglio":7,"Agosto":8,"Settembre":9,"Ottobre":10,"Novembre":11,"Dicembre":12
                }
                mese_str = filters["mese"]
                if mese_str in mesi_map:
                    mese_num = mesi_map[mese_str]
                    query = query.filter(extract("month", Fattura.data) == mese_num)

            # Filtro Cedente
            if filters.get("cedente") and filters["cedente"] != "Tutti i cedenti":
                query = query.filter(Fattura.fornitore == filters["cedente"])

            # Ricerca globale (search)
            if filters.get("search"):
                kw = filters["search"]
                query = query.filter(
                    or_(
                        Fattura.fornitore.ilike(f"%{kw}%"),
                        Fattura.numero.ilike(f"%{kw}%")
                    )
                )

        fatture = query.all()
        db.close()

        # Popoliamo la tabella
        self.table_fatture.setRowCount(len(fatture))
        for i, f in enumerate(fatture):
            self.table_fatture.setItem(i, 0, QTableWidgetItem(str(f.id)))
            self.table_fatture.setItem(i, 1, QTableWidgetItem(f.numero or ""))
            self.table_fatture.setItem(i, 2, QTableWidgetItem(str(f.data) if f.data else ""))
            self.table_fatture.setItem(i, 3, QTableWidgetItem(f.fornitore or ""))
            self.table_fatture.setItem(i, 4, QTableWidgetItem(str(f.totale)))
            stato = "Sì" if f.pagata else "No"
            self.table_fatture.setItem(i, 5, QTableWidgetItem(stato))

    def on_applica_filtri(self):
        """
        Quando l'utente preme 'Applica Filtri' (o cambiano i combo),
        raccogliamo i filtri e ricarichiamo la tabella.
        """
        anno = self.combo_anno.currentText()
        mese = self.combo_mese.currentText()
        search = self.search_line.text().strip()

        # Cedente selezionato
        selected_ced = None
        if self.list_cedenti.currentItem():
            selected_ced = self.list_cedenti.currentItem().text()
        else:
            selected_ced = "Tutti i cedenti"

        filters = {
            "anno": anno,
            "mese": mese,
            "cedente": selected_ced,
            "search": search
        }
        self.load_fatture_table(filters)

    def on_cedente_selected(self):
        """
        Ogni volta che selezioniamo un fornitore a sinistra, filtriamo nuovamente.
        """
        self.on_applica_filtri()

    # ----------------------------------------------------------------
    # PARTE 4: Scaricare Fatture da PEC e parse
    # ----------------------------------------------------------------

    def on_scarica_pec_clicked(self):
        """
        Quando clicco sul pulsante 'Scarica Fatture da PEC', scarico i file .xml e li salvo nel DB.
        """
        self.logger.info("Bottone 'Scarica Fatture da PEC' premuto.")
        try:
            scarica_allegati_xml("fatture_temp", logger=self.logger)
            self.logger.info("Download completato. Ora avvio parse e salvataggio.")
            self.parse_and_save_fatture("fatture_temp")
            self.logger.info("Tutte le fatture parse e salvate. Ricarico tabella.")
            # Ricarichiamo la tabella con i filtri attuali
            self.on_applica_filtri()
        except Exception as e:
            self.logger.exception("Errore durante la procedura di scaricamento/parse fatture PEC:")
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{e}")

    def parse_and_save_fatture(self, folder):
        """
        Leggiamo i file .xml in 'folder', li parsiamo e salviamo su DB,
        poi carichiamo su Dropbox (opzionale), infine rimuoviamo i file locali.
        """
        for fname in os.listdir(folder):
            if fname.lower().endswith(".xml"):
                full_path = os.path.join(folder, fname)
                self.logger.debug(f"Parsing file {fname}")
                fattura_obj = parse_fattura_xml(full_path)
                salva_fattura_su_db(fattura_obj)
                self.logger.debug(f"Fattura {fattura_obj.numero} salvata nel DB")

                # Carichiamo su Dropbox se vuoi
                if (fattura_obj.data and fattura_obj.fornitore and fattura_obj.numero):
                    self.logger.debug(f"Carico {fname} su Dropbox...")
                    upload_xml_to_dropbox(full_path, fattura_obj.fornitore,
                                          fattura_obj.data, fattura_obj.numero)
                # Rimuoviamo il file locale
                os.remove(full_path)

    # ----------------------------------------------------------------
    # PARTE 5: EVENTO su SELEZIONE FATTURA -> Mostra anteprima HTML con XSLT
    # ----------------------------------------------------------------
  
    def get_foglio_stile_path(self):
        """
        Restituisce il percorso del foglio di stile XSLT.
        """
        dir_corrente = os.path.dirname(__file__)
        xslt_path = os.path.join(dir_corrente, "..", "assets", "FoglioStile.xsl")
        xslt_path = os.path.abspath(xslt_path)
        return xslt_path

    def on_fattura_selected(self):
        """
        Quando seleziono una riga nella tabella,
        carico la fattura corrispondente e, se esiste xml_raw,
        applico il FoglioStile.xsl per mostrarla in HTML.
        """
        selected_rows = self.table_fatture.selectionModel().selectedRows()
        if not selected_rows:
            self.text_anteprima.clear()
            return

        row = selected_rows[0].row()
        fattura_id = self.table_fatture.item(row, 0).text()

        db = SessionLocal()
        f = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        db.close()

        if f and f.xml_raw:
            try:
                xslt_path = self.get_foglio_stile_path()  # ⬅️ Ora viene chiamata con `self.`
                html = genera_html_da_xml(f.xml_raw, xslt_path)
                self.text_anteprima.setHtml(html)
            except Exception as ex:
                self.logger.exception("Errore durante la trasformazione XSLT:")
                QMessageBox.warning(self, "Anteprima XSLT", f"Errore generazione HTML:\n{ex}")
                self.text_anteprima.clear()
        else:
            self.text_anteprima.clear()


    # ----------------------------------------------------------------
    # PARTE 6: Doppio click su una fattura -> Viewer Separato
    # ----------------------------------------------------------------
    def on_fattura_double_clicked(self, item):
        """
        Se l'utente fa doppio click su una riga della table_fatture,
        apriamo un viewer dedicato (testuale).
        """
        row = item.row()
        fattura_id = self.table_fatture.item(row, 0).text()
        self.show_fattura_viewer(fattura_id)

    def show_fattura_viewer(self, fattura_id):
        """
        Mostriamo una finestra di dialog con i dettagli della fattura.
        (se preferisci, puoi anche qui mostrare XSLT in un QDialog)
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        db = SessionLocal()
        f = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        db.close()
        if not f:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Viewer Fattura {f.numero}")

        layout = QVBoxLayout(dlg)

        text = QTextEdit()
        text.setReadOnly(True)
        detail_str = f"Fornitore: {f.fornitore}\nData: {f.data}\nNumero: {f.numero}\nTotale: {f.totale}\nPagata: {f.pagata}\n"
        if f.righe:
            detail_str += "\nRighe:\n"
            for r in f.righe:
                detail_str += f"- {r.descrizione} x {r.quantita} = {r.importo_riga}\n"
        text.setPlainText(detail_str)

        layout.addWidget(text)

        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(dlg.close)
        layout.addWidget(btn_close)

        dlg.setLayout(layout)
        dlg.exec()

    # ----------------------------------------------------------------
    # PARTE 7: Segnare la Fattura come Saldata
    # ----------------------------------------------------------------
    def on_segna_saldata(self):
        """
        Prendiamo la riga selezionata, settiamo pagata=True su DB, ricarichiamo la tabella.
        """
        selected_rows = self.table_fatture.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Nessuna fattura selezionata.")
            return
        row = selected_rows[0].row()
        fattura_id = self.table_fatture.item(row, 0).text()

        db = SessionLocal()
        f = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if f:
            f.pagata = True
            db.commit()
            QMessageBox.information(self, "OK", "Fattura contrassegnata come saldata.")
        db.close()

        self.on_applica_filtri()  # ricarichiamo la tabella con i filtri

    # ----------------------------------------------------------------
    # PARTE 8: Notifiche di scadenza entro 30 giorni (opzionale)
    # ----------------------------------------------------------------
    def check_scadenze_30gg(self):
        """
        Controlla se ci sono fatture non pagate che scadono entro 30 giorni,
        e mostra un popup. (Funziona se hai data_scadenza in DB)
        """
        db = SessionLocal()
        oggi = date.today()
        limite = oggi + timedelta(days=30)
        fatture_in_scadenza = db.query(Fattura).filter(
            Fattura.pagata == False,
            Fattura.data_scadenza != None,
            Fattura.data_scadenza <= limite
        ).all()
        db.close()

        if fatture_in_scadenza:
            msg = f"Hai {len(fatture_in_scadenza)} fatture in scadenza entro 30 giorni!"
            QMessageBox.warning(self, "Scadenze", msg)
