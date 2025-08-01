# Dashboard Bedienungsanleitung

Diese Anleitung beschreibt die Bedienung des Flask-Dashboards des Projekts.

## Starten

1. `.env` Datei anlegen und API-Schlüssel eintragen (siehe `README.md`).
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Dashboard starten:
   ```bash
   python app.py
   ```
   Anschließend ist die Oberfläche unter `http://localhost:5000` erreichbar.

## Portfolios verwalten

Oben auf der Startseite können neue Portfolios angelegt werden. Für jedes Portfolio sind ein Name sowie **eigener** Alpaca API Key und Secret erforderlich. Eine API Key/Secret Kombination darf nur einem Portfolio zugeordnet werden.

Bestehende Portfolios lassen sich über den "Delete"-Button entfernen.

## Simulation ausführen

Über den Button **Step** wird ein Simulationsschritt für alle Portfolios ausgelöst. Die Ergebnisse erscheinen anschließend im Dashboard.

## Strategie auswählen und Prompts anpassen

Innerhalb jedes Portfolio-Kastens befindet sich ein Dropdown zur Wahl der Strategie (z.B. `default`, `momentum`, `mean_reversion`). Darunter kann ein eigener Prompt für OpenAI hinterlegt werden. Der Prompt muss die Platzhalter `{strategy_type}`, `{portfolio}` und `{research}` enthalten. Über **Preview** lässt sich das generierte Ergebnis testen, bevor der Prompt gespeichert wird.

## Risiko- und Alarm-Einstellungen

Felder für **Stop Loss**, **Take Profit**, **Max Drawdown** und **Trade PnL Limit** ermöglichen die Festlegung individueller Schwellenwerte. Ein Klick auf **Save** speichert die Werte. Überschreitungen werden als Warnungen im Abschnitt "Risk Alerts" angezeigt.

## Datenansichten pro Portfolio

- **Equity Chart** zeigt Wertentwicklung inkl. Benchmark.
- **Diversification Score** und **Correlation Matrix** geben Hinweise zur Streuung des Portfolios.
- **Allocation Pie Chart** visualisiert die Aufteilung nach Assets.
- **Positions** listen alle offenen Positionen. Sortieren und Filtern ist möglich.
- **Open Orders** zeigt aktuelle Orders samt Status.
- **Activity** protokolliert Aktionen wie Trades oder Alerts (Filterbar nach Typ).
- **PnL Charts** stellen Gewinn/Verlust über verschiedene Intervalle dar.
- **Trades** listet die abgeschlossenen Trades. Über das Eingabefeld können Notizen und Tags gespeichert werden. Klick auf einen Eintrag öffnet Details und Preisverlauf des Trades; der Button "Warum?" zeigt den Decision-Explainer.
- Über die Links **Download**, **Report** und **Export** lassen sich Handelsdaten bzw. komplette Dashboard-Daten exportieren (JSON, CSV oder PDF).

## Vergleichsansicht

Der Link "Compare Portfolios" öffnet eine Seite zum direkten Vergleich mehrerer Portfolios. Dort werden Kernkennzahlen tabellarisch aufgelistet und ein gemeinsamer Equity-Chart dargestellt.

