import csv
from datetime import timedelta, datetime

def _write_header_if_needed(filename, variables):
    """Write the CSV header if the file does not exist or is empty."""
    try:
        # Check if file exists and is non-empty
        with open(filename, 'r', newline='') as f:
            if f.read(1):
                return  # Header already present
    except FileNotFoundError:
        pass  # File doesn't exist yet, we'll create it with header

    # Build and write header row
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
    Run a long simulation in chunks, flushing to CSV periodically to avoid data loss.

    :param timeline:       K-Spice Timeline object
    :param selected_app:   Name of the application within the timeline
    :param variables:      List of [variable_name, unit] pairs to sample
    :param total_minutes:  Total simulation duration in minutes
    :param chunk_size:     Number of samples to collect before writing to file
    :param filename:       Path to the CSV file for output
    """
    total_seconds = total_minutes * 60
    buffer = []

    # Ensure the CSV header is in place
    _write_header_if_needed(filename, variables)

    try:
        for second in range(1, total_seconds + 1):
            # Advance simulation by 1 second
            timeline.run_for(timedelta(seconds=1))
            sample = timeline.get_values(selected_app, variables)
            sample.insert(0, timeline.model_time.total_seconds())
            buffer.append(sample)

            # Flush buffer to file when it reaches chunk_size
            if len(buffer) >= chunk_size:
                _flush_buffer(filename, buffer)
                buffer.clear()

        # Flush any remaining samples after loop completion
        if buffer:
            _flush_buffer(filename, buffer)
            buffer.clear()

    except Exception as e:
        # On error, flush what's left in the buffer before re-raising
        if buffer:
            _flush_buffer(filename, buffer)
        print(f"[ERROR] Simulation interrupted: {e!r}")
        raise


# === Example usage ===
project_name = "DemoProject"
state = 0
date_str = datetime.now().strftime("%d.%m.%Y_%H-%M")
filename = f"{project_name}_state{state}_{date_str}.csv"

# Simulate for 24 hours (1440 minutes), flushing every 500 samples
run_long_simulation(
    timeline=tl,
    selected_app=selected_app,
    variables=variables,
    total_minutes=1440,
    chunk_size=500,
    filename=filename
)
