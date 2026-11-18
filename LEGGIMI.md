# Sito di Lo Sbando - Centro Situazionale

Sito statico di una pagina, senza dipendenze né build: HTML e CSS in `index.html`, font e immagini in locale.
Colori, caratteri e logo seguono il manuale di identità di Lo Sbando (blu #004aad granuloso, crema, rosso solo nel logo; League Spartan e Bree Serif).

```
index.html        pagina unica (testi, calendario, contatti)
404.html          pagina di errore
img/              logo (lo-sbando-logo.png) e anteprima social (og-image.jpg)
fonts/            League Spartan 800 e Bree Serif, licenza SIL OFL
scripts/calendario.py              genera il calendario da Google Calendar
.github/workflows/calendario.yml   lo esegue ogni ora su GitHub
favicon.ico, favicon-192.png, apple-touch-icon.png   icone (la S)
```

## Pubblicare con GitHub Pages

1. Crea un repository su GitHub (per esempio `losbando-sito`) e carica il contenuto di questa cartella.
2. Nel repository: Settings > Pages > Source: "Deploy from a branch", branch `main`, cartella `/ (root)`.
3. Dominio: il file `CNAME` contiene già `losbando.it`. In Settings > Pages scrivi `losbando.it` in "Custom domain" e, quando il certificato è pronto, attiva "Enforce HTTPS".
4. DNS (dal pannello del registrar di losbando.it):
   - quattro record `A` per `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - un record `CNAME` per `www` verso `<tuo-utente-github>.github.io`

Canonical, `sitemap.xml` e `robots.txt` puntano già a `https://losbando.it/`. La data `<lastmod>` della sitemap la aggiorna lo script del calendario.

## Aggiornare il calendario

Il calendario del sito si aggiorna **da solo** dal Google Calendar pubblico "Lo Sbando". Non va modificato a mano: tutto ciò che sta tra `<!-- CALENDARIO:INIZIO -->` e `<!-- CALENDARIO:FINE -->` in `index.html` viene riscritto.

Come funziona:
- GitHub Actions esegue `scripts/calendario.py` ogni ora (GitHub a volte parte con qualche ora di ritardo). Se qualcosa è cambiato, fa un commit ("Calendario aggiornato da Google Calendar") e il sito si ripubblica.
- Per aggiornarlo subito: su GitHub apri **Actions > Aggiorna calendario > Run workflow**.
- Per provarlo sul computer: `python3 scripts/calendario.py`.

Cosa scrivere su Google Calendar:
- **Titolo**: breve, è il titolo sul sito.
- **Descrizione**: una sola riga che dice cosa succede davvero. Compare sotto il titolo, dopo l'orario.
- **Orario di inizio e fine**: compaiono come `19:30 - 21:00`. Un evento "tutto il giorno" compare senza orario.
- **Ripetizione settimanale** (corsi): l'evento va nel box "Ogni settimana" e i suoi giorni diventano quadrati a contorno nella griglia. Per chiudere un corso imposta una data di fine alla ripetizione.
- Gli eventi singoli diventano quadrati pieni nella griglia e righe nell'elenco del mese.
- Il sito mostra il mese corrente e i successivi che hanno eventi (al massimo 4).

Attenzione: il calendario è pubblico. Niente invitati, note interne o numeri di telefono negli eventi.

Siccome il bot fa commit su `main`, in GitHub Desktop premi sempre **Fetch origin** (e poi **Pull**) prima di modificare il sito.

## Regole di tono (dal manuale)

- "Lo Sbando", con articolo e S maiuscola. Sottotitolo: "Centro Situazionale".
- Titoli degli eventi brevi e giocosi, sotto una sola riga concreta. Dai del tu, imperativo per gli inviti.
- Date "Mer 4", orari `18:00 - 21:00`. Niente emoji, niente gergo istituzionale.
- Non aggiungere "APS" finché l'iscrizione al RUNTS non è completa.
