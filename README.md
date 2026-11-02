# Radar Placement – ponte Adzuna

Raccoglie dall'API di Adzuna le offerte degli ultimi 14 giorni per i profili da piazzare
e le salva in `data/adzuna.json`. Lo scanner Radar Placement IT legge il file e porta
le offerte nella dashboard.

- `profili.json` – profili attivi (sincronizzato dallo scanner con la dashboard; nessuna nota riservata)
- `scripts/adzuna.py` – interroga Adzuna (Italia + DE, NL, BE, FR, ES, AT, PL, CH, GB)
- `.github/workflows/adzuna.yml` – gira alle 5:20 e 11:20 UTC, a ogni modifica di `profili.json` e a mano da *Actions*

## Configurazione

In *Settings → Secrets and variables → Actions* aggiungere:

- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

Il repository è pubblico: contiene solo ruoli, seniority e offerte pubbliche, mai chiavi o note sui candidati.
