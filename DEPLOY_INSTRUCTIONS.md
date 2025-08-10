# Istruzioni per Deploy su Render

## 1. Pubblica su GitHub

Apri il terminale ed esegui questi comandi:

```bash
cd /Users/enzo/Desktop/SYSTEM_Hybrid_Kultepe/admin_interface

# Il repository git è già inizializzato e il commit è fatto
# Ora devi solo pushare su GitHub:

# Opzione 1: Se hai GitHub CLI installato
gh repo create mekan-admin --public --source=. --remote=origin --push

# Opzione 2: Se usi SSH
git remote remove origin
git remote add origin git@github.com:enzococca/mekan-admin.git
git push -u origin main

# Opzione 3: Se usi HTTPS con token
# Prima crea il repository su https://github.com/new
# Nome: mekan-admin
# Poi:
git remote remove origin
git remote add origin https://github.com/enzococca/mekan-admin.git
git push -u origin main
# Ti chiederà username (enzococca) e password (usa un Personal Access Token)
```

## 2. Deploy su Render

1. Vai su https://render.com e registrati/accedi
2. Clicca su "New +" → "Web Service"
3. Connetti il tuo account GitHub se non l'hai già fatto
4. Cerca e seleziona il repository `mekan-admin`
5. Render rileverà automaticamente il file `render.yaml` con tutte le configurazioni
6. Clicca su "Create Web Service"

## 3. URL della tua App

Dopo il deploy (circa 3-5 minuti), la tua app sarà disponibile su:
```
https://mekan-admin.onrender.com
```
(o un URL simile che Render ti assegnerà)

## 4. Accesso

- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANTE**: Cambia la password admin dopo il primo accesso!

## Cosa è già configurato:

✅ Database Supabase (già connesso)
✅ Tutte le variabili d'ambiente nel `render.yaml`
✅ Server Gunicorn per produzione
✅ Python 3.11.6
✅ Tutte le dipendenze necessarie

## Funzionalità disponibili online:

- 📊 Dashboard con statistiche
- 👥 Gestione utenti e ruoli
- 🏛️ Dati archeologici (MEKAN, Birim, Walls, Graves, Finds)
- 🔗 Navigazione relazioni padre-figlio
- 🖼️ Indicatori media colorati (verde = ha foto, grigio = senza foto)
- 📈 Grafici e visualizzazioni
- 🗺️ Mappe con Leaflet
- 📝 Log attività

## Note:

- Il piano gratuito di Render include 750 ore/mese
- L'app va in sleep dopo 15 minuti di inattività
- Si risveglia automaticamente alla prima richiesta (può impiegare 30-60 secondi)
- I dati sono già nel database Supabase, quindi saranno immediatamente visibili