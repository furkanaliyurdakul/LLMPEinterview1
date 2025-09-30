# Authentication Credentials Reference

## Study Participant Credentials

### Personalised Learning Cohort
- **Username:** `personalised_p001` | **Password:** `PersonalisedCohort2025!`
- **Username:** `personalised_p002` | **Password:** `PersonalisedCohort2025!`  
- **Username:** `personalised_p003` | **Password:** `PersonalisedCohort2025!`

**Configuration:**
- Study condition: Personalised explanations
- Data folder: `personalised_cohort/`
- Dev mode: ❌ | Fast test: ❌ | Upload enabled: ❌

### Generic Learning Cohort  
- **Username:** `generic_g001` | **Password:** `GenericCohort2025!`
- **Username:** `generic_g002` | **Password:** `GenericCohort2025!`
- **Username:** `generic_g003` | **Password:** `GenericCohort2025!`

**Configuration:**
- Study condition: Generic explanations  
- Data folder: `generic_cohort/`
- Dev mode: ❌ | Fast test: ❌ | Upload enabled: ❌

## Research Team Credentials

### Development Mode
- **Username:** `dev_researcher` | **Password:** `DevMode2025Research!`

**Configuration:**
- Study condition: Personalised (with sidebar toggle)
- Data folder: `dev_testing/`  
- Dev mode: ✅ | Fast test: ❌ | Upload enabled: ✅

### Fast Demo Mode
- **Username:** `fast_demo` | **Password:** `FastDemo2025!`

**Configuration:**
- Study condition: Personalised
- Data folder: `demo_testing/`
- Dev mode: ❌ | Fast test: ✅ | Upload enabled: ❌

### Combined Dev + Fast Test
- **Username:** `dev_fast_test` | **Password:** `DevFastTest2025!`

**Configuration:**
- Study condition: Personalised (with sidebar toggle)
- Data folder: `dev_fast_testing/`
- Dev mode: ✅ | Fast test: ✅ | Upload enabled: ✅

### Administrator Access
- **Username:** `admin_furkan` | **Password:** `AdminAccess2025Furkan!`

**Configuration:**
- Study condition: Personalised (with sidebar toggle)
- Data folder: `admin_testing/`
- Dev mode: ✅ | Fast test: ❌ | Upload enabled: ✅

## Data Organization

All session data is automatically organized in both local storage and Supabase:

```
output/
├── personalised_cohort/          # Personalised study participants
│   ├── 20250930_143022_Bailey_Smith/
│   └── 20250930_144115_Morgan_Chen/
├── generic_cohort/               # Generic study participants  
│   ├── 20250930_145203_Alex_Johnson/
│   └── 20250930_150344_Jordan_Lee/
├── dev_testing/                  # Development sessions
├── demo_testing/                 # Fast demo sessions
├── dev_fast_testing/            # Combined dev+demo sessions
└── admin_testing/               # Administrator sessions
```

## Security Features

- ✅ **Secure password hashing** with study-specific salt
- ✅ **Automatic session cleanup** on logout  
- ✅ **Credential-based access control** with role permissions
- ✅ **Data segregation** by credential type for analysis
- ✅ **Session expiration** - requires re-login for each session

## Usage Instructions

1. **For study participants:** Use assigned credentials only
2. **For development:** Use `dev_researcher` or `dev_fast_test` 
3. **For demos:** Use `fast_demo` for quick demonstrations
4. **For admin tasks:** Use `admin_furkan` for full access

⚠️ **Important:** All passwords are case-sensitive and must be entered exactly as shown.