# Überblick über vorhandene Strategien

In der Anwendung stehen aktuell mehrere einfache Strategietypen zur Auswahl. Sie bestimmen, welche Hinweise OpenAI bei der Entscheidungsfindung bekommt.

## Vorhandene Strategien

### `default`
Die Standardvariante ohne besondere Ausrichtung. OpenAI erhält lediglich die aktuelle Portfolio‑Situation und allgemeine Marktforschung. Gut geeignet, um erste Schritte mit dem Simulator zu machen.

### `momentum`
Fokussiert auf Trendfolgesignale. Kaufentscheidungen werden bevorzugt, wenn der Kurs eines Wertpapiers bereits deutlich gestiegen ist und Stärke zeigt. Verkäufe erfolgen, sobald der Trend abflaut.

### `mean_reversion`
Setzt auf Rückkehr zum Mittelwert. Nach starken Kursanstiegen wird mit fallenden Kursen gerechnet und umgekehrt. Die Strategie sucht also gezielt nach überkauften oder überverkauften Situationen.

## Weitere mögliche Strategien

Im Folgenden einige Ideen, die sich ähnlich wie oben als `strategy_type` verwenden lassen:

1. **breakout** – Einstieg bei Ausbruch über wichtige Widerstände oder unter Unterstützungen.
2. **value** – Fundamentale Bewertung steht im Vordergrund; es werden nur vergleichsweise günstige Aktien gekauft.
3. **news_sentiment** – Handelsentscheidungen basieren stark auf aktueller Nachrichtenlage und deren Sentiment.
4. **pairs_trading** – Gleichzeitig long und short in korrelierenden Werten, um Preisdifferenzen auszunutzen.
5. **scalping** – Sehr kurzfristige Trades mit kleinen Kurszielen und engem Risikomanagement.
