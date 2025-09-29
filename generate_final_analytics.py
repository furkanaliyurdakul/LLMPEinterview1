#!/usr/bin/env python3
"""
Utility script to generate final research analytics for all existing sessions.

This script:
1. Scans the output directory for all session folders
2. Generates final_research_analytics.json for each session
3. Provides a summary of analytics generation results

Usage:
    python generate_final_analytics.py
    
or to process a specific session:
    python generate_final_analytics.py --session 20250922_142955_Winter_Smith
"""

import argparse
import json
import os
import sys
from pathlib import Path
from session_manager import SessionManager


def generate_analytics_for_session(session_dir: Path) -> dict:
    """Generate final analytics for a single session."""
    try:
        session_id = session_dir.name
        
        # Read condition from condition.txt
        condition_file = session_dir / "condition.txt"
        condition = "unknown"
        if condition_file.exists():
            condition = condition_file.read_text().strip()
        
        # Create session manager for this session
        sm = SessionManager()
        sm.session_dir = str(session_dir)
        sm.session_id = session_id
        sm.condition = condition
        
        # Set up directories
        sm.profile_dir = str(session_dir / "profile")
        sm.analytics_dir = str(session_dir / "analytics")
        sm.ueq_dir = str(session_dir / "ueq")
        sm.knowledge_test_dir = str(session_dir / "knowledge_test")
        
        # Generate final analytics
        final_path = sm.create_final_analytics()
        
        return {
            "session_id": session_id,
            "status": "success",
            "path": final_path,
            "condition": condition
        }
        
    except Exception as e:
        return {
            "session_id": session_dir.name,
            "status": "error",
            "error": str(e),
            "condition": "unknown"
        }


def main():
    parser = argparse.ArgumentParser(description="Generate final research analytics for sessions")
    parser.add_argument("--session", help="Process specific session ID only")
    parser.add_argument("--output-dir", default="output", help="Output directory containing sessions")
    args = parser.parse_args()
    
    # Get project root directory
    project_root = Path(__file__).parent
    output_dir = project_root / args.output_dir
    
    if not output_dir.exists():
        print(f"Error: Output directory {output_dir} does not exist")
        sys.exit(1)
    
    # Find session directories
    if args.session:
        session_dirs = [output_dir / args.session]
        if not session_dirs[0].exists():
            print(f"Error: Session {args.session} not found")
            sys.exit(1)
    else:
        # Find all session directories (they start with timestamp format YYYYMMDD_HHMMSS_)
        session_dirs = [
            d for d in output_dir.iterdir() 
            if d.is_dir() and len(d.name.split("_")) >= 3
        ]
    
    if not session_dirs:
        print("No session directories found")
        sys.exit(0)
    
    print(f"Found {len(session_dirs)} session(s) to process...")
    print()
    
    results = []
    for session_dir in sorted(session_dirs):
        print(f"Processing: {session_dir.name}")
        result = generate_analytics_for_session(session_dir)
        results.append(result)
        
        if result["status"] == "success":
            print(f"  ✓ Analytics generated: {Path(result['path']).name}")
        else:
            print(f"  ✗ Error: {result['error']}")
        print()
    
    # Summary
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total sessions processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\\nCondition breakdown for successful sessions:")
        conditions = {}
        for result in successful:
            condition = result["condition"]
            conditions[condition] = conditions.get(condition, 0) + 1
        
        for condition, count in sorted(conditions.items()):
            print(f"  {condition}: {count} sessions")
    
    if failed:
        print(f"\\nFailed sessions:")
        for result in failed:
            print(f"  {result['session_id']}: {result['error']}")
    
    print()
    print("Final analytics files are saved as 'final_research_analytics.json' in each session's analytics/ directory")


if __name__ == "__main__":
    main()