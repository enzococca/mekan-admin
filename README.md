# MEKAN Archaeological Data Web Interface

Sistema web completo per la gestione e visualizzazione dei dati archeologici del progetto MEKAN/Kultepe.

## Funzionalità

### 🔍 Visualizzazione Dati
- **Stratigraphic Units (US)**: Visualizza e cerca unità stratigrafiche
- **MEKAN/CAN Units**: Gestione unità sistema turco
- **Finds Catalog**: Catalogo reperti archeologici
- **Mappe Interattive**: Visualizzazione spaziale con Leaflet
- **Statistiche**: Dashboard con grafici e analisi dati

### 📊 Export Dati
- Export Excel con formattazione
- Generazione PDF per singoli record
- API REST per integrazione con altri sistemi

### 🔐 Gestione Utenti
- Sistema di ruoli e permessi
- Autenticazione sicura
- Log attività utenti
- Token di invito per nuovi utenti

## Installazione

### Con Docker Compose (Consigliato)

```bash
cd admin_interface
docker-compose up -d
```

### Manuale

1. Installa dipendenze:
```bash
pip install -r requirements.txt
```

2. Configura variabili ambiente:
```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=hybrid_strat
export DB_USER=postgres
export DB_PASSWORD=postgres
```

3. Avvia applicazione:
```bash
python app.py
```

## Accesso

- URL: http://localhost:5001
- Username iniziale: `admin`
- Password iniziale: `admin123` (cambiarla al primo accesso)

## API Endpoints

### Dati Archeologici
- `GET /api/stratigraphic_units` - Lista US con filtri
- `GET /api/mekan_units` - Lista unità MEKAN
- `GET /api/finds` - Catalogo reperti
- `GET /api/relationships` - Relazioni stratigrafiche
- `GET /api/statistics` - Statistiche database
- `GET /api/spatial/features` - Dati GeoJSON per mappe

### Export
- `POST /api/export/excel` - Export Excel
- `POST /api/export/pdf` - Export PDF singolo record

### Ricerca
- `GET /api/search/global` - Ricerca globale

## Struttura Database

Il sistema si connette al database PostgreSQL/PostGIS esistente con le seguenti tabelle principali:
- `stratigraphic_units` - Unità stratigrafiche
- `mekan_data` - Dati sistema MEKAN/CAN
- `finds_catalog` - Catalogo reperti
- `stratigraphic_relationships` - Relazioni tra US
- `system_users` - Utenti sistema
- `user_roles` - Ruoli e permessi

## Personalizzazione

### Aggiungere nuovi campi
Modifica `api_routes.py` per includere nuovi campi nelle query.

### Modificare visualizzazione
Aggiorna i template HTML in `templates/` per personalizzare l'interfaccia.

### Estendere API
Aggiungi nuovi endpoint in `api_routes.py` per funzionalità aggiuntive.

## Sicurezza

- Password hashate con bcrypt
- Sessioni sicure con Flask-Login
- CSRF protection
- Validazione input
- Permessi basati su ruoli

## Troubleshooting

### Errore connessione database
Verifica che PostgreSQL sia in esecuzione sulla porta configurata e che le credenziali siano corrette.

### Errore import moduli
Assicurati di aver installato tutte le dipendenze: `pip install -r requirements.txt`

### Docker: host.docker.internal non funziona
Su Linux, usa l'IP della macchina host invece di `host.docker.internal`.

## Sviluppo

Per modalità sviluppo con auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## License

Progetto interno per uso archeologico.