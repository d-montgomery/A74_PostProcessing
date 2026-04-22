import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

save_fig = True
posf_only = False
min_time = 55
max_time = 60

ignore_fuel = ['e2-sajf3']
ignore_fuel = ['']
add_line_symbols = False
marker_size = 8

color_scheme = 'blues' # Options: 'blues', 'purples', 'default'


inlet_z = 0.7886565 # inlet location 
max_z = 1
max_z = 0.7886565 + 0.12 # (m)
print(f"Filtering data to z <= {max_z} m")

vars = ['spray_density']
var_label = {'spray_mass': 'Total Spray Mass', 'spray_vol':'Total Spray Volume', 'spray_density':'Spray Density'}

fsize = 16
# Get all integrated CSV files
if min_time == max_time:
    data_dir = Path(f'data_paraview_integrals_{min_time}ms')
else:
    data_dir = Path(f'data_paraview_integrals_{min_time}ms-{max_time}ms')
csv_files = sorted(data_dir.glob('integrated_*.csv'))

print(f"Found {len(csv_files)} integrated CSV files")

# Line specifications for plotting
def linespecs(name):
    line_style = "-"
    if ("posf10264".lower() in name):
        color="#7f7f7f"
        lab="NJFCP JP8"
        if posf_only:
            lab = "JP8"
            if "gc-to-gc" in name:
                lab+=": GC-to-GC"
                color="indigo"
                line_style="-"
            elif "gc-to-surr" in name:
                lab+=": GC-to-Surrogate"
                if color_scheme == 'blues':
                    color="#7f7f7f"
                elif color_scheme == 'purples':
                    color="rebeccapurple"
                line_style="-."
            elif "gc-to-hychem" in name:
                lab+=": GC-to-Hychem"
                color="mediumpurple"
                line_style="-."
            elif "surr-to-surr" in name:
                lab+=": Surrogate-to-Surrogate"
                color="steelblue"
                line_style="--"
            elif "surr-to-hychem" in name:
                lab+=": Surrogate-to-HyChem"
                color="skyblue"
                line_style="--"
            elif "hychem-to-hychem" in name:
                lab+=": HyChem-to-HyChem"
                color="#333333"
                line_style=":"
    elif ("E1-SSJF2".lower() in name):
        if color_scheme == 'blues':
            color="#2980B9"
        else:
            color="tab:orange"
        lab="DLR FT Blend"
    elif ("E2-SAJF3".lower() in name):
        color="#91BCD8"
        lab="DLR HEFA Blend"
    elif ("we-hefa" in name):
        color="#063C61"
        lab="HEFA"
    else:
        color="black"
        lab=""
    if "gc-to-surr" in name:
        if "posf10264" in name:
            marker = 'o'
        elif "e1-ssjf2" in name:
            marker = 's'
        elif "e2-sajf3" in name:
            marker = 'D'
        elif "we-hefa" in name:
            marker = '^'
        else:
            marker = 'o'
    else:
        marker = None
    return color, lab, line_style, marker

# Parse files and group by fuel
fuel_data = {}  # {fuel_label: {'z_values': [], 'spray_mass': [], 'spray_vol': [], 'color': ...}}

for file in csv_files:
    # Parse filename to extract fuel and model
    # Pattern: integrated_{fuel}_{model}.csv
    match = re.search(r'integrated_(.+?)_(.+?)\.csv$', file.name)
    if not match:
        print(f"Warning: Could not parse filename {file.name}")
        continue
    
    fuel_name = f'{match.group(1)}_{match.group(2)}'
    fuel_base = match.group(1)  # just the fuel part, e.g. 'e2-sajf3'

    if posf_only and "posf10264" not in fuel_name.lower():
        print(f"Skipping {file.name} because it does not match POSF10264")
        continue
    
    if not posf_only and "gc-to-surr" not in fuel_name.lower():
        print(f"Skipping {file.name} because it does not match GC-to-Surrogate")
        continue
    
    if any(ign and ign.lower() in fuel_base.lower() for ign in ignore_fuel):
        print(f"Skipping {file.name} because it is in the ignore list")
        continue
    
    # Read the integrated data CSV
    try:
        df = pd.read_csv(file)
    except Exception as e:
        print(f"Error reading {file.name}: {e}")
        continue
    
    print(f"  {file.stem}: {df.shape[0]} rows, fuel={fuel_name}")
    
    # Check if CellCenters_2 column exists
    if 'CellCenters_2' not in df.columns:
        print(f"    Warning: CellCenters_2 column not found in {file.name}")
        continue

    # Limit dataframe to data within max_z
    df = df[df['CellCenters_2'] <= max_z]
    
    # Get fuel label and color
    color, fuel_label, line_style, marker = linespecs(fuel_name)
    
    # Initialize storage for this fuel if not already present
    if fuel_label not in fuel_data:
        fuel_data[fuel_label] = {'color': color, 'z_values': [], 'line_style': line_style, 'marker': marker}
    
    # Extract data directly - no filtering or calculation needed
    fuel_data[fuel_label]['z_values'] = df['CellCenters_2'].tolist()
    
    # Get var if it exists
    for var in vars:
        if var in df.columns:
            fuel_data[fuel_label][var] = df[var].tolist()
        else:
            print(f"    Warning: {var} column not found in {file.name}")
    if 'Area' in df.columns:
        fuel_data[fuel_label]['Area'] = df['Area'].tolist()
    else:
        print(f"    Warning: Area column not found in {file.name}")

# Get normalization constants for each variable
norm_constants = {}
for var in vars:
    x = 0
    x = max([max(fuel_data[fuel_label][var]) for fuel_label in fuel_data if var in fuel_data[fuel_label]], default=1)
    norm_constants[var] = x
    print(f"Normalization constant for {var}: {x}")

# Create plots
for var in vars:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))

    # Plot each fuel as a line with points, sorted by largest peak value first
    sorted_fuels = sorted(fuel_data.items(), key=lambda item: max(item[1][var]) if var in item[1] else 0, reverse=True)
    for fuel_label, data in sorted_fuels:
        z_vals = data['z_values']
        
        # Get the appropriate variable data
        values_list = []
        for k in range(len(data[var])):
            values_list.append(data[var][k] / norm_constants[var])

        
        # Create pairs and sort by z
        valid_pairs = [(z, v) for z, v in zip(z_vals, values_list) if v is not None and v != '']
        if not valid_pairs:
            continue
        
        sorted_pairs = sorted(valid_pairs)
        z_sorted = [z for z, _ in sorted_pairs]
        values_sorted = [v for _, v in sorted_pairs]
        
        # Scale values
        z_scaled = [(z - inlet_z)*100 for z in z_sorted]
        #values_scaled = [v*yscale[var] for v in values_sorted]
        
        marker = data['marker'] if add_line_symbols else None
        markersize = marker_size if add_line_symbols else 8
        ax.plot(z_scaled, values_sorted, data['line_style'], color=data['color'], linewidth=2, marker=marker, markersize=markersize, label=fuel_label)

    ax.set_xlabel('Distance from Inlet (cm)', fontsize=fsize)
    ax.set_ylabel(f'Normalized {var_label[var]}', fontsize=fsize)
    ax.tick_params(labelsize=fsize)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=fsize-2, loc='best')

    # Save plot
    if min_time == max_time:
        filename = f'integrated_{var}_{min_time}ms'
    else:
        filename = f'integrated_{var}_{min_time}ms-{max_time}ms'
    if posf_only:
        filename += '_jp8_only'
    filename += '.png'
    plt.tight_layout()
    if save_fig:
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved: {filename}")
    plt.show()
