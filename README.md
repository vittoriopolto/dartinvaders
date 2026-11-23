# DartsInvaders

Sito Django per tracciare i risultati dei campionati di freccette a squadre.
Home con la classifica dei giocatori, elenco partite, dettaglio e modifica dei risultati.

## Installazione in locale

macOS / Linux:

```bash
cd dartsinvaders
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Windows (PowerShell):

```powershell
cd dartsinvaders
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Poi apri http://127.0.0.1:8000, clicca "Accedi" con l'utente creato e prova a
caricare il referto di esempio (`esempio_referto.txt`).

## Come funziona

1. Carichi la foto del referto su Claude e ti fai restituire il testo nel formato standard.
2. In "Carica referto" incolli il testo e premi "Controlla il referto": vedi l'anteprima e gli eventuali avvisi.
3. Premi "Salva il referto". Se la partita (stesso campionato e stesso numero) esiste già, viene sostituita.
4. Se trovi un errore, apri la partita e usa "Modifica risultati".

Giocatori e squadre vengono creati da soli al primo referto. Il giocatore si riconosce dal
numero di tessera. Per rinominare o correggere giocatori e squadre usa `/admin/`.

## Impostazioni (file .env)

- `OUR_TEAM_NAME`: nome della tua squadra come scritto nei referti (default: Dart Invaders).
- `DATABASE_URL`: se manca, in locale si usa SQLite. Per usare Neon incolla la stringa di connessione.

Consiglio: in locale lascia SQLite, così i test non finiscono nel database vero.
Le migrazioni (cartella `core/migrations`) vanno committate su Git, servono al deploy.
