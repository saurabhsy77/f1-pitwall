import os

import fastf1
import matplotlib.pyplot as plt

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

lap = session.laps.pick_drivers('LEC').pick_fastest()
tel = lap.get_car_data().add_distance()

print(tel[['Distance', 'Speed', 'Throttle', 'Brake']].head())

plt.figure(figsize=(12, 5))
plt.plot(tel['Distance'], tel['Speed'])
plt.xlabel('Distance around lap (m)')
plt.ylabel('Speed (km/h)')
plt.title("Leclerc's fastest lap — Monaco 2024 — Speed trace")
plt.grid(True)
plt.savefig('speed_trace.png')
print("Saved chart as speed_trace.png")
