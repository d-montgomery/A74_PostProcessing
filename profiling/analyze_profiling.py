#!/usr/bin/env python3
"""
Script to analyze profiling results from PeleLMeX simulations.
Extracts timing statistics for key functions across different configurations.

Configuration:
  Edit TIMESTEPS at the top of this script to analyze different directories:
  TIMESTEPS = 10   # Analyze profile_10 directory
  TIMESTEPS = 100  # Analyze profile_100 directory

Output:
  Prints profiling summary to stdout
  Saves CSV to: profile_{TIMESTEPS}/profiling_analysis_summary_{TIMESTEPS}.csv
"""

import os
import re
from pathlib import Path
import pandas as pd

# ===== CONFIGURATION =====
# Set timesteps to analyze: 10 or 100
TIMESTEPS = 100
# =======================


def parse_profile_file(filepath):
    """
    Parse a profile_*.out file and extract timing information.
    
    Args:
        filepath: Path to the profile file
        
    Returns:
        tuple: (data dict, total_time float, particle_count int) - Dictionary containing timing data for each function 
               (both exclusive and inclusive), total simulation time, and particle count
    """
    data = {}
    total_time = None
    particle_count = None
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Extract particle count from metadata comment at end of file
    for line in reversed(lines):
        if 'Total initial particles:' in line:
            # Parse the line format: "# Total initial particles: XXXXXX"
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    particle_count = int(parts[-1].strip())
                    break
                except ValueError:
                    continue
    
    # Find the start of the exclusive profiling table
    excl_start_idx = None
    for i, line in enumerate(lines):
        if 'Name' in line and 'NCalls' in line and 'Excl. Min' in line:
            excl_start_idx = i + 2  # Skip the header and separator line
            break
    
    # Find the start of the inclusive profiling table
    incl_start_idx = None
    for i, line in enumerate(lines):
        if 'Name' in line and 'NCalls' in line and 'Incl. Min' in line:
            incl_start_idx = i + 2  # Skip the header and separator line
            break
    
    # Parse exclusive profiling data
    if excl_start_idx is not None:
        for line in lines[excl_start_idx:]:
            # Stop at empty lines or lines with dashes
            if not line.strip() or line.startswith('---'):
                break
            
            # Parse the line - format: Name NCalls Excl.Min Excl.Avg Excl.Max Max%
            parts = line.split()
            if len(parts) >= 6:
                name = parts[0]
                try:
                    ncalls = int(parts[1])
                    excl_min = float(parts[2])
                    excl_avg = float(parts[3])
                    excl_max = float(parts[4])
                    excl_max_pct = float(parts[5].rstrip('%'))
                    
                    data[name] = {
                        'NCalls': ncalls,
                        'Excl_Min': excl_min,
                        'Excl_Avg': excl_avg,
                        'Excl_Max': excl_max,
                        'Excl_Max_Pct': excl_max_pct
                    }
                except (ValueError, IndexError):
                    continue
    
    # Parse inclusive profiling data
    if incl_start_idx is not None:
        for line in lines[incl_start_idx:]:
            # Stop at empty lines or lines with dashes
            if not line.strip() or line.startswith('---'):
                break
            
            # Parse the line - format: Name NCalls Incl.Min Incl.Avg Incl.Max Max%
            parts = line.split()
            if len(parts) >= 6:
                name = parts[0]
                try:
                    incl_min = float(parts[2])
                    incl_avg = float(parts[3])
                    incl_max = float(parts[4])
                    incl_max_pct = float(parts[5].rstrip('%'))
                    
                    # Add to existing entry or create new one
                    if name in data:
                        data[name].update({
                            'Incl_Min': incl_min,
                            'Incl_Avg': incl_avg,
                            'Incl_Max': incl_max,
                            'Incl_Max_Pct': incl_max_pct
                        })
                    else:
                        # Function only appears in inclusive section
                        ncalls = int(parts[1])
                        data[name] = {
                            'NCalls': ncalls,
                            'Incl_Min': incl_min,
                            'Incl_Avg': incl_avg,
                            'Incl_Max': incl_max,
                            'Incl_Max_Pct': incl_max_pct
                        }
                except (ValueError, IndexError):
                    continue
    
    # Use Incl_Avg from PeleLMeX::Evolve() as total_time if available
    if 'PeleLMeX::Evolve()' in data and 'Incl_Avg' in data['PeleLMeX::Evolve()']:
        total_time = data['PeleLMeX::Evolve()']['Incl_Avg']
    
    if total_time is None:
        # Throw error if total time cannot be determined
        raise ValueError(f"Total time could not be determined from file: {filepath}")
    return data, total_time, particle_count


def analyze_profiling_directory(directory, functions_of_interest):
    """
    Analyze all profile_*.out files in the directory.
    
    Args:
        directory: Path to the profiling directory
        functions_of_interest: List of function names to extract
        
    Returns:
        DataFrame: Pandas DataFrame with all results
    """
    profile_files = sorted(Path(directory).glob('profile_*.out'))
    
    results = []
    total_times = {}
    particle_counts = {}
    
    for filepath in profile_files:
        # Extract configuration from filename (e.g., "gc-to-gc" from "profile_posf10264_gc-to-gc.out")
        # Remove "profile_" prefix and get the stem
        full_config = filepath.stem.replace('profile_', '')
        
        # Extract configuration after case ID (remove prefix like "posf10264_")
        # The case ID is followed by an underscore
        if '_' in full_config:
            # Split on underscore and take everything after the first part (case ID)
            config = '_'.join(full_config.split('_')[1:])
        else:
            config = full_config
        
        # Parse the file
        data, total_time, particle_count = parse_profile_file(filepath)
        
        # Store total time
        if total_time is not None:
            total_times[config] = total_time
        
        # Store particle count
        if particle_count is not None:
            particle_counts[config] = particle_count
        
        # Extract data for functions of interest
        for func_name in functions_of_interest:
            if func_name in data:
                result = {
                    'Configuration': config,
                    'Function': func_name,
                    **data[func_name]
                }
                results.append(result)
    
    df = pd.DataFrame(results)
    
    # Add Total_Time column to each row
    if total_times:
        df['Total_Time'] = df['Configuration'].map(total_times)
    
    # Add Particles column to each row
    if particle_counts:
        df['Particles'] = df['Configuration'].map(particle_counts)
    
    return df


def print_summary(df):
    """Print a summary of the profiling results."""
    
    print("\n" + "="*80)
    print("PROFILING ANALYSIS SUMMARY")
    print("="*80 + "\n")
    
    # Summary by function - Exclusive
    print("EXCLUSIVE TIMING - AVERAGE BY FUNCTION (across all configurations)")
    print("-" * 80)
    func_summary = df.groupby('Function').agg({
        'Excl_Avg': ['mean', 'std', 'min', 'max'],
        'Excl_Max_Pct': ['mean', 'std', 'min', 'max'],
        'NCalls': ['mean', 'min', 'max']
    }).round(2)
    # Fill NaN std values with 0 (occurs when function appears in only one configuration)
    func_summary = func_summary.fillna(0)
    print(func_summary)
    print()
    
    # Summary by function - Inclusive
    if 'Incl_Avg' in df.columns:
        print("\nINCLUSIVE TIMING - AVERAGE BY FUNCTION (across all configurations)")
        print("-" * 80)
        func_summary_incl = df.groupby('Function').agg({
            'Incl_Avg': ['mean', 'std', 'min', 'max'],
            'Incl_Max_Pct': ['mean', 'std', 'min', 'max'],
            'NCalls': ['mean', 'min', 'max']
        }).round(2)
        # Fill NaN std values with 0 (occurs when function appears in only one configuration)
        func_summary_incl = func_summary_incl.fillna(0)
        print(func_summary_incl)
        print()
    
    # Summary by configuration
    print("\nTIMING BY CONFIGURATION")
    print("-" * 80)
    for config in sorted(df['Configuration'].unique()):
        print(f"\nConfiguration: {config}")
        print("-" * 40)
        config_data = df[df['Configuration'] == config].sort_values('Excl_Max_Pct', ascending=False)
        for _, row in config_data.iterrows():
            incl_str = ""
            if 'Incl_Avg' in row:
                incl_str = f"  Incl_Avg: {row['Incl_Avg']:>8.2f}s  Incl_Max%: {row['Incl_Max_Pct']:>6.2f}%"
            print(f"  {row['Function']:<50} "
                  f"Excl_Avg: {row['Excl_Avg']:>8.2f}s  "
                  f"Excl_Max%: {row['Excl_Max_Pct']:>6.2f}%  "
                  f"NCalls: {row['NCalls']:>8}"
                  f"{incl_str}")
    
    # Comparison table - Exclusive
    print("\n\nCOMPARISON TABLE: Excl_Avg (seconds)")
    print("-" * 80)
    pivot = df.pivot(index='Function', columns='Configuration', values='Excl_Avg')
    # Fill NaN with a dash to indicate function not profiled in that configuration
    print(pivot.fillna('-').to_string())
    
    print("\n\nCOMPARISON TABLE: Excl_Max % of Total Time")
    print("-" * 80)
    pivot_pct = df.pivot(index='Function', columns='Configuration', values='Excl_Max_Pct')
    print(pivot_pct.fillna('-').to_string())
    
    # Comparison table - Inclusive
    if 'Incl_Avg' in df.columns:
        print("\n\nCOMPARISON TABLE: Incl_Avg (seconds)")
        print("-" * 80)
        pivot_incl = df.pivot(index='Function', columns='Configuration', values='Incl_Avg')
        print(pivot_incl.fillna('-').to_string())
        
        print("\n\nCOMPARISON TABLE: Incl_Max % of Total Time")
        print("-" * 80)
        pivot_incl_pct = df.pivot(index='Function', columns='Configuration', values='Incl_Max_Pct')
        print(pivot_incl_pct.fillna('-').to_string())
    
    print("\n\nCOMPARISON TABLE: Number of Calls")
    print("-" * 80)
    pivot_ncalls = df.pivot(index='Function', columns='Configuration', values='NCalls')
    print(pivot_ncalls.fillna('-').to_string())


def save_results_to_csv(df, output_file):
    """Save results to CSV file."""
    df.to_csv(output_file, index=False)
    print(f"\n\nResults saved to: {output_file}")


def main():
    # Directory containing profiling files
    base_dir = Path(__file__).parent
    profiling_dir = base_dir / f'profile_{TIMESTEPS}'
    
    if not profiling_dir.exists():
        print(f"Error: {profiling_dir} not found!")
        return
    
    # Functions of interest
    functions_of_interest = [
        'SprayParticleContainer::updateParticles()',
        'PeleLMeX::advance::scalars_adv',
        'PeleLMeX::calcDiffusivity()',
        'PeleLMeX::getDiffusivity()',
        'PeleLMeX::Advance()',
        'PeleLMeX::advance::diffusion'
    ]
    
    # Analyze the profiling files
    print(f"Analyzing profiling files in: {profiling_dir}")
    print(f"Looking for {len(functions_of_interest)} functions of interest...")
    
    df = analyze_profiling_directory(profiling_dir, functions_of_interest)
    
    if df.empty:
        print("No data found for the specified functions!")
        return
    
    # Print summary
    print_summary(df)
    
    # Save to CSV
    output_file = profiling_dir / f'profiling_analysis_summary_{TIMESTEPS}.csv'
    save_results_to_csv(df, output_file)


if __name__ == '__main__':
    main()
