import csv
from datetime import timedelta, datetime

def _write_header_if_needed(filename, variables):
    """Write the CSV header if the file does not exist or is empty."""
    try:
        with open(filename, 'r', newline='') as f:
            if f.read(1):
                return
    except FileNotFoundError:
        pass

    header = [['ModelTime', 's']] + variables
    header_flat = [f"{var[0]} [{var[1]}]" for var in header]
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header_flat)


def _flush_buffer(filename, buffer):
    """Append all rows in the buffer to the CSV file."""
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(buffer)


def run_long_simulation(
        timeline,
        selected_app,
        variables,
        total_minutes,
        chunk_size,
        filename
    ):
    """
    Run a long simulation in chunks, flushing to CSV periodically to avoid data loss,
    and print progress at 25% intervals.

    :param timeline:       K-Spice Timeline object
    :param selected_app:   Name of the application within the timeline
    :param variables:      List of [variable_name, unit] pairs to sample
    :param total_minutes:  Total simulation duration in minutes
    :param chunk_size:     Number of samples to collect before writing to file
    :param filename:       Path to the CSV file for output
    """
    total_seconds = total_minutes * 60
    buffer = []

    # print start message
    print("simulation started, Progress 0%")

    # prepare progress checkpoints at 25%, 50%, 75%, and 100%
    checkpoints = [
        int(total_seconds * 0.25),
        int(total_seconds * 0.50),
        int(total_seconds * 0.75),
        total_seconds
    ]
    next_cp = 0

    _write_header_if_needed(filename, variables)

    try:
        for second in range(1, total_seconds + 1):
            # advance simulation by 1 second
            timeline.run_for(timedelta(seconds=1))
            sample = timeline.get_values(selected_app, variables)
            sample.insert(0, timeline.model_time.total_seconds())
            buffer.append(sample)

            # flush buffer if needed
            if len(buffer) >= chunk_size:
                _flush_buffer(filename, buffer)
                buffer.clear()

            # print progress at each checkpoint
            if next_cp < len(checkpoints) and second == checkpoints[next_cp]:
                print(f"progres {25 * (next_cp + 1)}%")
                next_cp += 1

        # flush any remaining samples
        if buffer:
            _flush_buffer(filename, buffer)
            buffer.clear()

        # print completion message
        print(f"Simulation completed successfully, file saved as: {filename}")

    except Exception as e:
        # on error, flush what's left then notify and re-raise
        if buffer:
            _flush_buffer(filename, buffer)
        print(f"[ERROR] Simulation interrupted: {e!r}")
        print(f"Unexpected error, file saved as: {filename}")
        raise


##################################################################################################################################################
######################################### Initializing the K-Spice Simulator #####################################################################
##################################################################################################################################################

project_path = r"C:\K-Spice-Projects\Yggdrasil Hugin LATEST_Eryk_2"  # Path for project folder

timeline = "Yggdrasil_LCS"                        # Name of the timeline to be activated
mdlFile  = "Yggdrasil"                            # Name of the model file to be loaded
prmFile  = "Yggdrasil"                            # Name of the parameter file to be loaded
valFile  = "Yggdrasil_Steady_State_Manual_Mode"   # Name of the initial conditions file to be loaded

# Instantiate the simulator object 
sim = kspice.Simulator(project_path)

# Open the project and load the timeline 
tl = sim.activate_timeline(timeline)

# Load models, parameters, initial_conditions
tl.load(mdlFile, prmFile, valFile)

# Initialize the timeline
tl.initialize()

# Different applications 
selected_app = tl.applications[0].name           # Hugin A
selected_app1 = tl.applications[1].name          # Hugin B

# Set the execution speed of the timeline to 2.0X real time
tl.set_speed(2.0)

# === Your variables list ===
variables = [
    ["D-36L00040A-1200PRd:OutletStream.f",   "kg/h"],
    ["D-13HCV2319:TargetPosition",          "%"],
    ["D-13HCV2419:TargetPosition",          "%"],
    ["D-13HCV2121A:TargetPosition",         "%"],
    ["D-13HCV2121B:TargetPosition",         "%"],
    ["D-13HCV0305:TargetPosition",          "%"],
    ["F-18FCV0105:TargetPosition",          "%"],
    ["N-18FCV0105_RD1:TargetPosition",      "%"],
    ["N-18FCV0105_LF1:TargetPosition",      "%"],
    ["G-13HCV0505:TargetPosition",          "%"],
    ["D-27PIC0101:InternalSetpoint",        "barg"],
    ["D-27TIC0106:InternalSetpoint",        "C"],
    ["D-24PIC0002:InternalSetpoint",        "barg"],
    ["D-26PIC0056:InternalSetpoint",        "barg"],
    ["D-20PIC0304:InternalSetpoint",        "barg"],
    ["D-21L00007A-1400PL-BD20a:OutletStream.f", "kg/h"],
    ["D-21L00007A-1400PL-BD20a:OutletStream.q", "m3/h"],
    ["D-21L00007A-1400PL-BD20a:OutletStream.w", "kg/mol"],
]

# === Example usage ===
project_name = "DemoProject"
state = 0
date_str = datetime.now().strftime("%d.%m.%Y_%H-%M")
filename = f"{project_name}_state{state}_{date_str}.csv"

# simulate 10 minutes (for testing), flush every 500 samples, print progress at each 25%
run_long_simulation(
    timeline=tl,
    selected_app=selected_app,
    variables=variables,
    total_minutes=10,
    chunk_size=500,
    filename=filename
)
