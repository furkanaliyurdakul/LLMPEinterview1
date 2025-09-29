#!/usr/bin/env python3
"""
Research Data Analyzer - Consolidates and analyzes all final research analytics

This script:
1. Collects all final_research_analytics.json files across sessions
2. Generates aggregate statistics and insights
3. Creates comparison reports between personalized vs generic conditions
4. Exports research-ready data summaries

Usage:
    python analyze_research_data.py
    
    # With specific output file
    python analyze_research_data.py --output research_summary.json
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


def load_analytics_files(output_dir: Path) -> List[Dict]:
    """Load all final_research_analytics.json files from session directories."""
    analytics_files = []
    
    for session_dir in output_dir.iterdir():
        if not session_dir.is_dir():
            continue
            
        analytics_file = session_dir / "analytics" / "final_research_analytics.json"
        if analytics_file.exists():
            try:
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analytics_files.append(data)
            except Exception as e:
                print(f"Warning: Could not load {analytics_file}: {e}")
    
    return analytics_files


def analyze_session_data(analytics_data: List[Dict]) -> Dict:
    """Analyze collected analytics data and generate insights."""
    
    # Separate by condition
    personalized_sessions = [d for d in analytics_data if d.get("session_info", {}).get("condition") in ["personalized", "personalised"]]
    generic_sessions = [d for d in analytics_data if d.get("session_info", {}).get("condition") == "generic"]
    
    analysis = {
        "total_sessions": len(analytics_data),
        "conditions": {
            "personalized": len(personalized_sessions),
            "generic": len(generic_sessions)
        },
        "session_timing_analysis": {},
        "interaction_analysis": {},
        "ueq_analysis": {},
        "knowledge_test_analysis": {},
        "learning_efficiency_analysis": {},
        "detailed_sessions": []
    }
    
    # Helper function to extract metrics safely
    def safe_extract(data_list, path, default=None):
        """Safely extract nested values from data structures."""
        values = []
        for item in data_list:
            try:
                val = item
                for key in path:
                    val = val[key]
                if val is not None:
                    values.append(val)
            except (KeyError, TypeError):
                if default is not None:
                    values.append(default)
        return values
    
    # Session timing analysis
    def analyze_timing(sessions, condition_name):
        total_times = safe_extract(sessions, ["summary_metrics", "total_session_time_minutes"])
        learning_times = safe_extract(sessions, ["page_timings", "personalized_learning"], 0)
        learning_times_min = [t/60 for t in learning_times if t > 0]
        
        if total_times:
            analysis["session_timing_analysis"][condition_name] = {
                "total_session_time_stats": {
                    "mean": statistics.mean(total_times),
                    "median": statistics.median(total_times),
                    "std_dev": statistics.stdev(total_times) if len(total_times) > 1 else 0,
                    "min": min(total_times),
                    "max": max(total_times),
                    "count": len(total_times)
                }
            }
            
            if learning_times_min:
                analysis["session_timing_analysis"][condition_name]["learning_phase_time_stats"] = {
                    "mean": statistics.mean(learning_times_min),
                    "median": statistics.median(learning_times_min),
                    "std_dev": statistics.stdev(learning_times_min) if len(learning_times_min) > 1 else 0,
                    "min": min(learning_times_min),
                    "max": max(learning_times_min),
                    "count": len(learning_times_min)
                }
    
    # Interaction analysis
    def analyze_interactions(sessions, condition_name):
        total_interactions = safe_extract(sessions, ["summary_metrics", "learning_engagement", "total_ai_interactions"])
        slide_explanations = safe_extract(sessions, ["summary_metrics", "learning_engagement", "slide_explanations"])
        manual_chats = safe_extract(sessions, ["summary_metrics", "learning_engagement", "manual_chat"])
        slide_to_chat_ratios = safe_extract(sessions, ["summary_metrics", "learning_engagement", "slide_to_chat_ratio"])
        
        if total_interactions:
            analysis["interaction_analysis"][condition_name] = {
                "total_interactions_stats": {
                    "mean": statistics.mean(total_interactions),
                    "median": statistics.median(total_interactions),
                    "std_dev": statistics.stdev(total_interactions) if len(total_interactions) > 1 else 0,
                    "min": min(total_interactions),
                    "max": max(total_interactions),
                    "count": len(total_interactions)
                },
                "interaction_breakdown": {
                    "slide_explanations": {
                        "mean": statistics.mean(slide_explanations) if slide_explanations else 0,
                        "total": sum(slide_explanations) if slide_explanations else 0
                    },
                    "manual_chat": {
                        "mean": statistics.mean(manual_chats) if manual_chats else 0,
                        "total": sum(manual_chats) if manual_chats else 0
                    }
                }
            }
            
            if slide_to_chat_ratios:
                analysis["interaction_analysis"][condition_name]["slide_to_chat_ratio_stats"] = {
                    "mean": statistics.mean(slide_to_chat_ratios),
                    "median": statistics.median(slide_to_chat_ratios),
                    "std_dev": statistics.stdev(slide_to_chat_ratios) if len(slide_to_chat_ratios) > 1 else 0
                }
    
    # UEQ Analysis
    def analyze_ueq(sessions, condition_name):
        ueq_means = []
        ueq_grades = defaultdict(list)
        
        for session in sessions:
            ueq_results = session.get("ueq_results")
            if ueq_results:
                scale_means = ueq_results.get("scale_means", {})
                grades = ueq_results.get("grades", {})
                
                if scale_means:
                    ueq_means.append(scale_means)
                
                for scale, grade in grades.items():
                    ueq_grades[scale].append(grade)
        
        if ueq_means:
            # Calculate average UEQ scores across sessions
            scale_averages = {}
            for scale in ["Attractiveness", "Perspicuity", "Efficiency", "Dependability", "Stimulation", "Novelty"]:
                scale_values = [means.get(scale, 0) for means in ueq_means if scale in means]
                if scale_values:
                    scale_averages[scale] = {
                        "mean": statistics.mean(scale_values),
                        "std_dev": statistics.stdev(scale_values) if len(scale_values) > 1 else 0,
                        "count": len(scale_values)
                    }
            
            analysis["ueq_analysis"][condition_name] = {
                "scale_scores": scale_averages,
                "grade_distribution": {
                    scale: {
                        "excellent": grades.count("Excellent"),
                        "good": grades.count("Good"),
                        "above_average": grades.count("Above Average"),
                        "below_average": grades.count("Below Average"),
                        "bad": grades.count("Bad")
                    } for scale, grades in ueq_grades.items()
                },
                "total_responses": len(ueq_means)
            }
    
    # Knowledge Test Analysis
    def analyze_knowledge_test(sessions, condition_name):
        accuracies = safe_extract(sessions, ["summary_metrics", "knowledge_test_summary", "accuracy_percentage"])
        correct_answers = safe_extract(sessions, ["summary_metrics", "knowledge_test_summary", "correct_answers"])
        
        if accuracies:
            analysis["knowledge_test_analysis"][condition_name] = {
                "accuracy_stats": {
                    "mean": statistics.mean(accuracies),
                    "median": statistics.median(accuracies),
                    "std_dev": statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
                    "min": min(accuracies),
                    "max": max(accuracies),
                    "count": len(accuracies)
                }
            }
            
            if correct_answers:
                analysis["knowledge_test_analysis"][condition_name]["correct_answers_stats"] = {
                    "mean": statistics.mean(correct_answers),
                    "median": statistics.median(correct_answers),
                    "std_dev": statistics.stdev(correct_answers) if len(correct_answers) > 1 else 0
                }
    
    # Learning Efficiency Analysis
    def analyze_efficiency(sessions, condition_name):
        interactions_per_min = safe_extract(sessions, ["summary_metrics", "learning_efficiency", "interactions_per_minute"])
        avg_time_per_interaction = safe_extract(sessions, ["summary_metrics", "learning_efficiency", "avg_time_per_interaction_seconds"])
        
        if interactions_per_min:
            analysis["learning_efficiency_analysis"][condition_name] = {
                "interactions_per_minute_stats": {
                    "mean": statistics.mean(interactions_per_min),
                    "median": statistics.median(interactions_per_min),
                    "std_dev": statistics.stdev(interactions_per_min) if len(interactions_per_min) > 1 else 0,
                    "count": len(interactions_per_min)
                }
            }
            
            if avg_time_per_interaction:
                analysis["learning_efficiency_analysis"][condition_name]["avg_time_per_interaction_stats"] = {
                    "mean": statistics.mean(avg_time_per_interaction),
                    "median": statistics.median(avg_time_per_interaction),
                    "std_dev": statistics.stdev(avg_time_per_interaction) if len(avg_time_per_interaction) > 1 else 0
                }
    
    # Run analyses for both conditions
    if personalized_sessions:
        analyze_timing(personalized_sessions, "personalized")
        analyze_interactions(personalized_sessions, "personalized")
        analyze_ueq(personalized_sessions, "personalized")
        analyze_knowledge_test(personalized_sessions, "personalized")
        analyze_efficiency(personalized_sessions, "personalized")
    
    if generic_sessions:
        analyze_timing(generic_sessions, "generic")
        analyze_interactions(generic_sessions, "generic")
        analyze_ueq(generic_sessions, "generic")
        analyze_knowledge_test(generic_sessions, "generic")
        analyze_efficiency(generic_sessions, "generic")
    
    # Create detailed session summaries
    for session_data in analytics_data:
        session_info = session_data.get("session_info", {})
        summary_metrics = session_data.get("summary_metrics", {})
        
        detailed_session = {
            "session_id": session_info.get("session_id"),
            "pseudonym": session_info.get("pseudonym"),
            "condition": session_info.get("condition"),
            "total_time_minutes": summary_metrics.get("total_session_time_minutes"),
            "total_interactions": summary_metrics.get("learning_engagement", {}).get("total_ai_interactions"),
            "knowledge_accuracy": summary_metrics.get("knowledge_test_summary", {}).get("accuracy_percentage"),
            "has_ueq_data": session_data.get("ueq_results") is not None,
            "has_profile_data": session_data.get("profile_data") is not None
        }
        
        analysis["detailed_sessions"].append(detailed_session)
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description="Analyze research data from all sessions")
    parser.add_argument("--output", default="research_analysis.json", help="Output file for analysis results")
    parser.add_argument("--output-dir", default="output", help="Directory containing session data")
    args = parser.parse_args()
    
    project_root = Path(__file__).parent
    output_dir = project_root / args.output_dir
    
    if not output_dir.exists():
        print(f"Error: Output directory {output_dir} does not exist")
        return
    
    print("Loading analytics files...")
    analytics_data = load_analytics_files(output_dir)
    
    if not analytics_data:
        print("No analytics files found. Run generate_final_analytics.py first.")
        return
    
    print(f"Found {len(analytics_data)} session analytics files")
    print("Analyzing data...")
    
    analysis_results = analyze_session_data(analytics_data)
    
    # Save analysis results
    output_file = project_root / args.output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=4, ensure_ascii=False)
    
    print(f"Analysis complete! Results saved to: {output_file}")
    
    # Print summary
    print("\\n" + "="*60)
    print("RESEARCH DATA SUMMARY")
    print("="*60)
    print(f"Total sessions analyzed: {analysis_results['total_sessions']}")
    print(f"Personalized condition: {analysis_results['conditions']['personalized']} sessions")
    print(f"Generic condition: {analysis_results['conditions']['generic']} sessions")
    
    # Print key insights if available
    if analysis_results["interaction_analysis"]:
        print("\\nInteraction Insights:")
        for condition, data in analysis_results["interaction_analysis"].items():
            total_stats = data.get("total_interactions_stats", {})
            if total_stats:
                print(f"  {condition.title()}: Avg {total_stats.get('mean', 0):.1f} interactions per session")
    
    if analysis_results["knowledge_test_analysis"]:
        print("\\nKnowledge Test Performance:")
        for condition, data in analysis_results["knowledge_test_analysis"].items():
            accuracy_stats = data.get("accuracy_stats", {})
            if accuracy_stats:
                print(f"  {condition.title()}: Avg {accuracy_stats.get('mean', 0):.1f}% accuracy")
    
    print(f"\\nDetailed analysis available in: {output_file}")


if __name__ == "__main__":
    main()