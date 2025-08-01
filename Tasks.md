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


Klar, hier kommen **weitere fortgeschrittene Tasks ab Task 15**, die das Dashboard richtig “next level” machen!
Das Ziel: **Maximaler Einblick in jeden Bot und jede Position, coole Visualisierungen, Transparenz, Nutzerkomfort und “Geek Value”.**
Alle Tasks sind so formuliert, dass sie einzeln umgesetzt werden können. Vieles davon ist auch Inspiration für späteres Premium- oder Multi-User-Feature-Set!

---

```markdown
### Task 15: Live-Positionsübersicht pro Portfolio (Bot)

- [x] Baue eine Live-Ansicht aller offenen Positionen je Portfolio ins Dashboard:
    - [x] Symbol, Stückzahl, aktueller Kurs, durchschnittlicher Einstiegskurs, aktueller Gewinn/Verlust (absolut/relativ)
    - [x] Echtzeit-Update via SocketIO/Websocket
    - [x] Sortier- und Filteroption (z.B. nach Gewinn/Verlust)

---

### Task 16: Offene Trades/Orders in Echtzeit visualisieren

- [ ] Zeige alle aktiven offenen Orders (pending trades) pro Portfolio übersichtlich an.
- [ ] Visualisiere den Status (offen, ausgeführt, teilweise, abgelehnt) mit Icon/Farbe.
- [ ] Zeige geplante Order-Strategien (z.B. Stop Loss/Take Profit) direkt im Dashboard an.

---

### Task 17: Trade-Historie mit erweiterten Charts

- [ ] Integriere in jedem Portfolio eine Timeline (Chart.js) der durchgeführten Trades.
- [ ] Zeige auf Klick alle Details (Order-Parameter, Zeitpunkt, Kurs, Resultat, Strategie).
- [ ] Ermögliche einen Drill-Down von Summenstatistik → Einzeltrade-Ansicht.

---

### Task 18: Kurs- und Performance-Chart je Trade

- [ ] Für jede offene Position zeige einen Chart (Chart.js) mit dem Kursverlauf des gehandelten Assets seit Einstieg.
- [ ] Markiere Einstiegs- und ggf. Ausstiegspunkte, Stop-Loss/Take-Profit-Linien.
- [ ] Visualisiere den aktuellen Gewinn/Verlust live im Chart.

---

### Task 19: Investitionsübersicht & Asset-Allokation

- [ ] Zeige pro Bot ein “Investment Breakdown” als Tortendiagramm (Pie Chart):
    - [ ] Prozentuale/absolute Verteilung aller investierten Mittel auf die einzelnen Assets
    - [ ] Hebe große Positionen oder Klumpenrisiken visuell hervor.

---

### Task 20: Gewinn/Verlust-Diagramme (PnL Analysis)

- [ ] Zeige pro Bot folgende Diagramme:
    - [ ] Tages- und Wochenergebnis (PnL) als Liniendiagramm
    - [ ] Historische Gesamtperformance (Equity Curve)
    - [ ] Top/Flop-Trades nach Gewinn/Verlust (Bar Chart)
- [ ] Ermögliche den Zeitraum zu filtern (Tag, Woche, Monat, Gesamt).

---

### Task 21: Aktivitätsfeed & Log-Viewer

- [ ] Integriere einen Feed, der alle Aktionen des Bots chronologisch auflistet:
    - [ ] Trades, Orderplatzierungen, Research-Events, Strategie-Wechsel
    - [ ] Live-Updates ohne Reload (SocketIO)
    - [ ] Filter nach Typ (nur Trades, nur Warnungen, nur Systeminfos)

---

### Task 22: Bot-KI-Entscheidungen transparent machen (Decision-Explainer)

- [ ] Füge einen “Warum hat der Bot das gemacht?”-Button hinzu:
    - [ ] Zeige für jede Aktion die genutzte Strategie und das OpenAI-Prompt inkl. Antwort.
    - [ ] Optional: Visualisiere welche Research-Daten zu dieser Entscheidung geführt haben.
    - [ ] “KI-Logbuch” pro Bot anlegen.

---

### Task 23: Alerts und Schwellenwert-Warnungen

- [ ] Implementiere ein Alert-System:
    - [ ] Gewinn/Verlust-Thresholds pro Trade/Portfolio einstellbar (z.B. Alarm bei -10% Drawdown)
    - [ ] Visuelle und akustische Warnungen im Dashboard
    - [ ] Optionale Benachrichtigungen per E-Mail/Push

---

### Task 24: User-Notizen & Tagging pro Trade

- [ ] Erlaube dem Nutzer zu jedem Trade/Position/Portfolio eigene Notizen zu hinterlegen.
- [ ] Trades können mit Tags (z.B. “Momentum”, “News”, “KI-Tipp”) versehen werden.
- [ ] Tags und Notizen im UI und Export anzeigen.

---

### Task 25: Multi-Dashboard-View & Bot-Vergleich

- [ ] Erlaube die parallele Anzeige mehrerer Dashboards (z.B. Split View für 2 Bots)
    - [ ] Direktvergleich wichtiger Kennzahlen (Gewinn/Verlust, Allokation, Risikolevel)
    - [ ] Heatmap: Welcher Bot performt am besten?

---

### Task 26: Export aller Dashboard-Daten

- [ ] Exportiere den aktuellen Zustand aller Dashboards (als CSV, JSON, PDF)
- [ ] Exportoption für einzelne Charts, Tabellen, Trade-Logs, Aktivitätsfeeds

---

### Task 27: Dark Mode & Custom Themes

- [ ] Ermögliche einen Dark Mode und mehrere Color Themes für das Dashboard.
- [ ] Speichere die Einstellung im User-Profil / Browser Storage

---

### Task 28: Realtime-Benchmark-Overlay

- [ ] Zeige pro Asset und Portfolio einen Overlay-Linienchart, der die eigene Performance mit dem Marktindex (S&P500, DAX, BTC etc.) live vergleicht

---

### Task 29: Mobile-optimierte Dashboard-Ansicht

- [ ] Responsive Redesign aller Dashboards und Charts
- [ ] Touch-freundliche Bedienung
- [ ] Mobile-spezifische Features wie “Swipe zum Portfolio-Wechsel”

---

### Task 30: Advanced-Analytics & “What-If”-Simulation

- [ ] Simuliere, wie sich der Gewinn/Verlust entwickelt hätte, wenn der Bot anders entschieden hätte (“What-If-Mode”)
- [ ] Szenarien vergleichbar anzeigen (z.B. Buy&Hold, KI, Zufall)
- [ ] Visualisierung der Ergebnisse als Overlay/Chart

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
