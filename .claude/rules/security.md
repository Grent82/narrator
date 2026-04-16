# Security Rules

- Keine Tokens, Secrets, Passwoerter oder produktionsnahe Zugangsdaten in Antworten, Logs oder Commits aufnehmen.
- Dateien wie `.env`, `*.pem`, `*.key` und vergleichbare Secret-Dateien nur mit expliziter Notwendigkeit bearbeiten.
- Sensible Daten nicht in Debug-Ausgaben oder Fehlertexten ausgeben.
- Bei Unsicherheit ueber Secret-Handling konservativ handeln und erst blockieren oder nachfragen.
