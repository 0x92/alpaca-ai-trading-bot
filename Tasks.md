# Tasks.md — Multi-Portfolio Alpaca Trading Simulator (from scratch)

## Epic: Multi-Portfolio Trading Simulator mit OpenAI-Research, Realtime-Dashboard & Strategie-Management

---

### Task 0: Projektstruktur, .gitignore und .env Setup

- [x] Lege die grundlegende Projektstruktur an:
    - [x] Hauptverzeichnis, z.B. `alpaca-trading-sim/`
    - [x] Unterordner:
        - [x] `app/` (für Python-Module)
        - [x] `templates/` (für Flask-Templates)
        - [x] `static/` (für JS, CSS, ggf. Chart.js)
        - [x] `tests/` (optional für Unit-Tests)
    - [x] Wichtige Files:
        - [x] `app/__init__.py`
        - [x] `requirements.txt`
        - [x] `README.md`
        - [x] `.gitignore`
        - [x] `.env.example` und `.env`
- [x] Erstelle eine sinnvolle `.gitignore`, z.B.:
    - `.env`
    - `__pycache__/`
    - `.vscode/`
    - `*.pyc`
    - `*.db`
- [x] Erstelle eine `.env.example` mit Platzhaltern für alle benötigten Secrets (API-Keys etc.).
- [x] Implementiere das Laden von Umgebungsvariablen in Python (`python-dotenv` oder `os.environ`).
- [x] Test: Einlesen von Keys aus der `.env` in einer Beispieldatei (z.B. `print(os.environ.get("ALPACA_API_KEY"))`).

---

### Task 1: Basis-Modul `portfolio_manager.py` anlegen

- [x] Erstelle das Python-Modul `portfolio_manager.py` im `app/`-Ordner.
    - [x] Implementiere die Klasse `Portfolio`:
        - [x] Konstruktor mit Name, Alpaca-API-Key, Secret, Base-URL.
        - [x] Methode `get_account_info()` für Account-Status.
        - [x] Methode `place_order()` für Market-Orders.
        - [x] Member `history` für Order-Historie.
    - [x] Implementiere die Klasse `MultiPortfolioManager`:
        - [x] Verwaltung mehrerer Portfolios.
        - [x] Methode `step_all()` für Trades über alle Portfolios (zunächst Dummy-Entscheidung).
- [x] Test: Lege 2 Test-Portfolios an, prüfe Account-Info und platziere eine Beispiel-Order (Paper API).

---

### Task 2: Research-Engine bauen (Yahoo Finance, Finnhub, NewsAPI)

- [x] Erstelle das Modul `research_engine.py` im `app/`-Ordner mit folgenden Funktionen:
    - [x] `get_fundamentals_yahoo(symbol)`
    - [x] `get_news_finnhub(symbol)`
    - [x] `analyze_sentiment(news_items)`
    - [x] `get_research(symbol)` (Kombiniert alles zu JSON)
- [x] Test: Gebe für ein Beispiel-Symbol das Research-JSON aus.

---

### Task 3: OpenAI-Strategie in `portfolio_manager.py` integrieren

- [x] Überarbeite `portfolio_manager.py`:
    - [x] Importiere das Research-Modul.
    - [x] Implementiere `get_strategy_from_openai(portfolio, research, strategy_type)`.
    - [x] Prompt soll Portfolio-Status, Research-JSON und Strategie-Typ enthalten.
    - [x] Die Methode `step_all()` soll Research holen und an OpenAI geben.
- [x] Test: Lass für mehrere Strategien mit gleichem Portfolio verschiedene Entscheidungen ausgeben.

---

### Task 4: Flask-Webdashboard Grundgerüst

- [x] Erstelle das Flask-App-Modul `app.py` im Hauptverzeichnis:
    - [x] Dashboard mit Übersicht aller Portfolios (Name, Cash, Portfolio-Wert, letzte Trades).
    - [x] Template mit Tailwind CSS für grundlegendes UI.
    - [x] Button "Step" für einen Simulationsschritt.
- [x] Test: Portfolios und ihre Orders werden im Browser korrekt angezeigt.

---

### Task 5: Echtzeit-Updates mit Flask-SocketIO

- [x] Integriere Flask-SocketIO in `app.py`.
    - [x] Sende nach jedem Portfolio-Update/Order ein `trade_update`-Event an alle Clients.
    - [x] Template: Füge Socket.IO-Client ein, der Events abfängt.
    - [x] Aktualisiere Portfolio- und Order-Listen live im Dashboard.
- [x] Test: Mehrere Browserfenster zeigen die Updates in Echtzeit.

---

### Task 6: Chart.js für Order-Historie und Equity Curve

- [x] Baue im Dashboard ein Chart.js-Linechart für Portfolio-Equity (Wertentwicklung).
    - [x] Backend: Zeitreihe für Equity vorbereiten und ans Template geben.
    - [x] Chart aktualisiert sich automatisch bei neuem Data-Update (über Sockets oder AJAX).
- [ ] Optional: Pie-Chart für Holdings.
- [x] Test: Mehrere Trades, Entwicklung wird als Chart angezeigt.

---

### Task 7: Strategie pro Portfolio steuerbar machen

- [x] Erweitere `Portfolio` um ein Attribut `strategy_type`.
- [x] Im Dashboard: Dropdown für Strategieauswahl je Portfolio.
    - [x] Neue Route `/portfolio/<name>/set_strategy` im Backend.
    - [x] Nach Änderung wird beim nächsten Schritt die neue Strategie genutzt.
- [x] Test: Verschiedene Strategien führen zu unterschiedlichem Trading-Verhalten.

---

### Task 8: (Optional) Portfolio-Management UI & User-Flows

- [x] Möglichkeit, neue Portfolios im Dashboard anzulegen/löschen.
- [x] Übersicht über alle Portfolios und ihre Strategien.
- [x] Persistenz in SQLite oder JSON.

---

### Task 9: (Optional) Security & Error Handling

- [x] API Keys/Secrets niemals an den Client geben.
- [x] Fehler und Rate Limits sauber behandeln und loggen.

---

### Task 10: Performance-Benchmarks & Vergleich (z.B. S&P500, DAX)

- [x] Baue eine Vergleichsfunktion, die die Performance jedes Portfolios automatisch mit mindestens einem Index (z.B. S&P500, DAX) vergleicht.
    - [x] Hole historische und aktuelle Daten der Benchmarks per API (z.B. Yahoo Finance, Alpha Vantage).
    - [x] Berechne Out- und Underperformance jedes Portfolios vs. Benchmarks (ab Startzeitpunkt).
    - [x] Visualisiere die Performance-Vergleiche als Chart im Dashboard.
    - [x] Test: Zeige für mindestens zwei Portfolios und einen Index den Performance-Vergleich an.

---

### Task 11: Intelligentes Positions- und Risikomanagement

- [x] Implementiere Risiko-Features pro Portfolio:
    - [x] Setze Stop-Loss, Take-Profit, Max-Drawdown-Limits (einstellbar pro Portfolio).
    - [x] Bei Überschreiten automatisches Schließen von Positionen oder Warnmeldungen.
    - [x] Ergänze einen “Smart Allocator” für Positionsgrößen anhand Risikoniveau und/oder KI-Empfehlung.
    - [x] Visualisiere Risikostatus und Alarme im Dashboard.
    - [x] Test: Simuliere einen Drawdown und prüfe, ob korrekt reagiert wird.

---

### Task 12: Trade-Log Export und Report-Generator

- [x] Implementiere einen Export für alle Trades (Orders) jedes Portfolios.
    - [x] Exporte als CSV, Excel und/oder PDF (Download-Link im Dashboard).
    - [x] Generiere automatisch Monats- und Jahresberichte mit Statistiken (Gewinn/Verlust, Winrate, Gebühren etc.).
    - [ ] Optional: Report-Versand per E-Mail.
    - [x] Test: Erzeuge einen Beispiel-Export und Bericht für ein Test-Portfolio.

---

### Task 13: Visualisierung von Correlation & Diversifikation

- [x] Analysiere die Korrelation zwischen gehaltenen Assets (auf Basis historischer Kursdaten).
    - [x] Baue eine Heatmap oder Korrelationsmatrix (z.B. mit Plotly, Chart.js oder D3.js).
    - [x] Berechne und visualisiere einen Diversifikations-Score pro Portfolio.
    - [x] Warne bei Klumpenrisiken (z.B. zu hoher Anteil eines Assets).
    - [x] Zeige die Visualisierungen im Dashboard.
    - [x] Test: Lege ein Portfolio mit stark korrelierten Assets an und prüfe die Anzeige.

---

### Task 14: Strategie-Editor mit Custom Prompts (No-Code-Editor für OpenAI-Trading-Strategien)

- [x] Entwickle einen Editor im Dashboard, mit dem User eigene OpenAI-Prompts/Strategie-Templates konfigurieren können (ohne Programmierung).
    - [x] Speichere die Prompts pro Portfolio in der Datenbank oder als JSON.
    - [x] Validierung der Eingaben, Vorschau auf das Resultat.
    - [x] Binde die Custom-Prompts in die Entscheidungslogik ein, sodass bei jedem Trade der gewählte Prompt genutzt wird.
    - [x] Test: Definiere einen eigenen Prompt und führe Trades danach aus.

---


### Task 15: Live-Positionsübersicht pro Portfolio (Bot)

- [x] Baue eine Live-Ansicht aller offenen Positionen je Portfolio ins Dashboard:
    - [x] Symbol, Stückzahl, aktueller Kurs, durchschnittlicher Einstiegskurs, aktueller Gewinn/Verlust (absolut/relativ)
    - [x] Echtzeit-Update via SocketIO/Websocket
    - [x] Sortier- und Filteroption (z.B. nach Gewinn/Verlust)

---

### Task 16: Offene Trades/Orders in Echtzeit visualisieren

- [x] **Backend**:
    - [x] API-Route `/api/portfolio/<name>/orders?status=open`
      Liefert alle offenen (pending) Orders je Portfolio.
    - [x] Backend-Logik, um Order-Status zu überwachen und Änderungen an das Frontend zu pushen.
- [x] **Frontend**:
    - [x] Visualisierung aller offenen Orders im Dashboard (mit Status, Typ, Symbol, Zielkurs, Menge).
    - [x] Farbcodierung und Icons je Status.
    - [x] Echtzeit-Update per SocketIO/Websocket.

---

### Task 17: Trade-Historie mit erweiterten Charts

- [x] **Backend**:
    - [x] API-Route `/api/portfolio/<name>/trade_history`
      Liefert alle abgeschlossenen Trades mit Details (Zeitpunkt, Entry/Exit, Resultat etc.).
    - [x] Option: Serverseitige Filter- und Suchfunktion.
- [x] **Frontend**:
    - [x] Integriere Chart.js-Trade-Timeline.
    - [x] Drilldown-Funktion: Beim Klick auf einen Trade Details anzeigen.
    - [x] Summenstatistiken und Einzeltrade-View.

---

### Task 18: Kurs- und Performance-Chart je Trade

- [x] **Backend**:
    - [x] API-Route `/api/trade/<id>/price_history`
      Liefert den Kursverlauf des gehandelten Assets für den Zeitraum des Trades.
    - [x] Backend-Logik: Hole historische Preisdaten von Datenanbieter (z.B. Yahoo, Finnhub).
- [x] **Frontend**:
    - [x] Chart.js für Kursverlauf pro Trade/Position.
    - [x] Visualisierung von Einstiegs-, Ausstiegs-, SL/TP-Punkten und aktuellem Kurs.

---

### Task 19: Investitionsübersicht & Asset-Allokation

- [x] **Backend**:
    - [x] Berechne und aggregiere die aktuelle Verteilung aller Investments je Portfolio.
    - [x] API-Route `/api/portfolio/<name>/allocation`
      Liefert Allokation als Liste/Prozentwerte je Asset.
- [x] **Frontend**:
    - [x] Pie Chart (Chart.js) für Investment Breakdown im Dashboard.
    - [x] Klumpenrisiken visuell hervorheben.

---

### Task 20: Gewinn/Verlust-Diagramme (PnL Analysis)

- [x] **Backend**:
    - [x] API-Route `/api/portfolio/<name>/pnl_history?interval=day|week|month`
      Liefert PnL-Zeitreihe je Portfolio.
    - [x] Berechne Top/Flop-Trades serverseitig.
- [x] **Frontend**:
    - [x] Chart.js-Diagramme für Tages-/Wochen-/Monatsergebnis und Equity Curve.
    - [x] Bar-Chart für Top-/Flop-Trades.
    - [x] Zeitraumauswahl im UI.

---

### Task 21: Aktivitätsfeed & Log-Viewer

- [x] **Backend**:
    - [x] Logik, die alle Aktionen (Trades, Orders, Research, Strategie-Wechsel) pro Portfolio als Log speichert.
    - [x] API-Route `/api/portfolio/<name>/activity_log?type=all|trades|alerts`
      Liefert chronologischen Feed.
    - [x] Option: Events per SocketIO pushen.
- [x] **Frontend**:
    - [x] Aktivitätsfeed im Dashboard, filterbar nach Typ.
    - [x] Live-Update ohne Reload.

---

### Task 22: Bot-KI-Entscheidungen transparent machen (Decision-Explainer)

- [x] **Backend**:
    - [x] Speichere Prompt, Research-Input und KI-Antwort zu jeder Trading-Entscheidung im Portfolio/Trade-Objekt.
    - [x] API-Route `/api/trade/<id>/decision_explainer`
      Liefert alle Entscheidungsdaten für einen Trade.
- [x] **Frontend**:
    - [x] Button “Warum?” pro Trade/Order.
    - [x] Popup/Modal mit Prompt, Input und KI-Output.
    - [ ] Optional: Visualisiere Einflussfaktoren aus dem Research.

---

### Task 23: Alerts und Schwellenwert-Warnungen

- [x] **Backend**:
    - [x] Felder für Schwellenwerte im Portfolio/Trade (max. Drawdown, PnL-Limits).
    - [x] Überwache in der Trade- und Positionslogik, ob Schwellenwerte überschritten werden.
    - [x] API-Route `/api/portfolio/<name>/alerts`
    - [x] Push Alerts per SocketIO und ggf. E-Mail/Push.
- [x] **Frontend**:
    - [x] Anzeigen und Konfigurieren von Alerts im Dashboard.
    - [x] Visual/Akustisch (z.B. Banner, Sound).

---

### Task 24: User-Notizen & Tagging pro Trade

- [x] **Backend**:
    - [x] Datenmodell: Notiz- und Tag-Felder an Trade-Objekt.
    - [x] API-Routen zum Hinzufügen, Bearbeiten, Löschen von Notizen/Tags (`/api/trade/<id>/notes`, `/api/trade/<id>/tags`).
- [x] **Frontend**:
    - [x] Notiz-Eingabefeld und Tag-Widget pro Trade/Position im UI.
    - [x] Anzeige und Suche nach Tags/Notizen.

---

### Task 25: Multi-Dashboard-View & Bot-Vergleich

- [x] **Backend**:
    - [x] API-Route `/api/portfolios/compare?names=Bot1,Bot2`
      Liefert Kernmetriken mehrerer Bots für Vergleich (Equity, PnL, Allokation, Risiko etc.).
- [x] **Frontend**:
    - [x] Split View/Switch zwischen mehreren Dashboards.
    - [x] Heatmap/Tabellen für direkten Vergleich.

---

### Task 26: Export aller Dashboard-Daten

- [x] **Backend**:
    - [x] Export-Logik für CSV, JSON, PDF aller Portfolio-/Trade-/Chart-Daten.
    - [x] API-Route `/api/portfolio/<name>/export?format=csv|json|pdf`
- [x] **Frontend**:
    - [x] Export-Button im Dashboard, Auswahl von Bereich und Format.

---

### Task 27: Dark Mode & Custom Themes

- [ ] **Backend**:  
    - [ ] API-Route `/api/user/<id>/theme`  
      Speichert/fetch Theme-Einstellung pro User (optional: DB).
- [ ] **Frontend**:  
    - [ ] Dark Mode Switch, Auswahl Themes.
    - [ ] Speicherung im Profil/Local Storage.

---

### Task 28: Realtime-Benchmark-Overlay

- [ ] **Backend**:  
    - [ ] API-Route `/api/portfolio/<name>/benchmark_overlay?symbol=SPY`
      Liefert eigene Performance + Benchmark-Daten für Overlay-Chart.
    - [ ] Regelmäßiges Updaten mit externen Kursdaten.
- [ ] **Frontend**:  
    - [ ] Overlay-Chart je Asset/Portfolio mit Portfolio vs. Index-Linie.
    - [ ] Auswahl Benchmark im UI.

---

### Task 29: Mobile-optimierte Dashboard-Ansicht

- [ ] **Backend**:  
    - [ ] Sicherstellen, dass alle API-Routen und Datenformate auch mobil performant nutzbar sind.
- [ ] **Frontend**:  
    - [ ] Responsive Redesign aller UI-Komponenten (TailwindCSS, Media Queries).
    - [ ] Touch-optimierte Bedienelemente.
    - [ ] Mobile-spezifische Features, z.B. Swipe für Portfolio-Wechsel.

---

### Task 30: Advanced-Analytics & “What-If”-Simulation

- [ ] **Backend**:  
    - [ ] Simulation-Logik für alternative Szenarien (Buy&Hold, KI, Zufall etc.).
    - [ ] API-Route `/api/portfolio/<name>/whatif?scenario=hold|ki|random`
      Liefert simulierte PnL-Kurven für verschiedene Szenarien.
- [ ] **Frontend**:  
    - [ ] Visualisierung (Chart.js) der realen und simulierten Szenarien als Overlay.
    - [ ] UI zur Auswahl und zum Vergleich verschiedener What-If-Analysen.

---

### Task 31: Multi-Portfolio-Handling gemäß 1 API Key = 1 Portfolio (Alpaca) umsetzen

**Ziel:**  
Die Systemlogik und das gesamte Dashboard müssen so angepasst werden, dass **jedes Portfolio mit einem eigenen Alpaca-API-Key betrieben wird**.  
Mehrere simultan laufende Portfolios benötigen entsprechend viele API Keys (jeweils von separaten Alpaca-Accounts).  
Das System soll es ermöglichen, beliebig viele (aber immer getrennte) Portfolios zu verwalten, wobei **jeder Portfolio-Instanz ein individuelles Key/Secret-Paar zugeordnet ist**.

---

#### Subtasks:

- [x] **31.1** Portfolio-Datenstruktur so erweitern, dass pro Portfolio die API-Zugangsdaten (Key, Secret, Base-URL) zwingend hinterlegt sind.
  – Optional: E-Mail/Friendly Name/Account-Info je Portfolio speichern.  
  – Schlüssel-Validierung: Nur gültige (Paper/Live) Keys akzeptieren.

- [x] **31.2** Portfolio-Objekte dürfen keine API Keys teilen!
  – Prüfe dies beim Hinzufügen neuer Portfolios im System.

- [x] **31.3** Im Dashboard und beim Erstellen eines neuen Portfolios:
  – Formular für API Key & Secret hinzufügen (beides Pflichtfelder).  
  – Optional: Wahl ob Paper oder Live Trading (Base-URL Feld).  
  – Hinweis/Tool-Tipp: "Ein Alpaca-Account/Key = ein Portfolio. Für weitere Portfolios weitere Accounts und Keys anlegen!"

- [x] **31.4** Beim Editieren: Zeige Key-Infos (abgedeckt), kein Klartext!

- [x] **31.5** Validierung: Bei fehlenden oder doppelten Keys darf das Portfolio nicht angelegt werden.

- [x] **31.6** Beim Initialisieren jedes Portfolios im Backend (Portfolio-Manager, Models etc.):
  – API Key, Secret und Base-URL laden und an die jeweilige Portfolio-Instanz weitergeben.  
  – Keine zentrale API-Session – jede Portfolio-Instanz nutzt eine eigene API-Connection mit eigenen Zugangsdaten.  
  – Exception-Handling für ungültige oder abgelaufene Keys.

- [x] **31.7** MultiPortfolioManager etc. dürfen nicht auf einen globalen API-Key zurückfallen!

- [x] **31.8** Speichere Portfolios samt zugehörigen API-Daten in der gewünschten Persistenz (JSON, DB etc.).
  – Nie Secrets an den Client senden oder in Logs speichern!  
  – Maskiere/verschlüssele gespeicherte Keys.

- [x] **31.9** Schreibe automatisierte Tests:
  – Zwei Portfolios mit unterschiedlichen Keys müssen unabhängig traden und agieren können.  
  – Ein Portfolio mit ungültigem oder gesperrtem Key gibt einen sauberen Fehler aus und stoppt alle Aktionen.  
  – Versuche, zwei Portfolios mit dem gleichen Key zu erstellen → Fehler/Hinweis.  
  – Alle Portfolio-spezifischen Aktionen (z.B. Trades, Status) laufen *immer* nur mit den Credentials des jeweiligen Portfolios.

- [ ] **31.10** (Optional) Baue ein Key-Management-Modul:
  – Möglichkeit, API Keys zentral im Backend sicher zu speichern, anzuzeigen, zu löschen.  
  – Keys nur zur Laufzeit an das jeweilige Portfolio-Objekt übergeben.  
  – Hinweise für den Nutzer zu Sicherheit & Aufbewahrung.

- [x] **31.11** Dokumentiere im README.md und/oder im Dashboard-UI die Info:
  – "Ein Alpaca-API-Key entspricht immer genau einem Portfolio. Für weitere unabhängige Portfolios sind weitere (Paper-)Accounts und Keys nötig!"

---

**Fazit:**  
Nach diesem Task ist die gesamte App konsistent und professionell darauf ausgelegt, dass jedes Portfolio auf exakt einen Alpaca-Account/API-Key mappt und echte Multi-Portfolio-Strategien möglich sind.  
Ein Nutzer kann beliebig viele Bots/Portfolios gleichzeitig anlegen, **muss aber für jedes einen eigenen API Key bereitstellen**.

---


```

**Jeder Task ist optional und kann als Epic, Feature, oder einzelne Issues/Stories behandelt werden!**
Wenn du für einen Task konkrete Subtasks, Beispiel-UI, ein Issue-Template oder eine Architektur-Skizze willst, sag einfach Bescheid.

## Quickstart & Testing

- [x] Installiere Requirements (`pip install -r requirements.txt`).
- [x] Lege API-Keys für Alpaca (Paper), Yahoo/Finnhub/NewsAPI, OpenAI in der `.env` an.
- [x] Starte lokal: Das Dashboard zeigt Portfolios und Orders, Trades laufen simuliert ab.

---

## Stretch Goals / Nice-to-have

- [ ] Backtesting für Strategien.
- [ ] AutoML-Tuning für KI-Strategien.
- [ ] Mobile-optimiertes UI.

---

**Hinweis:**  
Jede Task ist für Coding-Agents einzeln und unabhängig bearbeitbar!  
Mit Task 0 starten, dann Schritt für Schritt weiter — Abhängigkeiten beachten.
