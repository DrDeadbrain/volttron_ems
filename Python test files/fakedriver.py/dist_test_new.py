import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Function to calculate realistic capacities based on demand
def calculate_realistic_capacities(demand_series):
    average_demand = demand_series.mean()
    battery_capacity = average_demand * 15  # kWh, enough for several hours up to a day
    solar_capacity = average_demand * 0.5  # kW, typical for supplementary solar energy
    wind_capacity = average_demand * 2  # kW, typical for small wind turbines
    chp_capacity = average_demand * 0.5  # kW, small CHP

    return solar_capacity, wind_capacity, chp_capacity, battery_capacity

# Function to simulate solar generation with a diurnal pattern
def simulate_solar_generation(time_steps, solar_capacity):
    solar_generation = []
    for time in time_steps:
        hour = time.hour
        if 6 <= hour <= 18:  # Assume solar generation only occurs from 6 AM to 6 PM
            solar_gen = solar_capacity * np.sin((hour - 6) * np.pi / 12)
        else:
            solar_gen = 0
        solar_generation.append(solar_gen)
    return np.array(solar_generation)

# Function to simulate wind generation with randomness
def simulate_wind_generation(time_steps, wind_capacity):
    np.random.seed(0)
    wind_generation = wind_capacity * np.abs(np.random.uniform(0, 1, len(time_steps)))
    return wind_generation

# Function to simulate ramped generation
def apply_ramp(generation, ramp_rate):
    ramped_generation = np.copy(generation)
    for i in range(1, len(generation)):
        ramped_generation[i] = max(min(ramped_generation[i-1] + ramp_rate, generation[i]), ramped_generation[i-1] - ramp_rate)
    return ramped_generation

# Function to run the simulation
def run_simulation(num_time_points, time_resolution, solar_capacity, wind_capacity, chp_capacity, battery_capacity, battery_efficiency, thermal_storage_capacity, thermal_storage_efficiency, demand_series, thermal_demand_profile, use_solar=True, use_wind=True, use_chp=True, ramp_rate=0.5):
    if time_resolution == 'hourly':
        freq = 'H'
    elif time_resolution == '15-min':
        freq = '15min'
    else:
        raise ValueError("Invalid time_resolution. Choose 'hourly' or '15-min'.")

    time_steps = pd.date_range(start=pd.Timestamp.now().normalize(), periods=num_time_points, freq=freq)

    # Initialize generation data
    if use_solar:
        solar_generation = simulate_solar_generation(time_steps, solar_capacity)
        #solar_generation = apply_ramp(solar_generation, ramp_rate)
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

    battery_storage = 0
    thermal_storage = 0
    generation_off = False

    for j, i in enumerate(df.index):
        net_generation = df.at[i, 'Total_Generation']
        net_thermal_generation = df.at[i, 'CHP_Generation'] - df.at[i, 'Thermal_Demand']
        net_demand = df.at[i, 'Demand']

        if generation_off:
            net_generation = 0

        # Update battery capacity
        if net_generation > net_demand and battery_storage < battery_capacity:
            excess_energy = net_generation - net_demand
            charge = min(excess_energy * battery_efficiency, battery_capacity - battery_storage)
            battery_storage += charge
            df.at[i, 'Battery_Change'] = charge
        elif net_generation < net_demand and battery_storage > 0:
            energy_deficit = net_demand - net_generation
            discharge = min(energy_deficit, battery_storage)
            battery_storage -= discharge
            df.at[i, 'Battery_Change'] = -discharge

        df.at[i, 'Battery_Storage'] = battery_storage

        # Control generation based on battery capacity level
        if battery_storage >= battery_capacity:
            generation_off = True
        elif battery_storage <= 0:
            generation_off = False

        if generation_off:
            df.at[i, 'Solar_Generation'] = 0
            df.at[i, 'Wind_Generation'] = 0
            df.at[i, 'CHP_Generation'] = 0
        else:
            if use_solar:
                df.at[i, 'Solar_Generation'] = solar_generation[j]
            if use_wind:
                df.at[i, 'Wind_Generation'] = wind_generation[j]
            if use_chp:
                df.at[i, 'CHP_Generation'] = chp_capacity

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

    plt.figure(figsize=(14, 10))

    plt.subplot(3, 1, 1)
    if use_solar:
        plt.plot(df.index, df['Solar_Generation'], label='Solar Generation')
    if use_wind:
        plt.plot(df.index, df['Wind_Generation'], label='Wind Generation')
    if use_chp:
        plt.plot(df.index, df['CHP_Generation'], label='CHP Generation')
    plt.plot(df.index, df['Demand'], label='Electrical Demand', linestyle='--')
    plt.ylabel('MW')
    plt.title('Electrical Generation vs. Demand')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(df.index, df['Battery_Storage'], color='purple', label='Battery Storage')
    plt.fill_between(df.index, 0, df['Battery_Storage'], color='purple', alpha=0.3)
    plt.ylabel('MWh')
    plt.title('Battery Storage Level Over Time')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(df.index, df['Thermal_Storage'], color='orange', label='Thermal Storage')
    plt.fill_between(df.index, 0, df['Thermal_Storage'], color='orange', alpha=0.3)
    plt.plot(df.index, df['Thermal_Demand'], label='Thermal Demand', linestyle='--')
    plt.ylabel('MWh')
    plt.title('Thermal Storage Level Over Time')
    plt.legend()

    plt.tight_layout()
    plt.show()

# Creating a sample demand_dict with hourly values between 3000 and 10000 kW
num_time_points = 24 * 7  # One week of hourly values
np.random.seed(42)
demand_series = np.random.randint(3000, 10001, size=num_time_points)

thermal_demand = np.random.randint(2000, 4000, size=num_time_points)

# Calculate realistic capacities based on demand_series
solar_capacity, wind_capacity, chp_capacity, battery_capacity = calculate_realistic_capacities(demand_series)

# Run the simulation
run_simulation(num_time_points=num_time_points,
               time_resolution='hourly',
               solar_capacity=solar_capacity, wind_capacity=wind_capacity, chp_capacity=chp_capacity,
               battery_capacity=battery_capacity, battery_efficiency=0.9,
               thermal_storage_capacity=10000, thermal_storage_efficiency=0.85,
               demand_series=demand_series, thermal_demand_profile=thermal_demand,
               use_solar=True, use_wind=True, use_chp=True,
               ramp_rate=0.1)  # Adjust ramp rate as needed
