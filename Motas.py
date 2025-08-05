import csv
from datetime import timedelta, datetime
import kspice

# -----------------------------------------------------------------------------
# Module: Buffered Switch-Case Simulation
# Description: Runs K-Spice simulations in sequential states, adjusting parameters
#              between runs, and writes results to separate CSV files using a
#              chunked buffer strategy to minimize data loss on failure.
# -----------------------------------------------------------------------------

# --- CSV Buffering Helpers ---
def _write_header_if_needed(filename, variables):
    """
    Write the CSV header if the file does not exist or is empty.

    Params:
        filename (str): Path to the CSV file.
        variables (List[List[str, str]]): List of [name, unit] pairs for columns.
    """
    try:
        with open(filename, 'r', newline='') as f:
            # If file already has content, skip writing header
            if f.read(1):
                return
    except FileNotFoundError:
        # File does not exist -> will write header
        pass

    header = [['ModelTime', 's']] + variables
    # Flatten header to "Name [unit]" format
    header_flat = [f"{var[0]} [{var[1]}]" for var in header]
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header_flat)


def _flush_buffer(filename, buffer):
    """
    Append all rows in the buffer to the CSV file and clear the buffer.

    Params:
        filename (str): Path to the CSV file.
        buffer (List[List[float]]): Rows to flush to disk.
    """
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(buffer)
    # Caller should clear buffer after flush


def run_buffered_simulation(timeline, app, variables, minutes, chunk_size, filename):
    """
    Run a chunked simulation for a given duration, writing results in increments
    to CSV to avoid data loss on errors or process termination.

    Params:
        timeline (kspice.Timeline): Active K-Spice timeline object.
        app (str): Application name within the timeline.
        variables (List[List[str, str]]): Variables to sample ([name, unit]).
        minutes (int): Simulation duration in minutes.
        chunk_size (int): Number of samples to buffer before writing.
        filename (str): Output CSV file path.
    """
    total_seconds = minutes * 60
    buffer = []

    # Progress checkpoints at 25%, 50%, 75%, 100%
    checkpoints = [
        int(total_seconds * 0.25),
        int(total_seconds * 0.50),
        int(total_seconds * 0.75),
        total_seconds
    ]
    next_cp = 0

    # Ensure CSV header is present
    _write_header_if_needed(filename, variables)
    print(f"Starting {minutes}min simulation (chunk {chunk_size}) → {filename}")

    try:
        for sec in range(1, total_seconds + 1):
            # Advance simulation by one second
            timeline.run_for(timedelta(seconds=1))
            # Sample variables and prepend model time
            sample = timeline.get_values(app, variables)
            sample.insert(0, timeline.model_time.total_seconds())
            buffer.append(sample)

            # Flush to disk if buffer is full
            if len(buffer) >= chunk_size:
                _flush_buffer(filename, buffer)
                buffer.clear()

            # Print progress at defined checkpoints
            if next_cp < len(checkpoints) and sec == checkpoints[next_cp]:
                print(f"  Progress {25 * (next_cp + 1)}%...")
                next_cp += 1

        # Final flush of any remaining rows
        if buffer:
            _flush_buffer(filename, buffer)
            buffer.clear()

        print(f"Completed {minutes}min simulation → data in {filename}")

    except Exception as e:
        # On error, flush what's left, log, then re-raise
        if buffer:
            _flush_buffer(filename, buffer)
        print(f"[ERROR] Simulation failed: {e!r}")
        print(f"Partial data flushed to {filename}")
        raise


# --- Parameter Adjustment Helper ---
def adjust_parameter(timeline, app, parameter_name, multiplier):
    """
    Multiply a control parameter by a given factor and update the timeline.

    Params:
        timeline (kspice.Timeline): Active timeline object.
        app (str): Application name.
        parameter_name (str): Name of the parameter to adjust.
        multiplier (float): Factor to multiply the current value by.
    """
    current = timeline.get_value(app, parameter_name)
    new_val = current * multiplier
    timeline.set_value(app, parameter_name, new_val)
    print(f"Adjusted {parameter_name}: {current} → {new_val} ({multiplier*100:.1f}%)")


# --- Filename Generator ---
def generate_filename(project_name, state):
    """
    Create a filename with project name, state index, and timestamp.

    Params:
        project_name (str): Base name for the project.
        state (int): Simulation state index.

    Returns:
        str: Generated filename.
    """
    ts = datetime.now().strftime("%d.%m.%Y_%H-%M")
    return f"{project_name}_state{state}_{ts}.csv"


# --- Main Simulation Flow ---
if __name__ == "__main__":
    # Initialize simulator
    project_path = r"C:\K-Spice-Projects\Yggdrasil Hugin LATEST_Eryk_2"
    sim = kspice.Simulator(project_path)
    tl  = sim.activate_timeline("Yggdrasil_LCS")
    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
    tl.initialize()
    tl.set_speed(2.0)

    # Application names
    app0 = tl.applications[0].name  # Hugin A
    app1 = tl.applications[1].name  # Hugin B

    # Variables to sample: [name, unit]
    variables = [
        ["D-13HCV2627:TargetPosition","%"],
        # ... rest of your variable list ...
        ["D-13PT2122:MeasuredValue","barg"],
    ]

    project_name = "Yggdrasil"
    chunk_size   = 500
    state        = 0

    print("=== Starting buffered switch-case simulation ===")

    # Loop through states as experiments
    while True:
        try:
            match state:
                case 0:
                    # State 0: 2min, adjust valve, 180min
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 0 ---")
                    run_buffered_simulation(tl, app1, variables, 2,   chunk_size, filename)
                    adjust_parameter(tl, app1, "G-13HCV0505:TargetPosition", 1.1)
                    run_buffered_simulation(tl, app1, variables, 180, chunk_size, filename)
                    state = 1

                case 1:
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 1 ---")
                    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
                    tl.initialize()
                    run_buffered_simulation(tl, app0, variables, 60,  chunk_size, filename)
                    adjust_parameter(tl, app0, "D-27PIC0101:InternalSetpoint", 1.1)
                    run_buffered_simulation(tl, app0, variables, 180, chunk_size, filename)
                    state = 2

                case 2:
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 2 ---")
                    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
                    tl.initialize()
                    run_buffered_simulation(tl, app0, variables, 60,  chunk_size, filename)
                    adjust_parameter(tl, app0, "D-27TIC0106:InternalSetpoint", 1.1)
                    run_buffered_simulation(tl, app0, variables, 180, chunk_size, filename)
                    state = 3

                case 3:
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 3 ---")
                    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
                    tl.initialize()
                    run_buffered_simulation(tl, app0, variables, 60,  chunk_size, filename)
                    adjust_parameter(tl, app0, "D-24PIC0002:InternalSetpoint", 1.1)
                    run_buffered_simulation(tl, app0, variables, 180, chunk_size, filename)
                    state = 4

                case 4:
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 4 ---")
                    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
                    tl.initialize()
                    run_buffered_simulation(tl, app0, variables, 60,  chunk_size, filename)
                    adjust_parameter(tl, app0, "D-26PIC0056:InternalSetpoint", 1.1)
                    run_buffered_simulation(tl, app0, variables, 180, chunk_size, filename)
                    state = 5

                case 5:
                    filename = generate_filename(project_name, state)
                    print("\n--- STATE 5 ---")
                    tl.load("Yggdrasil", "Yggdrasil", "Yggdrasil_Steady_State_Manual_Mode")
                    tl.initialize()
                    run_buffered_simulation(tl, app0, variables, 60,  chunk_size, filename)
                    adjust_parameter(tl, app0, "D-20PIC0304:InternalSetpoint", 0.9)
                    run_buffered_simulation(tl, app0, variables, 180, chunk_size, filename)
                    print("\n=== Simulation complete! ===")
                    break

        except Exception as e:
            print(f"[FATAL] Interrupted in state {state}: {e!r}")
            break
