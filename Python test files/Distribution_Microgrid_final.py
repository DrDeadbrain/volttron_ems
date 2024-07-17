import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Funktion zur Simulation der Solargeneration mit einem tageszeitlichen Muster
def simulate_solar_generation(time_steps, solar_capacity):
    solar_generation = []
    for time in time_steps:
        hour = time.hour
        if 6 <= hour <= 18:  # Annahme, dass die Solargeneration nur von 6 Uhr bis 18 Uhr erfolgt
            solar_gen = solar_capacity * np.sin((hour - 6) * np.pi / 12)
        else:
            solar_gen = 0
        solar_generation.append(solar_gen)
    return np.array(solar_generation)

# Funktion zur Simulation der Windgeneration mit Zufälligkeit
def simulate_wind_generation(time_steps, wind_capacity):
    np.random.seed(0)
    wind_generation = wind_capacity * np.abs(np.random.uniform(0, 1, len(time_steps)))
    return wind_generation

# Funktion zur Simulation der Erzeugung mit Rampe
def apply_ramp(generation, ramp_rate):
    ramped_generation = np.copy(generation)
    for i in range(1, len(generation)):
        ramped_generation[i] = max(min(ramped_generation[i-1] + ramp_rate, generation[i]), ramped_generation[i-1] - ramp_rate)
    return ramped_generation

# Funktion zur Simulation
def run_simulation(num_time_points, time_resolution, solar_capacity, wind_capacity, chp_capacity, battery_capacity, battery_efficiency, thermal_storage_capacity, thermal_storage_efficiency, demand_series, thermal_demand_profile, battery_mode='default', use_solar=True, use_wind=True, use_chp=True, ramp_rate=0.5):
    if time_resolution == 'hourly':
        freq = 'H'
    elif time_resolution == '15-min':
        freq = '15min'
    else:
        raise ValueError("Invalid time_resolution. Choose 'hourly' or '15-min'.")

    time_steps = pd.date_range(start=pd.Timestamp.now().normalize(), periods=num_time_points, freq=freq)

    # Initialisierung der Erzeugungsdaten
    if use_solar:
        solar_generation = simulate_solar_generation(time_steps, solar_capacity)
    else:
        solar_generation = np.zeros(len(time_steps))

    if use_wind:
        wind_generation = simulate_wind_generation(time_steps, wind_capacity)
        wind_generation = apply_ramp(wind_generation, ramp_rate)
    else:
        wind_generation = np.zeros(len(time_steps))

    if use_chp:
        chp_generation = np.full(len(time_steps), chp_capacity)
        chp_generation = apply_ramp(chp_generation, ramp_rate)
    else:
        chp_generation = np.zeros(len(time_steps))

    if len(demand_series) != len(time_steps) or len(thermal_demand_profile) != len(time_steps):
        raise ValueError("Length of demand_series and thermal_demand_profile must match the number of time steps.")

    df = pd.DataFrame({
        'Solar_Generation': solar_generation,
        'Wind_Generation': wind_generation,
        'CHP_Generation': chp_generation,
        'Demand': demand_series,
        'Thermal_Demand': thermal_demand_profile
    }, index=time_steps)
    df['Total_Generation'] = df['Solar_Generation'] + df['Wind_Generation'] + df['CHP_Generation']

    df['Battery_Storage'] = 0
    df['Battery_Change'] = 0
    df['Thermal_Storage'] = 0
    df['Thermal_Change'] = 0
    df['Surplus_Deficit'] = df['Total_Generation'] - df['Demand']
    df['Grid_Export'] = 0

    battery_storage = 0
    thermal_storage = 0

    for j, i in enumerate(df.index):
        net_generation = df.at[i, 'Total_Generation']
        net_thermal_generation = df.at[i, 'CHP_Generation'] - df.at[i, 'Thermal_Demand']
        net_demand = df.at[i, 'Demand']

        # Update battery capacity
        if battery_mode == 'default':
            if net_generation > net_demand and battery_storage < battery_capacity:
                excess_energy = net_generation - net_demand
                charge = min(excess_energy * battery_efficiency, battery_capacity - battery_storage)
                battery_storage += charge
                df.at[i, 'Battery_Change'] = charge
                df.at[i, 'Grid_Export'] = excess_energy - charge
            elif net_generation < net_demand and battery_storage > 0:
                energy_deficit = net_demand - net_generation
                discharge = min(energy_deficit, battery_storage)
                battery_storage -= discharge
                df.at[i, 'Battery_Change'] = -discharge
                df.at[i, 'Grid_Export'] = 0
        elif battery_mode == 'peak_shaving':
            if net_generation > net_demand and battery_storage < battery_capacity:
                charge = min((net_generation - net_demand) * battery_efficiency, battery_capacity - battery_storage)
                battery_storage += charge
                df.at[i, 'Battery_Change'] = charge
                df.at[i, 'Grid_Export'] = net_generation - net_demand - charge
            elif net_demand > np.percentile(demand_series, 80) and battery_storage > 0:
                discharge = min(net_demand - net_generation, battery_storage)
                battery_storage -= discharge
                df.at[i, 'Battery_Change'] = -discharge
                df.at[i, 'Grid_Export'] = 0
            else:
                df.at[i, 'Grid_Export'] = net_generation - net_demand

        df.at[i, 'Battery_Storage'] = battery_storage

        # Update thermal storage
        if net_thermal_generation > 0:
            thermal_charge = min(net_thermal_generation * thermal_storage_efficiency, thermal_storage_capacity - thermal_storage)
            thermal_storage += thermal_charge
            df.at[i, 'Thermal_Change'] = thermal_charge
        else:
            thermal_discharge = min(-net_thermal_generation, thermal_storage)
            thermal_storage -= thermal_discharge
            df.at[i, 'Thermal_Change'] = -thermal_discharge

        df.at[i, 'Thermal_Storage'] = thermal_storage

    plt.figure(figsize=(14, 15))

    plt.subplot(5, 1, 1)
    if use_solar:
        plt.plot(df.index, df['Solar_Generation'], label='Solar Generation')
    if use_wind:
        plt.plot(df.index, df['Wind_Generation'], label='Wind Generation')
    if use_chp:
        plt.plot(df.index, df['CHP_Generation'], label='CHP Generation')
    plt.plot(df.index, df['Demand'], label='Electrical Demand', linestyle='--')
    plt.ylabel('kW')
    plt.title('Electrical Generation vs. Demand')
    plt.legend()

    plt.subplot(5, 1, 2)
    plt.plot(df.index, df['Battery_Storage'], color='purple', label='Battery Storage')
    plt.fill_between(df.index, 0, df['Battery_Storage'], color='purple', alpha=0.3)
    plt.ylabel('kWh')
    plt.title('Battery Storage Level Over Time')
    plt.legend()

    plt.subplot(5, 1, 3)
    plt.plot(df.index, df['Thermal_Storage'], color='orange', label='Thermal Storage')
    plt.fill_between(df.index, 0, df['Thermal_Storage'], color='orange', alpha=0.3)
    plt.plot(df.index, df['Thermal_Demand'], label='Thermal Demand', linestyle='--')
    plt.ylabel('kWh')
    plt.title('Thermal Storage Level Over Time')
    plt.legend()

    plt.subplot(5, 1, 4)
    plt.plot(df.index, df['Surplus_Deficit'], color='blue', label='Surplus/Deficit')
    plt.axhline(0, color='red', linestyle='--', label='Equilibrium')
    plt.fill_between(df.index, 0, df['Surplus_Deficit'], where=(df['Surplus_Deficit'] >= 0), interpolate=True, color='green', alpha=0.3, label='Surplus')
    plt.fill_between(df.index, 0, df['Surplus_Deficit'], where=(df['Surplus_Deficit'] < 0), interpolate=True, color='red', alpha=0.3, label='Deficit')
    plt.ylabel('kW')
    plt.title('Energy Surplus/Deficit Over Time')
    plt.legend()

    plt.subplot(5, 1, 5)
    plt.plot(df.index, df['Grid_Export'], color='cyan', label='Grid Export')
    plt.fill_between(df.index, 0, df['Grid_Export'], color='cyan', alpha=0.3)
    plt.ylabel('kW')
    plt.title('Grid Export Over Time')
    plt.legend()

    plt.tight_layout()
    plt.show()

    return df

def calculate_self_sufficiency_and_self_consumption(df):
    daily_data = df.resample('D').sum()

    daily_data['Generation_Directly_Consumed'] = daily_data.apply(
        lambda row: min(row['Total_Generation'], row['Demand']), axis=1)

    daily_data['Self_Sufficiency'] = daily_data['Generation_Directly_Consumed'] / daily_data['Demand']
    daily_data['Self_Consumption'] = daily_data['Generation_Directly_Consumed'] / daily_data['Total_Generation']

    return daily_data[['Self_Sufficiency', 'Self_Consumption']]

# Beispielhafte Nutzung
num_time_points = 24 * 7  # Eine Woche an stündlichen Daten
np.random.seed(42)
demand_series = np.random.randint(3000, 10001, size=num_time_points)
thermal_demand = np.random.randint(2000, 4000, size=num_time_points)

# Angepasste Systemkapazitäten
solar_capacity = 2000  # kW
wind_capacity = 0  # kW, da keine Angabe gemacht
chp_capacity = 1600  # kW elektrisch
battery_capacity = 30  # kWh
thermal_storage_capacity = 105  # kWh

# Simulation ausführen
df = run_simulation(num_time_points=num_time_points,
                    time_resolution='hourly',
                    solar_capacity=solar_capacity, wind_capacity=wind_capacity, chp_capacity=chp_capacity,
                    battery_capacity=battery_capacity, battery_efficiency=0.9,
                    thermal_storage_capacity=thermal_storage_capacity, thermal_storage_efficiency=0.85,
                    demand_series=demand_series, thermal_demand_profile=thermal_demand,
                    battery_mode='peak_shaving',  # 'default' oder 'peak_shaving'
                    use_solar=True, use_wind=False, use_chp=True,
                    ramp_rate=0.1)  # Anpassung der Ramprate nach Bedarf

# Berechnung der Kenngrößen
daily_kenngroessen = calculate_self_sufficiency_and_self_consumption(df)
print(daily_kenngroessen)
