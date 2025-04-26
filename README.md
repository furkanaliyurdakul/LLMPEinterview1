# Personalized Learning Platform

A self‑contained Streamlit app for our KU Leuven study on AI‑generated learning explanations.  
All session data are stored pseudonymously so that results can be analysed without linking them to a real identity.

---
## Directory structure

Each time a participant opens the app a new _session directory_ is created under **`output/`**:

```
output/
  ├── 20250427_120345_Alex_Smith/   # <timestamp>_<fake-name>
  │   ├── profile/                  # uploaded & parsed student profile
  │   ├── knowledge_test/           # quiz results
  │   ├── learning_logs/            # tutor‑chat logs
  │   ├── ueq/                      # UEQ answers + benchmark
  │   └── meta/                     # page‑timer JSON, etc.
  └── …
```

### Pseudonymisation in a nutshell
1. When `SessionManager` starts it creates the session ID `(timestamp + fake name)` and writes it to `output/…/condition.txt`.
2. A **pseudonymised** copy of the profile replaces the real name with the fake name.  Down‑stream components read only this copy.
3. All later artefacts (chat logs, test results, UEQ) live in the same folder and therefore inherit the fake identifier.

---
## Key components
| file | role |
|------|------|
| `main.py` | navigation, page timer, session wiring |
| `Gemini_UI.py` | personalised/generic tutor UI & helpers |
| `session_manager.py` | directory & pseudonym handling |
| `personalized_learning_logger.py` | buffered file logger for tutor interactions |
| `testui_profilesurvey.py` | student‑profile questionnaire |
| `testui_knowledgetest.py` | 5‑item multiple‑choice quiz |
| `testui_ueqsurvey.py` | 26‑item UEQ short form + benchmark |
| `page_timer.py` | per‑page dwell‑time measurement |

---
## Selecting the study condition *(personalised vs generic)*

Participants must **not** know which branch they get.  
The choice is therefore made in **code, not in the UI**.

```python
# main.py – near the top
DEFAULT_PERSONALISED: bool = True  # True → personalised, False → generic
```

1. Set the flag, save the file, restart the Streamlit server.
2. The flag is copied into `st.session_state["use_personalisation"]` and cached for the whole run.
3. `SessionManager` writes the chosen condition to `output/…/condition.txt` so it is visible during analysis.

*Tip:* when `DEV_MODE = True` you can still uncomment the old facilitator radio‑button to flip the condition interactively while testing.

---
## Running the app

```bash
# (optional) create a fresh virtual environment
python -m venv .venv && source .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# launch the Streamlit server
streamlit run main.py

# (optional) expose it externally
ngrok http 8501     # copy the forwarded URL for your participants
```

All uploads and logs appear under **`output/`** immediately.  
After the session you can zip that folder for further analysis.
