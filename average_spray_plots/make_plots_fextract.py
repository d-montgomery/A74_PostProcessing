import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

# inlet location 
inlet_z = 0.7886565

z_locations = [0.81, 0.86, 0.91]

# Line specifications for plotting (from mixtureProps.py)
def linespecs(name):
    if ("posf10264".lower() in name):
        color="#7f7f7f" # Primary Blue
        lab="NJFCP JP8"
    elif ("E1-SSJF2".lower() in name):
        color="#2980B9" # Dark Gray
        lab="DLR FT Blend"
    elif ("E2-SAJF3".lower() in name):
        color="#91BCD8" # 50% Gray
        lab="DLR HEFA Blend"
    elif ("we-hefa" in name):
        color="#063C61" # WE HEFA
        lab="WE HEFA"
    else:
        color="black"
        lab=""
    return color, lab

# Get all CSV files in the fextract_all_levels subdirectory
data_dir = Path('fextract_data')
csv_files = sorted(data_dir.glob('line_*.csv'))

print(f"Found {len(csv_files)} CSV files")

# Read the data
dfs = {}
for file in csv_files:
    # Read the header line (3rd line) and remove the '#' prefix
    with open(file, 'r') as f:
        f.readline()  # Skip first comment line
        f.readline()  # Skip second comment line
        header_line = f.readline()  # Read the header line
    
    # Remove the '#' prefix and parse the column names
    header_line = header_line.lstrip('#').strip()
    column_names = header_line.split()
    
    # Make column names unique by appending a counter to duplicates
    seen = {}
    unique_names = []
    for name in column_names:
        if name in seen:
            seen[name] += 1
            unique_names.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            unique_names.append(name)
    
    # Read the data, skipping the first 3 lines (2 comments + 1 header)
    df = pd.read_csv(file, skiprows=3, sep=r'\s+', engine='python', header=None, names=unique_names)
    
    # Drop columns that match spray_*_src pattern
    cols_to_drop = [col for col in df.columns if col.startswith('spray_') and col.endswith('_src')]
    df = df.drop(columns=cols_to_drop)
    
    dfs[file.stem] = df
    print(f"  {file.stem}: {df.shape[0]} rows")

# Parse filename to extract type (pilot/premix) and z value
plot_groups = {}  # Dictionary: (type, z_value) -> list of (filename_stem, df)

for stem, df in dfs.items():
    # Extract type and z value from filename
    # Pattern: line_{type}_x..._z{z_value}_{fuel}...
    match = re.search(r'line_(pilot|premix)_.*_z([\d.]+)_', stem)
    if match:
        plane = match.group(1)
        z_value = float(match.group(2))
        key = (plane, z_value)
        
        if key not in plot_groups:
            plot_groups[key] = []
        plot_groups[key].append((stem, df))

# Sort the groups: pilot first, then premix, and within each, sort by z value
sorted_keys = sorted(plot_groups.keys(), key=lambda x: (x[0] != 'pilot', x[1]))

# Create 6 separate plots
for idx, key in enumerate(sorted_keys):
    plane, z_value = key
    
    if z_value in z_locations:
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Group files by fuel type
        fuel_groups = {}
        for stem, df in plot_groups[key]:
            color, lab = linespecs(stem)
            
            # Use the label as the fuel group key
            if lab not in fuel_groups:
                fuel_groups[lab] = {'color': color, 'dfs': []}
            fuel_groups[lab]['dfs'].append(df)
        
        # Plot each fuel group with a single legend entry
        for lab, fuel_data in fuel_groups.items():
            color = fuel_data['color']
            # Concatenate all dataframes for this fuel
            combined_df = pd.concat(fuel_data['dfs'], ignore_index=True)
            ax.scatter(combined_df['y']*100, combined_df['spray_mass']*1e9, alpha=0.9, s=20, color=color, label=lab)
        
        ax.set_xlabel('y (cm)', fontsize=12)
        ax.set_ylabel('Spray Mass ($\mu$g)', fontsize=12)
        ax.set_title(f'Line Over {plane.capitalize()} Plane at z = {z_value*100} cm', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10, loc='best')
        
        # Save each plot separately
        filename = f'spray_mass_{plane}_z{z_value}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {filename}")

# Create 2 plots: cumulative spray_mass vs z for pilot and premix
for plane_type in ['pilot', 'premix']:
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Group by fuel across all z values for this plane type
    fuel_z_total = {}  # fuel_label -> {z_value -> average_spray_mass}
    
    for (plane, z_value), file_list in plot_groups.items():
        if plane != plane_type:
            continue
        
        for stem, df in file_list:
            color, lab = linespecs(stem)
            
            if lab not in fuel_z_total:
                fuel_z_total[lab] = {'color': color, 'z_values': [], 'totals': []}
            
            total_spray_mass = df['spray_mass'].sum()
            fuel_z_total[lab]['z_values'].append(z_value)
            fuel_z_total[lab]['totals'].append(total_spray_mass)
    
    # Plot each fuel as a line with points
    for lab, data in fuel_z_total.items():
        # Sort by z_value
        sorted_pairs = sorted(zip(data['z_values'], data['totals']))
        z_vals = [(z - inlet_z)*100 for z, _ in sorted_pairs]
        totals = [m*1e9 for _, m in sorted_pairs]
        
        ax.plot(z_vals, totals, 'o-', color=data['color'], linewidth=2, markersize=8, label=lab)
    
    ax.set_xlabel('Distance from Inlet (cm)', fontsize=12)
    ax.set_ylabel('Total Spray Mass ($\mu$g)', fontsize=12)
    ax.set_title(f'Total Spray Mass Along {plane_type.capitalize()} Plane', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')
    
    # Save plot
    filename = f'spray_mass_total_{plane_type}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filename}")
