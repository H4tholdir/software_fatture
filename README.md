# 📌 Gestione Fatture - Software per la gestione automatizzata delle fatture elettroniche

## 🚀 Descrizione
**Gestione Fatture** è un software avanzato per la gestione automatica delle **fatture elettroniche XML**. Il sistema è pensato per **aziende e liberi professionisti** e offre un'ampia gamma di funzionalità, tra cui:

✅ **Download automatico delle fatture dalla PEC**
✅ **Parsing XML e conversione in database**
✅ **Trasformazione XSLT per anteprima HTML**
✅ **Sincronizzazione su Dropbox**
✅ **Gestione notifiche per scadenze fatture**
✅ **Interfaccia grafica intuitiva (PySide6)**

---

## 🛠 Funzionalità principali
### 📩 **1. Scaricamento automatico delle fatture dalla PEC**
- Connessione IMAP sicura con credenziali salvate in `.env`
- Download automatico degli allegati XML/P7M
- Filtraggio degli XML validi ed esclusione di file di sistema

### 📜 **2. Parsing avanzato delle fatture XML**
- Estrazione automatica di dati: numero, fornitore, importo, scadenza
- **Supporto a file P7M** con decodifica tramite OpenSSL
- Salvataggio in **database SQLite**
- Prevenzione duplicati con hash SHA-256

### 🖼 **3. Visualizzazione HTML con XSLT**
- Utilizzo del **foglio di stile ufficiale FatturaPA**
- Trasformazione XSLT con **lxml** per anteprima dettagliata
- **Visualizzazione diretta nell'interfaccia grafica**

### ☁️ **4. Sincronizzazione su Dropbox**
- **Archiviazione automatica delle fatture** su Dropbox
- Struttura organizzata `/fatture/ANNO/MESE/FORNITORE/NOME.xml`
- Supporto a download massivo in memoria

### 🔔 **5. Notifiche per scadenze**
- Rilevamento **fatture non pagate e in scadenza**
- Filtri per **fatture già scadute o imminenti**

### 🎨 **6. Interfaccia grafica moderna (Qt - PySide6)**
- **Tabella con ricerca avanzata**
- **Filtri per anno, mese, fornitore**
- **Pulsante per scaricare da PEC e caricare su Dropbox**
- **Visualizzazione dettagliata con anteprima XSLT**

---

## 📦 Installazione
### 1️⃣ **Requisiti**
Assicurati di avere **Python 3.8+** installato.

### 2️⃣ **Installazione delle dipendenze**
```bash
pip install -r requirements.txt
```

### 3️⃣ **Configurazione**
- Crea un file `.env` con i dati di accesso alla PEC e Dropbox:
```ini
PEC_SERVER=imaps.pec.tuodominio.com
PEC_USER=tuo_utente@pec.it
PEC_PASSWORD=tuapassword
DROPBOX_ACCESS_TOKEN=tuo_access_token
```

### 4️⃣ **Avvio del software**
```bash
python main.py
```

---

## 🔧 Struttura del progetto
📂 `database/` → Gestione database SQLite con SQLAlchemy  
📂 `services/` → Moduli per PEC, parsing, Dropbox, notifiche  
📂 `ui/` → Interfaccia grafica Qt  
📂 `assets/` → Foglio di stile XSLT  
📂 `logs/` → File di log per errori e debugging  

---

## 📌 Contributi
Se vuoi contribuire allo sviluppo, **fai un fork del progetto e apri una pull request!** ✨

---

## 📜 Licenza
MIT License - **Software open-source e libero per tutti!** 🎉

