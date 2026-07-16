import os

import fastf1
import matplotlib.pyplot as plt

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

# Pick two drivers to compare
driver1 = 'LEC'
driver2 = 'PIA'

lap1 = session.laps.pick_drivers(driver1).pick_fastest()
lap2 = session.laps.pick_drivers(driver2).pick_fastest()

tel1 = lap1.get_car_data().add_distance()
tel2 = lap2.get_car_data().add_distance()

plt.figure(figsize=(12, 5))
plt.plot(tel1['Distance'], tel1['Speed'], label=f'{driver1} ({lap1["LapTime"]})', color='red')
plt.plot(tel2['Distance'], tel2['Speed'], label=f'{driver2} ({lap2["LapTime"]})', color='orange')
plt.xlabel('Distance around lap (m)')
plt.ylabel('Speed (km/h)')
plt.title(f'{driver1} vs {driver2} — Monaco 2024 — Speed comparison')
plt.legend()
plt.grid(True)
plt.savefig('speed_comparison.png')
print("Saved chart as speed_comparison.png")
print(f"{driver1} lap time: {lap1['LapTime']}")
print(f"{driver2} lap time: {lap2['LapTime']}")