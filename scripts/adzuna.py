#!/usr/bin/env python3
"""Interroga l'API di Adzuna per ogni profilo attivo in profili.json
e salva le offerte degli ultimi 14 giorni in data/adzuna.json.

Credenziali lette dalle variabili d'ambiente ADZUNA_APP_ID e ADZUNA_APP_KEY
(in GitHub: Settings > Secrets and variables > Actions).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILI = os.path.join(ROOT, "profili.json")
OUT = os.path.join(ROOT, "data", "adzuna.json")

MAX_DAYS = 14
PER_PAGE = 50
# Paesi europei coperti da Adzuna
PAESI_EU = ["de", "nl", "be", "fr", "es", "at", "pl", "ch", "gb"]
NOMI_PAESE = {
    "it": "Italia", "de": "Germania", "nl": "Paesi Bassi", "be": "Belgio",
    "fr": "Francia", "es": "Spagna", "at": "Austria", "pl": "Polonia",
    "ch": "Svizzera", "gb": "Regno Unito",
}


def query_per(profilo):
    """Parametri di ricerca in base a ruolo e seniority."""
    ruolo = profilo["ruolo"].strip()
    sen = (profilo.get("seniority") or "").lower()
    q = {"what": ruolo}
    if sen.startswith("junior"):
        q["what"] = f"junior {ruolo}"
    elif sen.startswith("senior"):
        q["what"] = f"senior {ruolo}"
    elif sen.startswith("mid"):
        q["what_exclude"] = "senior lead junior stage internship"
    elif sen.startswith("lead"):
        q["what_or"] = "lead architect principal"
    return q


def chiama(paese, params, app_id, app_key):
    base = f"https://api.adzuna.com/v1/api/jobs/{paese}/search/1"
    p = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": PER_PAGE,
        "max_days_old": MAX_DAYS,
        "sort_by": "date",
        "content-type": "application/json",
        **params,
    }
    url = base + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        sys.exit("Mancano ADZUNA_APP_ID / ADZUNA_APP_KEY")

    with open(PROFILI, encoding="utf-8") as f:
        profili = [p for p in json.load(f) if p.get("attivo", True)]

    risultati, errori, visti = [], [], set()
    for prof in profili:
        paesi = (["it"] if prof.get("italia") else []) + (PAESI_EU if prof.get("europa") else [])
        params = query_per(prof)
        for paese in paesi:
            try:
                data = chiama(paese, params, app_id, app_key)
            except urllib.error.HTTPError as e:
                errori.append(f"{prof['id']}/{paese}: HTTP {e.code}")
                continue
            except Exception as e:  # rete, timeout, JSON
                errori.append(f"{prof['id']}/{paese}: {e}")
                continue
            for job in data.get("results", []):
                chiave = (prof["id"], str(job.get("id")))
                if chiave in visti:
                    continue
                visti.add(chiave)
                desc = " ".join((job.get("description") or "").split())
                risultati.append({
                    "profiloId": prof["id"],
                    "adzunaId": str(job.get("id")),
                    "titolo": job.get("title", "").strip(),
                    "azienda": (job.get("company") or {}).get("display_name", "").strip(),
                    "citta": (job.get("location") or {}).get("display_name", "").strip(),
                    "paese": NOMI_PAESE.get(paese, paese),
                    "pubblicato": (job.get("created") or "")[:10],
                    "url": job.get("redirect_url", ""),
                    "contratto": job.get("contract_type") or "",
                    "descrizione": desc[:400],
                })
            time.sleep(1)  # rispetta i limiti dell'API

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "giorni_max": MAX_DAYS,
            "profili": [p["id"] for p in profili],
            "errori": errori,
            "risultati": risultati,
        }, f, ensure_ascii=False, indent=1)
    print(f"{len(risultati)} offerte, {len(errori)} errori")


if __name__ == "__main__":
    main()
