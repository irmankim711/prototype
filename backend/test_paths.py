#!/usr/bin/env python3
"""Test script to check template directory paths"""

from pathlib import Path
import os

# Get the current working directory
cwd = Path.cwd()
print(f"Current working directory: {cwd}")

# Check if templates directory exists in current directory
templates_in_cwd = cwd / 'templates'
print(f"Templates in CWD: {templates_in_cwd}")
print(f"Exists: {templates_in_cwd.exists()}")

# Check if templates directory exists in parent directory
templates_in_parent = cwd.parent / 'templates'
print(f"Templates in parent: {templates_in_parent}")
print(f"Exists: {templates_in_parent.exists()}")

# Check what's in the templates directory if it exists
if templates_in_cwd.exists():
    print(f"\nFiles in {templates_in_cwd}:")
    for file in templates_in_cwd.iterdir():
        print(f"  - {file.name} ({file.suffix})")

if templates_in_parent.exists():
    print(f"\nFiles in {templates_in_parent}:")
    for file in templates_in_parent.iterdir():
        print(f"  - {file.name} ({file.suffix})")

# Check the path that the nextgen route would use
# __file__ would be the path to nextgen_report_builder.py
nextgen_file = cwd / 'app' / 'routes' / 'nextgen_report_builder.py'
if nextgen_file.exists():
    templates_from_nextgen = nextgen_file.parent.parent.parent / 'templates'
    print(f"\nTemplates path from nextgen route: {templates_from_nextgen}")
    print(f"Exists: {templates_from_nextgen.exists()}")
    
    if templates_from_nextgen.exists():
        print(f"Files in {templates_from_nextgen}:")
        for file in templates_from_nextgen.iterdir():
            print(f"  - {file.name} ({file.suffix})")
else:
    print(f"\nNextGen file not found at: {nextgen_file}")


