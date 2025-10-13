#!/usr/bin/env python3
"""
CLI tool to extract structured data from an Excel file and print a concise summary.
Uses the existing ExcelDataMapper (which leverages ExcelParserService) to analyze
sheets and map common fields (including Malay/localized headers) into a
standard structure: program_info, participants, evaluation, tentative, suggestions, attendance.

Usage:
  python backend/extract_from_excel.py "path/to/SENARAI SEMAK PUNCAK ALAM.xlsx"
"""
import os
import sys
import json
import argparse
from typing import Any, Dict

# Ensure backend package imports work when running from project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from app.services.template_optimizer import ExcelDataMapper
except Exception as e:
    print("Error: Unable to import ExcelDataMapper from app.services.template_optimizer.")
    print("Detail:", str(e))
    sys.exit(1)


def summarize_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
    participants = analysis.get('participants', []) or []
    suggestions = analysis.get('suggestions', {}) or {}
    evaluation = analysis.get('evaluation_data', {}) or {}
    tentative = analysis.get('tentative', {}) or {}

    # Extract readable keys for evaluation
    evaluation_keys = {}
    for section, section_data in evaluation.items():
        if isinstance(section_data, dict):
            evaluation_keys[section] = list(section_data.keys())
        else:
            evaluation_keys[section] = []

    summary = {
        "program_info": analysis.get('program_info', {}),
        "participants_count": len(participants),
        "participants_sample": participants[:5],
        "tentative": tentative,
        "evaluation_sections": evaluation_keys,
        "suggestions": {
            "consultant_count": len(suggestions.get('consultant', []) or []),
            "participants_count": len(suggestions.get('participants', []) or [])
        },
        "attendance": analysis.get('attendance', {}),
        "metadata": analysis.get('metadata', {})
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Extract structured data from Excel and print JSON summary")
    parser.add_argument("excel_path", help="Path to the Excel file (.xlsx or .xls)")
    args = parser.parse_args()

    excel_path = args.excel_path
    if not os.path.exists(excel_path):
        print(f"Error: File not found: {excel_path}")
        sys.exit(1)

    try:
        mapper = ExcelDataMapper()
        analysis = mapper.analyze_excel_structure(excel_path)
        summary = summarize_analysis(analysis)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception as e:
        print("Error analyzing Excel file:", str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
