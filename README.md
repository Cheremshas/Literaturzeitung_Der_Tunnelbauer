# LiteraturZeitung – Der Tunnelbauer

## Lokaler Start
```bash
pip install flask
python app.py
# Öffne http://localhost:5000
```

## Railway Deployment

1. Lade alle Dateien in ein **GitHub-Repository** hoch
2. Gehe auf [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Wähle dein Repository
4. Setze eine **Umgebungsvariable**:
   - `ADMIN_PASSWORD` = dein Passwort (Standard: `tunnelbauer2025`)
5. Fertig! Railway deployed automatisch.

> **Wichtig für persistente Daten auf Railway:**
> Railway's Filesystem ist ephemeral (wird bei Restart gelöscht).
> Füge ein **Railway Volume** hinzu:
> - In deinem Railway-Projekt: + New → Volume
> - Mount Path: `/app/data`
> - Ändere in `app.py`: `DB_PATH = '/app/data/data.db'`
> - Bilder-Ordner: `UPLOAD_FOLDER = '/app/data/uploads'`

## Dateien
- `app.py` – Flask-Server, alle API-Endpunkte
- `templates/index.html` – Frontend mit Admin-Modus
- `data.db` – SQLite-Datenbank (wird auto-erstellt)
- `static/uploads/` – Hochgeladene Bilder
- `requirements.txt` – Python-Pakete
- `Procfile` – Railway/Heroku Start-Befehl

## Admin-Funktionen
- **Login**: ⚙ Admin Button im Header
- **Texte bearbeiten**: Direkt auf der Seite klicken
- **Farben ändern**: 🎨 Button bei Zitaten, Themen, Interviews
- **Emoji wählen**: 😀 Button bei Themen-Icons
- **Bilder hochladen**: 📷 auf Buchcover oder Avatar klicken
- **Inhalte hinzufügen**: Buttons in der Admin-Leiste oben
- **Speichern**: Automatisch beim Verlassen eines Feldes
