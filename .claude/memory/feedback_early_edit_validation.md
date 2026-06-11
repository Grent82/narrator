---
name: feedback_early_edit_validation
description: Vor Edit Datei lesen wenn String-Match kritisch ist
metadata:
  type: feedback
---

**Warum:** In dieser Session war ein Edit-Fehler weil der Return-Type in `story_routes.py` anders war als erinnert (`StoryGenerateJobResponse` vs `StoryGenerateResponse`). Der Edit-Versuch schlug fehl, ein Read danach zeigte den korrekten Zustand.

**How to apply:**
- Vor Edit von Routes/Endpoints: Immer erst kurz Read um Return-Typen zu verifizieren
- Bei Edit-Fehlern: Nicht sofort retry, sondern Read zur Diagnose
- Besonders bei API-Responses: Typen können abweichen

**Link zu:** [[feedback_no_assumptions]]
