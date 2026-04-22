# trace generated using paraview version 5.13.2
#import paraview
#paraview.compatibility.major = 5
#paraview.compatibility.minor = 13

#### import the simple module from the paraview
from paraview.simple import *
import csv
import os
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# This script calculates 1 / A * integral(var dA) from z_min to z = 0.95
# fuels = 'e1-ssjf2', 'e2-sajf3', 'posf10264', 'we-hefa' (use gc-to-surr1)

# Time 20 ms, test for 2 fuels
#fuelNames = ['posf10264', 'posf10264']
#modelNames = ['gc-to-gc', 'gc-to-surr']
#pltFileNames = ['plt34886', 'plt34835']
#times = '20ms'

# Time 20 ms, remaining fuels
fuelNames = ['e1-ssjf2', 'e2-sajf3', 'we-hefa']
modelNames = ['gc-to-surr', 'gc-to-surr', 'gc-to-surr1']
pltFileNames = ['pltAvg_e1-ssjf2_gc-to-surr_35-40', 'pltAvg_e2-sajf3_gc-to-surr_35-40', 'pltAvg_we-hefa_gc-to-surr1_35-40']
times = '35ms-40ms'

#fuelNames =    ['posf10264', 'e1-ssjf2', 'e2-sajf3', 'we-hefa']
#modelNames =   ['gc-to-surr', 'gc-to-surr', 'gc-to-surr', 'gc-to-surr1']
#pltFileNames = ['plt34835',  'plt34805', 'plt35003', 'plt34733']
#times = '40ms'


outputLocation = f'/Users/dmontgo2/Documents/Pele-Cases/PrefVaporizationEffects-Study/Figures/average_spray_plots/data_paraview_integrals_{times}'


max_level = 2
dz = 0.4445*2/(64*2**2)
z_min = 0.7886565 + dz/2  # Start at center of first cell
z_max = 0.95
z_locations = [round(z_min + i*dz, 5) for i in range(int((z_max - z_min)/dz) + 1)]

# Create render view once, before the loop
renderView1 = GetActiveViewOrCreate('RenderView')
materialLibrary1 = GetMaterialLibrary()

for fuelName, modelName, pltFileName in zip(fuelNames, modelNames, pltFileNames):
    print(f"\nProcessing fuel: {fuelName}, model: {modelName}")

    pltFileLocation = f'/lustre/orion/cmb152/proj-shared/dmontgo2/PrefEvapStudy/A74_PeleLMeX/output_{fuelName}_{modelName}'
    output_file = f'{outputLocation}/integrated_{fuelName}_{modelName}.csv'

    # create a new 'AMReX/BoxLib Grid Reader'
    pltSource = AMReXBoxLibGridReader(registrationName='pltFileName', FileNames=[f'{pltFileLocation}/{pltFileName}'])

    # Properties modified on pltSource
    pltSource.Level = 2

    # show data in view
    pltSourceDisplay = Show(pltSource, renderView1, 'AMRRepresentation')

    # trace defaults for the display properties.
    pltSourceDisplay.Representation = 'Outline'

    # reset view to fit data
    renderView1.ResetCamera(False, 0.9)

    # update the view to ensure updated data information
    renderView1.Update()

    renderView1.ResetActiveCameraToPositiveX()

    # reset view to fit data
    renderView1.ResetCamera(False, 0.9)

    renderView1.AdjustRoll(-90.0)

    # create a new 'Coordinates' filter (replacement for deprecated AppendLocationAttributes)
    coordinatesFilter = Coordinates(registrationName='Coordinates', Input=pltSource)

    # show data in view
    coordinatesDisplay = Show(coordinatesFilter, renderView1, 'AMRRepresentation')

    # trace defaults for the display properties.
    coordinatesDisplay.Representation = 'Outline'

    # hide data in view
    Hide(pltSource, renderView1)

    # update the view to ensure updated data information
    renderView1.Update()

    # Storage for integrated data
    integrated_data = []

    # Loop over z locations and create slices
    for z_loc in z_locations:
        print(f"Creating slice for z_loc = {z_loc}")
        
        # create a new 'Slice'
        slice1 = Slice(registrationName=f'Slice_z{z_loc}', Input=coordinatesFilter)

        # Properties modified on slice1.SliceType
        slice1.SliceType.Origin = [0.0, 0.0, z_loc]
        slice1.SliceType.Normal = [0.0, 0.0, 1.0]

        # show data in view
        slice1Display = Show(slice1, renderView1, 'GeometryRepresentation')

        # trace defaults for the display properties.
        slice1Display.Representation = 'Surface'

        # update the view to ensure updated data information
        renderView1.Update()

        # set scalar coloring
        ColorBy(slice1Display, ('FIELD', 'vtkBlockColors'))

        # show color bar/color legend
        slice1Display.SetScalarBarVisibility(renderView1, True)

        # get color transfer function/color map for 'vtkBlockColors'
        vtkBlockColorsLUT = GetColorTransferFunction('vtkBlockColors')

        # get opacity transfer function/opacity map for 'vtkBlockColors'
        vtkBlockColorsPWF = GetOpacityTransferFunction('vtkBlockColors')

        # get 2D transfer function for 'vtkBlockColors'
        vtkBlockColorsTF2D = GetTransferFunction2D('vtkBlockColors')

        # Properties modified on slice1
        slice1.Triangulatetheslice = 0

        # update the view to ensure updated data information
        renderView1.Update()

        # create a new 'Integrate Variables'
        integrateVariables1 = IntegrateVariables(registrationName=f'IntegrateVariables_z{z_loc}', Input=slice1)

        # Properties modified on integrateVariables1
        integrateVariables1.DivideCellDataByVolume = 1

        # update the pipeline
        renderView1.Update()
        
        # Create a spreadsheet view to extract integrated data
        spreadSheetView = CreateView('SpreadSheetView')
        spreadSheetView.FieldAssociation = 'Cell Data'
        
        # show integrated data in spreadsheet view
        Show(integrateVariables1, spreadSheetView)
        
        # update view
        spreadSheetView.Update()
        
        # Export to temporary CSV
        temp_csv = f'/tmp/integrate_z{z_loc:.2f}.csv'
        try:
            ExportView(temp_csv, view=spreadSheetView)
            print(f"  Exported integration data to temporary CSV")
            
            # Read back the CSV and extract values
            if os.path.exists(temp_csv):
                with open(temp_csv, 'r') as f:
                    # Skip header
                    lines = f.readlines()
                    if len(lines) > 1:
                        # Parse the data row
                        row_data = {'z_location': z_loc}
                        # Get header
                        header = lines[0].strip().split(',')
                        # Get data
                        data = lines[1].strip().split(',')
                        for col, val in zip(header, data):
                            if col.strip() and col.strip() != '':
                                try:
                                    row_data[col.strip()] = float(val)
                                except:
                                    row_data[col.strip()] = val
                        integrated_data.append(row_data)
                        print(f"  Extracted {len(row_data)-1} variables from slice")
        except Exception as e:
            print(f"  Error exporting data: {e}")
        finally:
            # Clean up
            Delete(spreadSheetView)
            Delete(integrateVariables1)
            Delete(slice1)
            renderView1.Update()

    # Create DataFrame and export to CSV
    if integrated_data:
        # Get all unique column names
        all_columns = set()
        for row in integrated_data:
            all_columns.update(row.keys())
        
        # Remove z_location from the set and add it to the front
        all_columns.discard('z_location')
        columns = ['z_location'] + sorted(list(all_columns))
        
        # Export to CSV using standard csv module
        try:
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                for row in integrated_data:
                    # Ensure all values are present, fill missing with empty string
                    row_out = {col: row.get(col, '') for col in columns}
                    writer.writerow(row_out)
            
            print(f"\nIntegrated data exported to: {output_file}")
            print(f"Rows: {len(integrated_data)}")
            print(f"Columns: {columns}")
        except Exception as e:
            print(f"Error writing CSV: {e}")
    else:
        print("No integrated data collected")
    
    # Clean up all created objects for this fuel
    Delete(coordinatesDisplay)
    Delete(coordinatesFilter)
    Delete(pltSourceDisplay)
    Delete(pltSource)
    renderView1.Update()

print("\nScript completed successfully!")