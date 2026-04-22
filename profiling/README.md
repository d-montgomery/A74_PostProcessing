# Profiling Analysis

The profiling analysis scripts process profile output files from PeleLMeX simulations. Profiling data should be organized in directories with the following format: `profile_<timesteps>` (e.g., `profile_10`, `profile_100`).

## Scripts

- `cleanup_profile_files.py` - Cleans up profile output files by removing unnecessary sections and extracting particle count metadata.
- `analyze_profiling.py` - Analyzes cleaned profile files and extracts timing statistics for key functions. Outputs results to CSV.
- `visualize_profiling.py` - Creates visualizations (bar charts) from the profiling analysis CSV.

Edit the `TIMESTEPS` variable at the top of each script to analyze different timestep directories.
