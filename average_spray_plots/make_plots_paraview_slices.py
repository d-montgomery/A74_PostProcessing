import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

# inlet location 
inlet_z = 0.7886565

vars = ['spray_mass', 'spray_vol']
var_label = {'spray_mass': 'Total Spray Mass', 'spray_vol':'Total Spray Volume'}
yscale = {'spray_mass': 1e9, 'spray_vol':1e6}
units = {'spray_mass': '$\mu$g', 'spray_vol':'cm$^3$'}

# Get all CSV files in the subdirectory
data_dir = Path('paraview_slices_surrs')
csv_files = sorted(data_dir.glob('*.csv'))

print(f"Found {len(csv_files)} CSV files")

# Line specifications for plotting (from mixtureProps.py)
def linespecs(name):
    if ("posf10264".lower() in name):
        color="#7f7f7f"
        lab="NJFCP JP8"
    elif ("E1-SSJF2".lower() in name):
        color="#2980B9"
        lab="DLR FT Blend"
    elif ("E2-SAJF3".lower() in name):
        color="#91BCD8"
        lab="DLR HEFA Blend"
    elif ("we-hefa" in name):
        color="#063C61"
        lab="WE HEFA"
    else:
        color="black"
        lab=""
    return color, lab

# Parse files and group by fuel and z-value
fuel_z_totals = {}  # {fuel_label: {z_value: total_mass}}

for file in csv_files:
    # Parse filename to extract z-value and fuel
    # Pattern: plane_z{z_value}_{fuel}...
    match = re.search(r'plane_z([\d.]+)_(.+?)(_points)?\.csv$', file.name)
    if not match:
        print(f"Warning: Could not parse filename {file.name}")
        continue
    
    z_target = float(match.group(1))
    fuel_name = match.group(2)
    
    # Read the CSV file
    try:
        df = pd.read_csv(file)
    except Exception as e:
        print(f"Error reading {file.name}: {e}")
        continue
    
    print(f"  {file.stem}: {df.shape[0]} rows, z_target={z_target}, fuel={fuel_name}")
    
    # Check if CellCenters:2 column exists
    if 'CellCenters:2' not in df.columns:
        print(f"    Warning: CellCenters:2 column not found in {file.name}")
        continue
    
    # Filter to rows closest to target z-value
    z_values = df['CellCenters:2'].values
    if len(np.unique(z_values)) > 1:
        unique_z = np.unique(z_values)
        print(f"    Warning: Multiple z values found in {file.name}, expected a single plane. Unique z values: {unique_z}")
        
        # Use the z-value that minimizes (z_value - z_target)^2
        closest_z_value = unique_z[np.argmin(np.abs(unique_z - z_target))]
        print(f"    Using closest z value: {closest_z_value}")
        z_values = np.full_like(z_values, closest_z_value)  # Override with closest

    closest_z_mask = np.abs(z_values - z_target) < 0.001  # within 0.001 of target
    
    if not closest_z_mask.any():
        # If no rows within tolerance, find the closest ones
        closest_indices = np.argsort(np.abs(z_values - z_target))[:min(100, len(z_values))]
        filtered_df = df.iloc[closest_indices]
    else:
        filtered_df = df[closest_z_mask]
    
    # Calculate totals
    total_mass = filtered_df['spray_mass'].sum() if 'spray_mass' in df.columns else None
    total_vol = filtered_df['spray_vol'].sum() if 'spray_vol' in df.columns else None
    
    if total_mass is None and total_vol is None:
        print(f"    Warning: spray_mass and spray_vol columns not found in {file.name}")
        continue
    
    # Get fuel label
    color, fuel_label = linespecs(fuel_name)
    
    # Store the total
    if fuel_label not in fuel_z_totals:
        fuel_z_totals[fuel_label] = {'color': color, 'z_values': [], 'total_mass': [], 'total_vol': []}
    
    fuel_z_totals[fuel_label]['z_values'].append(z_target)
    fuel_z_totals[fuel_label]['total_mass'].append(total_mass)
    fuel_z_totals[fuel_label]['total_vol'].append(total_vol)

# Create plots
for var in vars:
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot each fuel as a line with points
    for fuel_label, data in fuel_z_totals.items():
        # Sort by z_value
        z_vals_list = data['z_values']
        if var == 'spray_mass':
            totals_list = data['total_mass']
        else:  # spray_vol
            totals_list = data['total_vol']
        
        # Filter out None values
        valid_pairs = [(z, t) for z, t in zip(z_vals_list, totals_list) if t is not None]
        if not valid_pairs:
            continue
        
        sorted_pairs = sorted(valid_pairs)
        z_vals = [(z - inlet_z)*100 for z, _ in sorted_pairs]
        totals = [t*yscale[var] for _, t in sorted_pairs]
        
        ax.plot(z_vals, totals, 'o-', color=data['color'], linewidth=2, markersize=8, label=fuel_label)

    ax.set_xlabel('Distance from Inlet (cm)', fontsize=12)
    ax.set_ylabel(f'{var_label[var]} ({units[var]})', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')

    # Save plot
    filename = f'total_{var}_slices.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nPlot saved: {filename}")
