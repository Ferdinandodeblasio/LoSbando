# Sito di Lo Sbando - Centro Situazionale

Sito statico di una pagina, senza dipendenze né build: HTML e CSS in `index.html`, font e immagini in locale.
Colori, caratteri e logo seguono il manuale di identità di Lo Sbando (blu #004aad granuloso, crema, rosso solo nel logo; League Spartan e Bree Serif).

```
index.html        pagina unica (testi, calendario, contatti)
404.html          pagina di errore
img/              logo (lo-sbando-logo.png) e anteprima social (og-image.jpg)
fonts/            League Spartan 800 e Bree Serif, licenza SIL OFL
favicon-32.png, apple-touch-icon.png   icone dal bollino
```

## Pubblicare con GitHub Pages

1. Crea un repository su GitHub (per esempio `losbando-sito`) e carica il contenuto di questa cartella.
2. Nel repository: Settings > Pages > Source: "Deploy from a branch", branch `main`, cartella `/ (root)`.
3. Dominio: il file `CNAME` contiene già `losbando.it`. In Settings > Pages scrivi `losbando.it` in "Custom domain" e, quando il certificato è pronto, attiva "Enforce HTTPS".
4. DNS (dal pannello del registrar di losbando.it):
   - quattro record `A` per `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - un record `CNAME` per `www` verso `<tuo-utente-github>.github.io`

Canonical, `sitemap.xml` e `robots.txt` puntano già a `https://losbando.it/`. Quando aggiorni il calendario, cambia `<lastmod>` nella sitemap.

## Aggiornare il calendario

Il calendario funziona come quello di La Situazione: un elenco per mese (le informazioni) e una griglia (il riassunto). Tutto è in `index.html`, nella sezione `<section class="calendario">`.

### Aggiungere un evento

1. Nell'elenco `<ul class="eventi">` del mese, in ordine di data:

   ```html
   <li class="evento" id="ev-2026-12-06"><time class="data" datetime="2026-12-06"><span class="gg">Sab</span><span class="n">6</span></time> <span><span class="titolo">Titolo breve</span><span class="desc">Una riga che dice cosa succede davvero</span></span></li>
   ```

   La descrizione è facoltativa. Un orario si scrive così: `<span class="ora"><time datetime="2026-12-06T19:30">19:30</time> - <time datetime="2026-12-06T22:00">22:00</time></span>`.

2. Nella griglia, sostituisci la cella del giorno:

   ```html
   <td class="evento"><a href="#ev-2026-12-06">6<span class="vh"> - Titolo breve</span></a></td>
   ```

   L'`id` della riga e l'`href` della cella devono coincidere.

### Appuntamenti settimanali

- Nella griglia: `<td class="corso">8<span class="vh"> - yoga</span></td>` (quadrato a contorno).
- Aggiorna il box crema "Ogni settimana" in cima al calendario (periodo, giorni, orari).

### Aggiungere un mese

Copia un intero blocco `<details class="mese"> ... </details>`, cambia l'`id` del titolo (`mese-AAAA-MM`, usato anche da `aria-labelledby` della tabella) e ricostruisci la griglia: una riga `<tr>` per settimana, da lunedì a domenica, celle vuote `<td></td>` prima del giorno 1 e dopo l'ultimo.

Il mese corrente si apre da solo. Sposta comunque l'attributo `open` sul mese corrente: vale per chi ha JavaScript disattivato.

I mesi passati si possono tenere (chiusi) o cancellare.

## Regole di tono (dal manuale)

- "Lo Sbando", con articolo e S maiuscola. Sottotitolo: "Centro Situazionale".
- Titoli degli eventi brevi e giocosi, sotto una sola riga concreta. Dai del tu, imperativo per gli inviti.
- Date "Mer 4", orari `18:00 - 21:00`. Niente emoji, niente gergo istituzionale.
- Non aggiungere "APS" finché l'iscrizione al RUNTS non è completa.
