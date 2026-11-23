#!/usr/bin/env python3
"""Genera il "Calendario situazionale" di index.html dal Google Calendar pubblico di Lo Sbando.

Uso:  python3 scripts/calendario.py            (scarica il calendario e aggiorna index.html)
      python3 scripts/calendario.py file.ics   (usa un file .ics locale, utile per provare)

Riscrive solo ciò che sta tra <!-- CALENDARIO:INIZIO --> e <!-- CALENDARIO:FINE --> in index.html
e aggiorna <lastmod> in sitemap.xml quando il calendario cambia. Solo libreria standard.

Regole:
- evento singolo            -> elenco del mese + quadrato pieno nella griglia
- evento che si ripete ogni settimana (RRULE WEEKLY) -> box "Ogni settimana" + quadrati a contorno
- mesi mostrati: dal mese corrente fino all'ultimo mese con eventi (al massimo MESI_MAX)
- titolo, descrizione e orari vengono da Google Calendar; la descrizione va su una riga
"""

import html
import re
import sys
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ICS_URL = ("https://calendar.google.com/calendar/ical/"
           "ae9e0ea7852e54f4884156572e2102671b13b10e3684e2937462c524d8884fae"
           "%40group.calendar.google.com/public/basic.ics")
TZ = ZoneInfo("Europe/Rome")
MESI_MAX = 4

RADICE = Path(__file__).resolve().parent.parent
INDEX = RADICE / "index.html"
SITEMAP = RADICE / "sitemap.xml"
INIZIO, FINE = "<!-- CALENDARIO:INIZIO -->", "<!-- CALENDARIO:FINE -->"

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
        "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
GG = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
BYDAY = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


# ---------- lettura del file .ics ----------

def leggi_ics(testo):
    testo = testo.replace("\r\n", "\n")
    testo = re.sub(r"\n[ \t]", "", testo)  # righe spezzate
    eventi = []
    for blocco in testo.split("BEGIN:VEVENT")[1:]:
        blocco = blocco.split("END:VEVENT")[0]
        campi = {}
        for riga in blocco.split("\n"):
            if ":" not in riga:
                continue
            chiave, valore = riga.split(":", 1)
            nome, *parametri = chiave.split(";")
            campi.setdefault(nome, []).append((parametri, valore))
        eventi.append(campi)
    return eventi


def testo_ics(valore):
    valore = (valore.replace("\\n", "\n").replace("\\N", "\n")
              .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\"))
    valore = re.sub(r"<br\s*/?>|</p>", "\n", valore, flags=re.I)  # Google a volte salva HTML
    valore = re.sub(r"<[^>]+>", "", valore)
    valore = html.unescape(valore)
    return re.sub(r"\s+", " ", valore).strip()


def data_ics(campo):
    """Restituisce (date, time|None) nel fuso di Roma."""
    parametri, valore = campo
    if "VALUE=DATE" in parametri or len(valore) == 8:
        return datetime.strptime(valore[:8], "%Y%m%d").date(), None
    if valore.endswith("Z"):
        dt = datetime.strptime(valore, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    else:
        tz = TZ
        for p in parametri:
            if p.startswith("TZID="):
                try:
                    tz = ZoneInfo(p[5:])
                except Exception:
                    pass
        dt = datetime.strptime(valore, "%Y%m%dT%H%M%S").replace(tzinfo=tz)
    dt = dt.astimezone(TZ)
    return dt.date(), dt.time()


def primo(campi, nome):
    return campi[nome][0] if nome in campi else None


def date_escluse(campi):
    escluse = set()
    for parametri, valore in campi.get("EXDATE", []):
        for v in valore.split(","):
            escluse.add(data_ics((parametri, v))[0])
    return escluse


# ---------- modello ----------

def privato(campi):
    """Eventi da non mostrare: [PRIVATO] nel titolo, oppure visibilità "privata" in Google Calendar
    (nel feed pubblico arrivano come CLASS:PRIVATE o con il solo titolo "Busy"/"Occupato")."""
    titolo = testo_ics(campi["SUMMARY"][0][1])
    if "[PRIVATO]" in titolo.upper():
        return True
    if "CLASS" in campi and campi["CLASS"][0][1].upper() in ("PRIVATE", "CONFIDENTIAL"):
        return True
    return titolo.lower() in ("busy", "occupato", "occupata")


def prepara(eventi_ics):
    singoli, settimanali = [], []
    cancellati = {}  # uid -> date annullate di una serie
    for c in eventi_ics:
        if "RECURRENCE-ID" in c and "STATUS" in c and c["STATUS"][0][1] == "CANCELLED":
            cancellati.setdefault(c["UID"][0][1], set()).add(data_ics(c["RECURRENCE-ID"][0])[0])
    for c in eventi_ics:
        if "DTSTART" not in c or "SUMMARY" not in c:
            continue
        if "STATUS" in c and c["STATUS"][0][1] == "CANCELLED":
            continue
        if privato(c):
            continue
        if "RECURRENCE-ID" in c:
            continue  # modifica di una singola ripetizione: la serie basta
        giorno, inizio = data_ics(primo(c, "DTSTART"))
        fine = data_ics(primo(c, "DTEND"))[1] if "DTEND" in c else None
        ev = {
            "uid": c["UID"][0][1] if "UID" in c else "",
            "titolo": testo_ics(c["SUMMARY"][0][1]),
            "desc": testo_ics(c["DESCRIPTION"][0][1]) if "DESCRIPTION" in c else "",
            "giorno": giorno, "inizio": inizio, "fine": fine,
        }
        if "RRULE" in c:
            regola = dict(p.split("=", 1) for p in c["RRULE"][0][1].split(";") if "=" in p)
            if regola.get("FREQ") != "WEEKLY":
                print(f"Avviso: ripetizione non settimanale ignorata per {ev['titolo']!r}", file=sys.stderr)
                continue
            fino = None
            if "UNTIL" in regola:
                fino = data_ics(([], regola["UNTIL"]))[0]
            giorni = [BYDAY[d[-2:]] for d in regola.get("BYDAY", "").split(",") if d[-2:] in BYDAY] or [giorno.weekday()]
            ev.update(giorni=sorted(giorni), fino=fino,
                      escluse=date_escluse(c) | cancellati.get(ev["uid"], set()))
            settimanali.append(ev)
        else:
            singoli.append(ev)
    settimanali.sort(key=lambda s: (s["inizio"] or time(0), s["titolo"]))  # ordine stabile
    return singoli, settimanali


def corso_attivo(s, giorno):
    return (giorno.weekday() in s["giorni"] and giorno >= s["giorno"]
            and (s["fino"] is None or giorno <= s["fino"]) and giorno not in s["escluse"])


# ---------- HTML ----------

e = lambda s: html.escape(s, quote=True)


def ora(t):
    return t.strftime("%H:%M")


def orario(ev, data=None):
    if ev["inizio"] is None:
        return ""
    pre = f"{data.isoformat()}T" if data else ""
    out = f'<time datetime="{pre}{ora(ev["inizio"])}">{ora(ev["inizio"])}</time>'
    if ev["fine"] and ev["fine"] != ev["inizio"]:
        out += f' - <time datetime="{pre}{ora(ev["fine"])}">{ora(ev["fine"])}</time>'
    return f'<span class="ora">{out}</span>'


def box_settimanali(settimanali, oggi):
    attivi = [s for s in settimanali if s["fino"] is None or s["fino"] >= oggi]
    righe = []
    for s in attivi:
        for g in s["giorni"]:
            righe.append((g, s["inizio"] or time(0), s))
    if not righe:
        return ""
    righe.sort(key=lambda r: (r[0], r[1]))
    li = "\n".join(
        f'<li class="corso"><span>{GIORNI[g]} · {e(s["titolo"])}</span> {orario(s)}</li>'
        for g, _, s in righe)
    return f'<div class="ricorrenze">\n<p class="etichetta">Ogni settimana</p>\n<ul>\n{li}\n</ul>\n</div>\n'


def mese_html(anno, mese, singoli, settimanali, aperto):
    primo_giorno = date(anno, mese, 1)
    ultimo = (date(anno + mese // 12, mese % 12 + 1, 1) - timedelta(days=1)).day
    del_mese = sorted((ev for ev in singoli if (ev["giorno"].year, ev["giorno"].month) == (anno, mese)),
                      key=lambda ev: (ev["giorno"], ev["inizio"] or time(0), ev["titolo"]))
    ids, per_giorno = {}, {}
    for ev in del_mese:
        base = f"ev-{ev['giorno'].isoformat()}"
        n = sum(1 for v in ids.values() if v.startswith(base))
        ids[id(ev)] = base if n == 0 else f"{base}-{n + 1}"
        per_giorno.setdefault(ev["giorno"].day, []).append(ev)

    celle = [""] * primo_giorno.weekday()
    for d in range(1, ultimo + 1):
        giorno = date(anno, mese, d)
        corsi = [s["titolo"] for s in settimanali if corso_attivo(s, giorno)]
        if d in per_giorno:
            nomi = [ev["titolo"] for ev in per_giorno[d]] + corsi
            celle.append(f'<td class="evento"><a href="#{ids[id(per_giorno[d][0])]}">{d}'
                         f'<span class="vh"> - {e(", ".join(nomi))}</span></a></td>')
        elif corsi:
            celle.append(f'<td class="corso">{d}<span class="vh"> - {e(", ".join(corsi))}</span></td>')
        else:
            celle.append(f"<td>{d}</td>")
    celle += [""] * (-len(celle) % 7)
    righe = ["<tr>" + "".join(c or "<td></td>" for c in celle[i:i + 7]) + "</tr>" for i in range(0, len(celle), 7)]

    intest = "".join(f'<th scope="col"><abbr title="{GIORNI[i].lower()}">{GG[i]}</abbr></th>' for i in range(7))
    hid = f"mese-{anno}-{mese:02d}"
    out = [f'<details class="mese"{" open" if aperto else ""}>',
           f'<summary><h3 id="{hid}">{MESI[mese - 1]} {anno}</h3></summary>',
           '<div class="voce">',
           f'<table class="griglia" aria-labelledby="{hid}">',
           f"<thead><tr>{intest}</tr></thead>",
           "<tbody>", *righe, "</tbody>", "</table>"]
    if del_mese:
        out += ["", '<ul class="eventi">']
        for ev in del_mese:
            g = ev["giorno"]
            dettagli = f'<span class="titolo">{e(ev["titolo"])}</span>'
            riga = " · ".join(x for x in [orario(ev, g), e(ev["desc"])] if x)
            if riga:
                dettagli += f'<span class="desc">{riga}</span>'
            out.append(f'<li class="evento" id="{ids[id(ev)]}"><time class="data" datetime="{g.isoformat()}">'
                       f'<span class="gg">{GG[g.weekday()]}</span><span class="n">{g.day}</span></time> '
                       f"<span>{dettagli}</span></li>")
        out.append("</ul>")
    out += ["</div>", "</details>"]
    return "\n".join(out)


def genera(singoli, settimanali, oggi):
    corrente = (oggi.year, oggi.month)
    futuri = [(ev["giorno"].year, ev["giorno"].month) for ev in singoli if (ev["giorno"].year, ev["giorno"].month) >= corrente]
    ultimo = max(futuri, default=corrente)
    mesi, (a, m) = [], corrente
    while (a, m) <= ultimo and len(mesi) < MESI_MAX:
        mesi.append((a, m))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)

    parti = [box_settimanali(settimanali, oggi)]
    parti.append('<ul class="legenda etichetta" aria-hidden="true">\n<li class="evento">Evento</li>\n'
                 '<li class="corso">Appuntamento settimanale</li>\n</ul>\n')
    parti.append('<div class="mesi">\n' + "\n\n".join(
        mese_html(a, m, singoli, settimanali, (a, m) == corrente) for a, m in mesi) + "\n</div>")
    return "\n".join(p for p in parti if p)


def main():
    if len(sys.argv) > 1:
        testo = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        richiesta = urllib.request.Request(ICS_URL, headers={"User-Agent": "losbando-sito"})
        with urllib.request.urlopen(richiesta, timeout=30) as r:
            testo = r.read().decode("utf-8")
    if "BEGIN:VCALENDAR" not in testo:
        sys.exit("Il calendario scaricato non è un file iCal: index.html non modificato.")

    oggi = datetime.now(TZ).date()
    singoli, settimanali = prepara(leggi_ics(testo))
    blocco = genera(singoli, settimanali, oggi)

    pagina = INDEX.read_text(encoding="utf-8")
    if INIZIO not in pagina or FINE not in pagina:
        sys.exit("Segnaposto CALENDARIO:INIZIO/FINE non trovati in index.html.")
    prima, resto = pagina.split(INIZIO, 1)
    _, dopo = resto.split(FINE, 1)
    nuova = f"{prima}{INIZIO}\n{blocco}\n{FINE}{dopo}"
    if nuova == pagina:
        print("Calendario invariato.")
        return
    INDEX.write_text(nuova, encoding="utf-8")
    if SITEMAP.exists():
        s = SITEMAP.read_text(encoding="utf-8")
        SITEMAP.write_text(re.sub(r"<lastmod>.*?</lastmod>", f"<lastmod>{oggi.isoformat()}</lastmod>", s), encoding="utf-8")
    print(f"Calendario aggiornato: {len(singoli)} eventi, {len(settimanali)} appuntamenti settimanali.")


if __name__ == "__main__":
    main()
