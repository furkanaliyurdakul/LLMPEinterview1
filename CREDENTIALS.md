# Platform Credentials

This document contains the login credentials for the AI Learning Platform.

## Participant Credentials

### Personalised Learning Cohort
- **Username:** `Participant1`
- **Password:** `Participant1`
- **Study Condition:** Personalised learning experience
- **Features:** Standard participant interface (no session info displayed)

### Generic Learning Cohort  
- **Username:** `Participant2`
- **Password:** `Participant2`
- **Study Condition:** Generic learning experience
- **Features:** Standard participant interface (no session info displayed)

## Non-Participant Credentials

### Development Mode
- **Username:** `dev`
- **Password:** `dev`
- **Features:** 
  - Full development access
  - File upload capabilities
  - Development tools enabled
  - Session info displayed in sidebar

### Fast Test Mode
- **Username:** `fasttest`
- **Password:** `fasttest`
- **Features:**
  - Quick tutorial/demo mode
  - Fast test mode active
  - Session info displayed in sidebar

### Development + Fast Test Mode
- **Username:** `devfast`
- **Password:** `devfast`
- **Features:**
  - Combined development and fast test mode
  - All development features enabled
  - Fast test mode active
  - File upload capabilities
  - Session info displayed in sidebar

## Data Organization

Session data is organized by credential type:

```
output/
├── personalised_cohort/          # Participant1 sessions
├── generic_cohort/               # Participant2 sessions
├── dev_testing/                  # dev credential sessions
├── demo_testing/                 # fasttest credential sessions
└── dev_fast_testing/            # devfast credential sessions
```

## Usage Notes

- **Participants** (Participant1, Participant2): Experience a clean interface without technical session information
- **Non-participants** (dev, fasttest, devfast): See session information and have access to additional features
- Fast test mode is now activated only through credentials, not manual buttons
- Development mode enables file upload functionality and development tools

## Security

- All passwords are hashed with platform-specific salt
- Session management is handled automatically
- Credentials determine access level and feature availability
- Data is organized by credential type for proper separation

---
**⚠️ Important:** Keep this file secure and do not commit it to version control.