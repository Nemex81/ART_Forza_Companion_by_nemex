"""
Piano di sviluppo **aggiornato e completo**, includendo l’ultimo dettaglio: selezione lingua da opzioni con modalità “salva e richiede riavvio” come ultimo commit. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]

## Obiettivo generale
Rifattorizzare `ART_Forza_Companion.py` per usare key stabili (non testi UI) per stato/config, applicare la localizzazione usando i JSON già presenti in `localization/en.json` e `localization/it.json`, mantenere compatibilità con vecchi `config.json`, e aggiungere un selettore lingua in UI che salva la preferenza e richiede riavvio. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:2]

## Commit 1 — Core i18n loader (`tr()`)
**Scopo:** introdurre il caricamento delle traduzioni senza cambiare ancora la struttura dei dizionari/chiavi interne. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include:
- aggiungere detection lingua di sistema (prefisso `it` → IT, altrimenti EN). [mcp_tool_github-mcp-direct_get_file_contents:0]
- `load_translations(lang)` che legge `localization/{lang}.json` e fallback su `en`. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]
- `tr(key, **kwargs)` con fallback “ritorna key se manca” + `.format(**kwargs)` safe. [mcp_tool_github-mcp-direct_get_file_contents:0]

Risultato atteso:
- Il programma può chiamare `tr("ui.app_title")` senza crash. [mcp_tool_github-mcp-direct_get_file_contents:0]

## Commit 2 — Key stabili + migrazione config
**Scopo:** eliminare la dipendenza dalle stringhe UI come chiavi interne e rendere il `config.json` robusto. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include:
- definire `TOGGLE_KEYS`, `SETTING_KEYS`, `AUDIO_COMPASS_OPTION_KEYS` coerenti con i file JSON (es. `toggle.audio.speed`, `setting.speed.interval`, `option.audio_compass.off`, ecc.). [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]
- introdurre mapping di migrazione:
  - da `"Speed Audio Toggle"` → `"toggle.audio.speed"`, ecc.
  - da `"Speed Interval"` → `"setting.speed.interval"`, ecc. [mcp_tool_github-mcp-direct_get_file_contents:0]
- aggiornare `load_configuration()` per:
  - leggere vecchio formato,
  - migrare chiavi a key stabili,
  - garantire default per chiavi mancanti. [mcp_tool_github-mcp-direct_get_file_contents:0]
- aggiornare `save_configuration()` in modo che salvi dizionari **con key stabili** (anche se mantieni per compatibilità i nomi `dict1/dict2/int_value`). [mcp_tool_github-mcp-direct_get_file_contents:0]

Risultato atteso:
- Nessun KeyError anche con `config.json` vecchio o parziale. [mcp_tool_github-mcp-direct_get_file_contents:0]

## Commit 3 — GUI localizzata (key interne + testo via `tr()`)
**Scopo:** la UI deve mostrare testi tradotti, ma la logica deve lavorare solo con key stabili. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include:
- `setWindowTitle(tr("ui.app_title"))`. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]
- titoli tab con `tr("ui.tab.audio_toggles")` e `tr("ui.tab.sensitivity")`. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:2]
- bottoni: iterare `TOGGLE_KEYS`, creare `QPushButton(tr(key))`, callback passa `key`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- edit box: iterare `SETTING_KEYS`, `QLabel(tr(key))`, `setAccessibleName(tr(key))`, memorizzare l’edit in `value_variables[key]`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- submit button: `tr("ui.button.submit")`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- combo bussola: `addItems([tr(k) for k in AUDIO_COMPASS_OPTION_KEYS])`. [mcp_tool_github-mcp-direct_get_file_contents:0]

Risultato atteso:
- UI tradotta correttamente in base alla lingua caricata. [mcp_tool_github-mcp-direct_get_file_contents:1][mcp_tool_github-mcp-direct_get_file_contents:2]

## Commit 4 — Localizzazione TTS/SR + direzioni
**Scopo:** eliminare stringhe hardcoded in output vocale e nelle direzioni bussola. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include:
- sostituire tutti i `speak("...")` / `print_Speak(..., "...")` con `tr("tts....")` usando placeholder dove serve (`gear`, `limit`, `left`, `right`, `mode`). [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]
- `convertDir()` deve restituire `tr("dir.north")` ecc., e `tr("dir.invalid")` se fuori range. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:2]
- `audio_compass_changed()` deve usare `tr("tts.compass_mode_changed", mode=tr(option_key))`. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:2]

Risultato atteso:
- Output vocale coerente con lingua. [mcp_tool_github-mcp-direct_get_file_contents:0]

## Commit 5 — Pulizia e bugfix
**Scopo:** sistemare bug evidenti e uniformare la nuova struttura. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include (minimo):
- correggere il refuso `configuration_value` → `configuration_values` (oggi rompe “Rear Tire Temp”). [mcp_tool_github-mcp-direct_get_file_contents:0]
- rifinire `updateVars()` e la logica affinché usi solo key stabili (`toggle.*` / `setting.*`). [mcp_tool_github-mcp-direct_get_file_contents:0]
- sistemare eventuali incoerenze emerse durante test (senza cambiare feature). [mcp_tool_github-mcp-direct_get_file_contents:0]

Risultato atteso:
- nessun errore runtime nel loop principale, e salvataggio/caricamento ok. [mcp_tool_github-mcp-direct_get_file_contents:0]

## Commit 6 — Opzioni lingua (salva + richiede riavvio)
**Scopo:** aggiungere la scelta lingua da UI (IT/EN) e salvarla nel config, senza aggiornare la UI live. [mcp_tool_github-mcp-direct_get_file_contents:0]

Cosa include:
- aggiungere un selettore lingua (es. `QComboBox`) nel tab “Audio & Toggles”. [mcp_tool_github-mcp-direct_get_file_contents:0]
- aggiungere supporto in config:
  - `language` può essere `"it"`, `"en"` o assente/null (nessuna scelta). [mcp_tool_github-mcp-direct_get_file_contents:0]
  - logica avvio:
    - se `language` è presente e valida → carica quella
    - altrimenti usa la lingua di sistema (regola: italiano se locale inizia per `it`, altrimenti inglese). [mcp_tool_github-mcp-direct_get_file_contents:0]
- quando l’utente cambia lingua in UI:
  - aggiornare `language` nel config e salvarlo
  - annunciare un messaggio “riavvio richiesto” (TTS). [mcp_tool_github-mcp-direct_get_file_contents:0]
- aggiungere nuove stringhe nei JSON:
  - `tts.restart_required` in EN e IT (poiché al momento non esiste nei file). [mcp_tool_github-mcp-direct_get_file_contents:1][mcp_tool_github-mcp-direct_get_file_contents:2]

Risultato atteso:
- selezione lingua persistente e applicata al prossimo avvio; UI non si aggiorna subito, ma comunica chiaramente che serve riavvio. [mcp_tool_github-mcp-direct_get_file_contents:0]

"""