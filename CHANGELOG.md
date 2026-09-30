# Changelog

## 2.0.0: 29 september 2026

De grote verbouwing, grotendeels op verzoek van de eerste gebruikers.

### Prijzen: eindelijk echt
- **De oude prijzen waren nooit echt.** De scraper haalde ze van mcdonaldsmenu.nl, dat nooit prijzen opleverde; de site viel altijd terug op vaste getallen. Dat domein staat inmiddels te koop.
- **Nieuwe scraper** (`scraper/`): meet elke ochtend tien filialen op Thuisbezorgd en Uber Eats en publiceert de **mediaan-bezorgprijs**. Mislukt de meting, dan blijven de oude prijzen staan en ziet de bezoeker dat ze verouderd zijn.
- **Prijsgeschiedenis** (`history.json`): nuggets per kwartaal sinds 2021 uit het Internet Archive, Veggie Nuggets tot ze in 2025 van het menu gingen, en de Big Mac sinds 1987 (The Economist).
- Op de site: een eerlijke prijsregel met datum, een tabel per filiaal en een formulier om zelf een winkelprijs te melden.

### Gevraagd door gebruikers
- **Verspillingsmodus**: meer bestellen als dat goedkoper is.
- **Grafiek aantal vs. prijs.**
- **Prijsgeschiedenis** met grafieken, inclusief veggie (historisch) en de Big Mac-trend.

### Nieuw
- Direct antwoord tijdens het typen, deelbare links (`?n=43`) en een deelknop.
- Prijs per nugget, ook per doosje, met een 👑 voor de voordeligste.
- Paaseieren, "Alle manieren", "Waarom 43?".
- Groepsbestelling met Tikkie-bedrag, budgetmodus, getallenrooster (standaard dicht), sausjes/calorieën/nugget-index, uitdaging van de dag en een doosjesspeeltuin.

### Verbeterd
- Invoercontrole (hele getallen tot 10.000) en de tab bevriest niet meer bij grote getallen.
- Nederlandse bedragen (€ 3,55), contrast op WCAG AA, donkere modus en een compacte mobiele weergave.
- Favicon, deelplaatje voor Slack/WhatsApp, meta-tags en `robots.txt`.
- `www.canitnugget.nl` werkt nu (doorverwijzing).
- Testbestanden, logs en scripts uit de publieke webroot gehaald.

### Repository
- Sectie *Bijdragen* in de README, issue-formulieren (fout, idee, winkelprijs), pull request-sjabloon, [Unlicense](LICENSE) en deze changelog.

## 1.0.0: september 2025

Eerste versie: kan-het-calculator voor 6, 9 en 20 nuggets met de goedkoopste combinatie.
