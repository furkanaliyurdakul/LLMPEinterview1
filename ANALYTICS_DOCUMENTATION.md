# Research Analytics System Documentation

This document explains the comprehensive analytics system that consolidates all research data into a single, easy-to-analyze format.

## Overview

The analytics system automatically generates a comprehensive `final_research_analytics.json` file for each completed session, containing all research-relevant data in one place. This eliminates the need to manually gather data from multiple directories and files.

## What's Included in Final Analytics

Each `final_research_analytics.json` file contains:

### 1. Session Information
- Session ID and pseudonym
- Experimental condition (personalized/generic)
- Timestamp and session directory path

### 2. Profile Data
- Student profile information (pseudonymized)
- Learning preferences and background

### 3. Page Timings
- Time spent on each page (home, profile, learning, test, UEQ)
- Total session duration
- Learning phase duration specifically

### 4. Interaction Analytics
- Number of slide explanations requested
- Number of manual chat messages
- Total AI interactions
- Engagement metrics (interaction distribution, slide-to-chat ratio)

### 5. UEQ Results
- Raw UEQ responses (1-7 scale)
- Calculated scale means
- Benchmark grades (Excellent, Good, etc.)
- Optional comment text

### 6. Knowledge Test Results
- Individual question answers
- Correct/incorrect marking
- Overall accuracy percentage
- Number of questions completed

### 7. Summary Metrics
- Total session time (seconds and minutes)
- Learning engagement summary
- Learning efficiency metrics (interactions per minute, avg time per interaction)
- UEQ summary scores
- Knowledge test performance summary

## How It Works

### Automatic Generation
The final analytics are automatically generated when a participant clicks "Finish" after completing the UEQ survey (the last step). The system:

1. Collects data from all session directories (profile, analytics, ueq, knowledge_test, meta)
2. Consolidates everything into a single JSON file
3. Calculates additional summary metrics
4. Saves to `{session_dir}/analytics/final_research_analytics.json`

### Manual Generation
You can also generate final analytics for existing sessions using the utility scripts:

#### For a single session:
```bash
python generate_final_analytics.py --session 20250922_142955_Winter_Smith
```

#### For all sessions:
```bash
python generate_final_analytics.py
```

#### Comprehensive research analysis:
```bash
python analyze_research_data.py
```

## Utility Scripts

### 1. `generate_final_analytics.py`
- Generates final analytics for one or all sessions
- Handles missing data gracefully
- Provides summary of successful/failed generations
- Shows condition breakdown

### 2. `analyze_research_data.py`
- Processes all final analytics files
- Generates aggregate statistics
- Compares personalized vs generic conditions
- Creates research-ready summary data
- Outputs to `research_analysis.json`

## File Locations

```
output/
├── 20250922_142955_Winter_Smith/
│   ├── analytics/
│   │   ├── interaction_analytics.json          # Individual interaction data
│   │   └── final_research_analytics.json       # ★ COMPREHENSIVE DATA
│   ├── profile/
│   │   ├── original_profile.json
│   │   └── pseudonymized_profile.json
│   ├── ueq/
│   │   └── ueq_responses.txt
│   ├── knowledge_test/
│   │   └── knowledge_test_results.json
│   └── meta/
│       └── page_durations.json
└── research_analysis.json                      # ★ AGGREGATE ANALYSIS
```

## Example Analytics Structure

```json
{
    "session_info": {
        "session_id": "20250922_142955_Winter_Smith",
        "pseudonym": "142955_Winter_Smith",
        "condition": "generic",
        "timestamp": "20250922"
    },
    "page_timings": {
        "home": 5.9,
        "profile_survey": 5.4,
        "personalized_learning": 45.5,
        "knowledge_test": 578.2
    },
    "interaction_analytics": {
        "interaction_counts": {
            "slide_explanations": 1,
            "manual_chat": 2,
            "total_user_interactions": 3
        },
        "engagement_metrics": {
            "slide_to_chat_ratio": 0.5,
            "interaction_distribution": {
                "slide_explanations_pct": 33.3,
                "manual_chat_pct": 66.7
            }
        }
    },
    "summary_metrics": {
        "total_session_time_minutes": 10.6,
        "learning_engagement": {
            "total_ai_interactions": 3,
            "slide_explanations": 1,
            "manual_chat": 2
        },
        "learning_efficiency": {
            "interactions_per_minute": 4.0,
            "avg_time_per_interaction_seconds": 15.2
        }
    }
}
```

## Research Benefits

### Single Source of Truth
- All research data in one consolidated file per session
- No need to manually collect from multiple directories
- Consistent format across all sessions

### Ready for Analysis
- Pre-calculated summary metrics
- Standardized data structure
- Easy to import into analysis tools (R, Python, SPSS)

### Comprehensive Coverage
- User behavior (interactions, timing)
- Learning outcomes (knowledge test)
- User experience (UEQ)
- Technical metrics (efficiency, engagement)

### Automated Processing
- Generates during normal platform usage
- Handles missing data gracefully
- Provides aggregate analysis across conditions

## Usage for Research Analysis

### Import into Python/R
```python
import json
import pandas as pd

# Load single session
with open('final_research_analytics.json', 'r') as f:
    session_data = json.load(f)

# Load aggregate analysis
with open('research_analysis.json', 'r') as f:
    research_summary = json.load(f)

# Convert to DataFrame for analysis
sessions = research_summary['detailed_sessions']
df = pd.DataFrame(sessions)
```

### Key Metrics for Analysis
- **Learning Engagement**: Total interactions, slide-to-chat ratio
- **Learning Efficiency**: Time per interaction, interactions per minute
- **User Experience**: UEQ scale scores and grades
- **Learning Outcomes**: Knowledge test accuracy
- **Session Behavior**: Time distribution across pages

### Condition Comparison
The system automatically separates data by experimental condition (personalized vs generic), making it easy to:
- Compare engagement patterns
- Analyze learning efficiency differences
- Evaluate user experience variations
- Assess knowledge acquisition effectiveness

## Best Practices

1. **Always generate final analytics** when a session is complete
2. **Run aggregate analysis** before conducting statistical tests
3. **Check data completeness** in the summary metrics
4. **Use the detailed_sessions** array for participant-level analysis
5. **Leverage pre-calculated metrics** to speed up analysis

This system provides everything you need for comprehensive research analysis in a single, well-structured file per session, plus aggregate insights across your entire study.