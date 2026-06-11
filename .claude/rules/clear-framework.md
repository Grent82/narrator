# C.L.E.A.R. Framework

Verbindliches Review- und Qualitätsframework fuer alle Agent-Rollen in diesem Repository.

## Kernprinzipien

Jeder Buchstabe steht fuer eine Dimension, in der KI-generierte oder implementierte Artefakte typischerweise versagen:

| Dimension | Fokus | Typische Schwachstellen |
|---|---|---|
| **C** - Correctness | Korrekte Logik, Fehlerbehandlung, Edge Cases | Semantische Fehler, fehlende Validierung, Happy-Path-Only |
| **L** - Libraries & Dependencies | Existenz und Kompatibilität von Packages | Halluzinierte Packages, falsche API-Versionen, Sicherheitslücken |
| **E** - Efficiency & Performance | Algorithmische Komplexität, Ressourcenmanagement | O(n²) statt O(n log n), redundante DB-Abfragen, Memory Leaks |
| **A** - Architecture Fit | Passung zur bestehenden Architektur und Modulgrenzen | UI/Route entscheidet ueber Kernlogik, ignorierte Schichtentrennung |
| **R** - Risks & Security | Sicherheitslücken, Input-Validierung, Credentials | SQL Injection, XSS, hartcodierte Secrets, fehlende Sanitization |

## Anwendung pro Agent-Rolle

### architect
- **C**: Datenfluesse und Transformationslogik auf Konsistenz pruefen
- **L**: Referenzierte Libraries auf Existenz und Version-Kompatibilität validieren
- **E**: Architekturentscheidungen auf Performance-Auswirkungen abklaeren
- **A**: Modulgrenzen, Schichtentrennung und Trade-offs explizit machen
- **R**: Architekturbedingte Risiken (Migrationen, Integrationsgrenzen) benennen

### developer
- **C**: Implementierung auf korrekte Logik und Fehlerfaelle pruefen
- **L**: Nur existierende, kompatible Packages importieren; Versionen in `requirements.txt` oder `pyproject.toml` validieren
- **E**: Ineffiziente Queries, Schleifen oder Ressourcenlecks vermeiden
- **A**: Code in bestehende Modulgrenzen (`api/`, `application/`, `infrastructure/`) einordnen
- **R**: Input-Validierung, Secrets-Handling und Sicherheitsimplikationen beachten

### fixer
- **C**: Bug-Ursache und -Korrektur auf korrekte Logik pruefen
- **L**: Keine neuen Dependencies einfuehren, es sei denn, sie sind zwingend erforderlich
- **E**: Bugfix darf Performance nicht verschlechtern
- **A**: Minimal-invasiv bleiben; keine Refactorings unter dem Deckmantel Bugfix
- **R**: Regression-Risiken und Sicherheitsauswirkungen der Korrektur benennen

### investigator
- **C**: Befunde klar zwischen Beobachtung, Hypothese und Ursache trennen
- **L**: Abhaengigkeiten zwischen Libraries bei Fehleranalysen beruecksichtigen
- **E**: Performance-Probleme als potenzielle Root Causes identifizieren
- **A**: Architekturbedingte Fehlerquellen (Grenzschnittstellen, Datenfluesse) pruefen
- **R**: Sicherheitsrelevante Ursachen priorisieren

### code-reviewer
- **C**: Korrektheit, Edge Cases, fehlende Fehlerbehandlung
- **L**: Importierte Packages existieren und sind kompatibel
- **E**: Algorithmische Komplexität, redundante Operationen
- **A**: Architektur-Adherenz, Design Patterns, Team-Standards
- **R**: Sicherheitslücken, Credentials, Input-Sanitization

### tester / test-writer
- **C**: Tests pruefen tatsaechlich das gewuenschte Verhalten
- **L**: Referenzierte Testdaten und Schnittstellen verfuegbar
- **E**: Keine redundanten Testfaelle; sinnvolle Coverage
- **A**: Tests folgen der Team-Teststrategie und -Struktur
- **R**: Sicherheits- und Negativtests vorhanden

### requirements-engineer
- **C**: Anforderungen stimmen mit Stakeholder-Aussagen ueberein
- **L**: Referenzierte Standards, Normen oder Systeme existieren
- **E**: Anforderungen präzise, nicht aufgebläht/redundant
- **A**: Passen in bestehende Systemlandschaft und Architektur
- **R**: Regulatorische oder Datenschutz-Risiken beruecksichtigt

### devops
- **C**: Konfigurationen und Skripte laufen ohne Fehler
- **L**: Referenzierte Images, Packages und Tools existieren und sind versioniert
- **E**: Ressourcenallokation (CPU, Memory, Disk) angemessen
- **A**: Infrastruktur passt zur bestehenden Deployment-Architektur
- **R**: Secrets-Handling, Netzwerkzugriffe, Zugriffskontrollen

### technical-writer
- **C**: Dokumentation entspricht dem tatsaechlichen Systemverhalten
- **L**: Referenzierte Tools, Befehle und Versionen korrekt
- **E**: Dokumentation präzise, nicht redundant oder ueberkompliziert
- **A**: Passt zur bestehenden Dokumentationsstruktur und -kultur
- **R**: Keine Secrets oder sensiblen Daten in Beispielen

## Verifikationsbefehle

```bash
# Package-Existenz prüfen (pip)
pip index versions <package-name>

# Package-Existenz prüfen (npm)
npm view <package-name>

# Version-Kompatibilität prüfen
pip show <package-name>
cat pyproject.toml | grep <package-name>

# Sicherheitslücken prüfen
pip-audit  # falls installiert
pip freeze | xargs pip check
```

## Meta-Regel

Das C.L.E.A.R. Framework ist **keine Checkliste zum Abhaken**, sondern eine **Denkstruktur**. Jeder Buchstabe steht fuer eine Dimension, in der KI-Outputs oder Implementierungen typischerweise versagen.

**Anwendung:**
- Bei Code-Reviews: Alle 5 Dimensionen systematisch durchgehen
- Bei Implementierungen: Jede Dimension aktiv bedenken
- Bei Fehleranalysen: Alle Dimensionen als potenzielle Ursachenquelle pruefen
- Bei Architektur-Entscheidungen: Trade-offs pro Dimension benennen
