Di seguito trovi una **nuova pianificazione correttiva** (come prompt per GitHub Coding Agent), pensata per rendere l’implementazione appena fatta “merge-ready”, risolvendo i 2 bug critici e aggiungendo hardening mirato senza cambiare feature. Riferimento: branch `copilot/refactor-main-application`, file principale `ART_Forza_Companion.py`. [mcp_tool_github-mcp-direct_get_file_contents:0][mcp_tool_github-mcp-direct_get_file_contents:1]

***

## Prompt istruzioni (fix plan) per GitHub Coding Agent

### Repo e contesto
- Repo: `Nemex81/ART_Forza_Companion_by_nemex`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- Branch di lavoro: crea un branch di fix (es. `fix/post-copilot-hardening`) **a partire da** `copilot/refactor-main-application`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- File da modificare principalmente:
  - `ART_Forza_Companion.py` (fix logica + robustezza). [mcp_tool_github-mcp-direct_get_file_contents:0]
- File di localizzazione: non dovrebbero richiedere ulteriori cambi, perché `tts.restart_required` e le opzioni lingua sono già presenti; verifica soltanto che restino integri. [mcp_tool_github-mcp-direct_get_file_contents:0]

### Obiettivo
Correggere in modo professionale e definitivo:
1) Bug critico: commistione tra `QLineEdit` e `int` dentro `value_variables` (stato settings instabile + rischio serializzazione). [mcp_tool_github-mcp-direct_get_file_contents:0]  
2) Bug critico: logica confronto velocità con `preSpeed` che rende impossibile rilevare aumento e falsa la gestione di `curSpeedInt`. [mcp_tool_github-mcp-direct_get_file_contents:0]  

In più: rafforzare la robustezza di path e input/clamp, senza cambiare il comportamento funzionale desiderato. [mcp_tool_github-mcp-direct_get_file_contents:0]

***

## Commit 1 — Fix architettura settings (separare UI da dati)
### Problema da risolvere
Nel codice corrente `value_variables` viene prima trattato come dict di int (settings), poi viene sovrascritto con widget `QLineEdit` in `add_edit_panel()`, e poi ancora viene sostituito con `int` in `submit_values()`, creando uno stato ibrido che rompe `updateVars()` e rischia incoerenze nel salvataggio. [mcp_tool_github-mcp-direct_get_file_contents:0]

### Implementazione richiesta
1) Introdurre due strutture distinte:
- `configuration_values: dict[str, int]` → **solo** valori numerici (sempre serializzabile). [mcp_tool_github-mcp-direct_get_file_contents:0]
- `setting_edits: dict[str, QLineEdit]` → **solo** widget della UI. [mcp_tool_github-mcp-direct_get_file_contents:0]

2) Evitare che `configuration_values` venga “copiato” da un dict che poi conterrà widget.
- Dopo `load_configuration()` assegna direttamente:
  - `button_states, settings_from_config, audio_compass_selection, language_preference = load_configuration()`
  - `configuration_values = settings_from_config.copy()` (che è int-only). [mcp_tool_github-mcp-direct_get_file_contents:0]
- Elimina/abbandona l’uso di `value_variables` come contenitore unico (può essere rimosso del tutto o rimpiazzato da `setting_edits`). [mcp_tool_github-mcp-direct_get_file_contents:0]

3) Modificare `add_edit_panel()`:
- iterare **su `SETTING_KEYS`** (non su `value_variables.keys()`). [mcp_tool_github-mcp-direct_get_file_contents:0]
- per ogni key:
  - creare `edit = QLineEdit()`
  - `setting_edits[key] = edit`
  - `edit.setText(str(configuration_values.get(key, default_configuration_values()[key])))` [mcp_tool_github-mcp-direct_get_file_contents:0]
  - NON scrivere widget dentro `configuration_values`. [mcp_tool_github-mcp-direct_get_file_contents:0]

4) Modificare `submit_values()`:
- leggere **solo** dai widget: `edit = setting_edits[key]`. [mcp_tool_github-mcp-direct_get_file_contents:0]
- validare input (integro l’attuale logica `isdigit()`).
- aggiornare **solo** `configuration_values[key] = int(text)` se valido.
- mantenere la TTS esistente (`tts.invalid_integers` / `tts.all_values_set`). [mcp_tool_github-mcp-direct_get_file_contents:0]

5) Modificare `updateVars()`:
- non deve più controllare `isinstance(value_variables[key], int)`.
- deve leggere direttamente da `configuration_values[key]` (che sarà sempre `int`). [mcp_tool_github-mcp-direct_get_file_contents:0]

6) Salvataggio:
- il pulsante `action.config.save` deve salvare:
  - `button_states` (bool)
  - `configuration_values` (int)
  - `audio_compass_selection`
  - `language_preference` [mcp_tool_github-mcp-direct_get_file_contents:0]

### Acceptance criteria
- `configuration_values` contiene sempre e solo numeri (int).
- Nessun widget viene mai serializzato in `config.json`.
- Dopo aver aperto la UI e premuto “Applica”, `updateVars()` continua a funzionare. [mcp_tool_github-mcp-direct_get_file_contents:0]

***

## Commit 2 — Fix logica speed (preSpeed/curSpeedInt)
### Problema da risolvere
In `processPacket()`, la riga `preSpeed = curSpeed` viene eseguita prima del confronto `if curSpeed > preSpeed`, rendendo il ramo “speed increased” impossibile e falsando `curSpeedInt`. [mcp_tool_github-mcp-direct_get_file_contents:0]

### Implementazione richiesta
Sostituire il blocco della speed logic con una variante corretta e leggibile:

- calcolare `diff = curSpeed - preSpeed`
- se `abs(diff) >= speedSense`:
  - memorizzare `old_speed = preSpeed`
  - poi aggiornare `preSpeed = curSpeed`
  - incrementare o decrementare `curSpeedInt` in base a confronto con `old_speed`
  - gestire `speedMon` e suono una sola volta per evento
  - gestire `speedInterval` in modo robusto:
    - `speedInterval == 0` → annuncia sempre
    - `speedInterval > 0` → annuncia quando `curSpeedInt % speedInterval == 0` [mcp_tool_github-mcp-direct_get_file_contents:0]

### Acceptance criteria
- `curSpeedInt` aumenta quando la velocità aumenta oltre soglia e diminuisce quando cala oltre soglia.
- Le letture di velocità rispettano `speedInterval` e `speedSense`. [mcp_tool_github-mcp-direct_get_file_contents:0]

***

## Commit 3 — Hardening path e clamp (robustezza)
Questo commit non deve cambiare feature, solo eliminare fragilità note. [mcp_tool_github-mcp-direct_get_file_contents:0]

### A) Path robusti (localization + config)
Problema: `load_translations()` usa `os.getcwd()`, quindi se l’app è avviata da una working directory diversa, non trova `localization/*.json`. [mcp_tool_github-mcp-direct_get_file_contents:0]

Fix:
- definire una costante:
  - `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`
- usare `BASE_DIR` per:
  - `localization/en.json`
  - `localization/{lang}.json`
  - opzionale (consigliato): anche `config.json` (così vive vicino allo script/exe). [mcp_tool_github-mcp-direct_get_file_contents:0]

### B) Clamp `audio_compass_selection`
Problema: `audio_compass_selection` letto dal config può essere fuori range; poi si usa come indice su `audio_compass_options[index]`. [mcp_tool_github-mcp-direct_get_file_contents:0]

Fix:
- dopo conversione a int:
  - `audio_compass_value = max(0, min(audio_compass_value, len(AUDIO_COMPASS_OPTION_KEYS)-1))` [mcp_tool_github-mcp-direct_get_file_contents:0]

### C) Minor: ridurre warning locale (facoltativo)
`locale.getdefaultlocale()` può generare warning su Python recenti; facoltativo sostituire con `locale.getlocale()` o altra strategia compatibile, ma senza introdurre dipendenze. [mcp_tool_github-mcp-direct_get_file_contents:0]

### Acceptance criteria
- Avvio da qualunque cartella: localization viene trovata correttamente.
- Nessun IndexError sul combo bussola anche con config corrotto. [mcp_tool_github-mcp-direct_get_file_contents:0]

***

## Nota finale (non cambiare)
- La scelta lingua deve rimanere “salva e richiede riavvio”, quindi **non** implementare refresh live UI in questi fix. [mcp_tool_github-mcp-direct_get_file_contents:0]

***

Se confermi, posso anche convertire questo piano in una versione “super sintetica” (solo checklist di azioni) da incollare direttamente nella task di Copilot/GitHub agent. Vuoi anche quella?