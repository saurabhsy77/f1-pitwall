import os

import fastf1
import matplotlib.pyplot as plt
import numpy as np


def compute_delta_time(reference_lap, compare_lap):
    """Align two laps on distance and compute time delta along the reference lap."""
    ref = reference_lap.get_car_data(interpolate_edges=True).add_distance()
    comp = compare_lap.get_car_data(interpolate_edges=True).add_distance()

    def pad_stream(stream):
        d_start = stream[1] - stream[0]
        d_end = stream[-1] - stream[-2]
        return np.concatenate([[stream[0] - d_start], stream, [stream[-1] + d_end]])

    comp_time = pad_stream(comp['Time'].dt.total_seconds().to_numpy())
    multiplier = ref.Distance.iat[-1] / comp.Distance.iat[-1]
    comp_distance = pad_stream(comp['Distance'].to_numpy()) * multiplier
    compare_time_at_ref_dist = np.interp(ref['Distance'], comp_distance, comp_time)

    delta = compare_time_at_ref_dist - ref['Time'].dt.total_seconds()
    return delta, ref, comp

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

driver1 = 'LEC'
driver2 = 'PIA'

lap1 = session.laps.pick_drivers(driver1).pick_fastest()
lap2 = session.laps.pick_drivers(driver2).pick_fastest()

delta_time, ref_tel, compare_tel = compute_delta_time(lap1, lap2)

fig, ax1 = plt.subplots(figsize=(12, 5))

# Delta line: positive = driver2 slower than driver1 at that point
ax1.plot(ref_tel['Distance'], delta_time, color='purple')
ax1.axhline(0, color='gray', linestyle='--', linewidth=1)
ax1.set_xlabel('Distance around lap (m)')
ax1.set_ylabel(f'<-- {driver2} ahead | {driver1} ahead -->  (seconds)')
ax1.set_title(f'{driver1} vs {driver2} — Monaco 2024 — Time delta')
ax1.grid(True)

plt.savefig('delta_time.png')
print("Saved chart as delta_time.png")
