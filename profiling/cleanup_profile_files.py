#!/usr/bin/env python3
"""
Script to clean up profile output files by removing unwanted sections.
Keeps content from ">> Final simulation time:" to just before "Unused ParmParse Variables:"
"""

from pathlib import Path
import sys


def cleanup_profile_file(filepath):
    """
    Clean up a profile file by removing lines before ">> Final simulation time:"
    and all lines from "Unused ParmParse Variables:" onwards.
    Also extracts and preserves the total number of initial particles.
    
    Args:
        filepath: Path to the profile file to clean
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Extract particle count from anywhere in the file
    particle_count = None
    for line in lines:
        if 'Total number of initial particles' in line:
            # Parse the line format: "Total number of initial particles XXXXXX"
            parts = line.split()
            if len(parts) >= 5:
                try:
                    particle_count = int(parts[-1])
                    break
                except ValueError:
                    continue
    
    # Find the start marker
    start_idx = None
    for i, line in enumerate(lines):
        if '>> Final simulation time:' in line:
            start_idx = i
            break
    
    if start_idx is None:
        print(f"Warning: Could not find '>> Final simulation time:' in {filepath}")
        return False
    
    # Find the end marker
    end_idx = None
    for i in range(start_idx, len(lines)):
        if 'Unused ParmParse Variables:' in lines[i]:
            end_idx = i
            break
    
    if end_idx is None:
        # If no end marker found, keep everything from start_idx to end
        end_idx = len(lines)
    
    # Keep lines from start_idx to end_idx (excluding end_idx and beyond)
    cleaned_lines = lines[start_idx:end_idx]
    
    # Append particle count as metadata if found
    if particle_count is not None:
        cleaned_lines.append(f"\n# Particle metadata\n")
        cleaned_lines.append(f"# Total initial particles: {particle_count}\n")
    
    # Write back the cleaned content
    try:
        with open(filepath, 'w') as f:
            f.writelines(cleaned_lines)
        print(f"Cleaned: {filepath}")
        return True
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
        return False


def main():
    # Directories to clean
    directories = [
        Path('/Users/dmontgo2/Library/CloudStorage/OneDrive-NREL/Projects/SAF-VTO/Ascent74/PrefVaporization-Study/Figures/profile/profile_10'),
        Path('/Users/dmontgo2/Library/CloudStorage/OneDrive-NREL/Projects/SAF-VTO/Ascent74/PrefVaporization-Study/Figures/profile/profile_100'),
    ]
    
    total_cleaned = 0
    total_failed = 0
    
    for directory in directories:
        if not directory.exists():
            print(f"Directory not found: {directory}")
            continue
        
        print(f"\nProcessing directory: {directory}")
        print("-" * 80)
        
        # Find all profile_*.out files
        profile_files = sorted(directory.glob('profile_*.out'))
        
        if not profile_files:
            print(f"  No profile_*.out files found in {directory}")
            continue
        
        for filepath in profile_files:
            if cleanup_profile_file(filepath):
                total_cleaned += 1
            else:
                total_failed += 1
    
    print("\n" + "=" * 80)
    print(f"Cleanup complete: {total_cleaned} files cleaned, {total_failed} files failed")


if __name__ == '__main__':
    main()
