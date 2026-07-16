import os

import fastf1
import matplotlib.pyplot as plt

# This creates a local cache folder so FastF1 doesn't re-download data every time
os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

# Load the same session
session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

# Get Leclerc's fastest lap
lap = session.laps.pick_drivers('LEC').pick_fastest()

# Get the telemetry (speed, throttle, brake, distance, etc.) for that lap
tel = lap.get_car_data().add_distance()

# Print the first few rows so we can SEE what the data looks like
print(tel[['Distance', 'Speed', 'Throttle', 'Brake']].head())

# Plot speed vs distance around the lap
plt.figure(figsize=(12, 5))
plt.plot(tel['Distance'], tel['Speed'])
plt.xlabel('Distance around lap (m)')
plt.ylabel('Speed (km/h)')
plt.title("Leclerc's fastest lap — Monaco 2024 — Speed trace")
plt.grid(True)
plt.savefig('speed_trace.png')
print("Saved chart as speed_trace.png")
