import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_simulation(start_date, end_date, solar_capacity, wind_capacity, chp_capacity, battery_capacity, battery_efficiency, thermal_storage_capacity, thermal_storage_efficiency, demand_profile, thermal_demand_profile, use_solar=True, use_wind=True, use_chp=True):
    time_steps = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Ensure the demand profiles match the time_steps length
    if len(demand_profile) != len(time_steps) or len(thermal_demand_profile) != len(time_steps):
        raise ValueError("Length of demand_profile and thermal_demand_profile must match the number of time steps between start_date and end_date.")
    
    # Initialize generation data
    solar_generation = np.zeros(len(time_steps))
    wind_generation = np.zeros(len(time_steps))
    chp_generation = np.zeros(len(time_steps))
    
    # Simulate solar power generation if enabled
    if use_solar:
        solar_generation = solar_capacity * np.sin(np.linspace(0, np.pi, len(time_steps)))
    
    # Simulate wind power generation if enabled
    if use_wind:
        wind_generation = wind_capacity * np.sin(np.linspace(0, 2 * np.pi, len(time_steps)))
    
    # Simulate CHP generation if enabled (constant output for simplicity)
    if use_chp:
        chp_generation = np.full(len(time_steps), chp_capacity)
    
    # Store in a DataFrame
    df = pd.DataFrame({
        'Solar_Generation': solar_generation,
        'Wind_Generation': wind_generation,
        'CHP_Generation': chp_generation,
        'Demand': demand_profile,
        'Thermal_Demand': thermal_demand_profile
    }, index=time_steps)
    df['Total_Generation'] = df['Solar_Generation'] + df['Wind_Generation'] + df['CHP_Generation']

    # Initialize storage variables
    df['Battery_Storage'] = 0  # Initial battery storage
    df['Battery_Change'] = 0  # Change in battery storage (positive for charging, negative for discharging)
    df['Thermal_Storage'] = 0  # Initial thermal storage
    df['Thermal_Change'] = 0  # Change in thermal storage (positive for charging, negative for discharging)

    battery_storage = 0  # Current battery storage
    thermal_storage = 0  # Current thermal storage

    for i in df.index:
        net_generation = df.at[i, 'Total_Generation'] - df.at[i, 'Demand']
        net_thermal_generation = df.at[i, 'CHP_Generation'] - df.at[i, 'Thermal_Demand']
        
        if net_generation > 0:
            # Excess electrical generation, charge the battery
            charge = min(net_generation * battery_efficiency, battery_capacity - battery_storage)
            battery_storage += charge
            df.at[i, 'Battery_Change'] = charge
        else:
            # Electrical demand exceeds generation, discharge the battery if possible
            discharge = max(net_generation, -battery_storage)
            battery_storage += discharge  # discharge is negative
            df.at[i, 'Battery_Change'] = discharge
            
        df.at[i, 'Battery_Storage'] = battery_storage
        
        if net_thermal_generation > 0:
            # Excess thermal generation, charge the thermal storage
            thermal_charge = min(net_thermal_generation * thermal_storage_efficiency, thermal_storage_capacity - thermal_storage)
            thermal_storage += thermal_charge
            df.at[i, 'Thermal_Change'] = thermal_charge
        else:
            # Thermal demand exceeds generation, discharge the thermal storage if possible
            thermal_discharge = max(net_thermal_generation, -thermal_storage)
            thermal_storage += thermal_discharge  # discharge is negative
            df.at[i, 'Thermal_Change'] = thermal_discharge
            
        df.at[i, 'Thermal_Storage'] = thermal_storage

    # Plotting the results with battery and thermal storage
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

# Calculate the number of hours between start_date and end_date
start_date = '2023-01-01'
end_date = '2023-01-02'
time_steps = pd.date_range(start=start_date, end=end_date, freq='15min')
num_hours = len(time_steps)

# Generate an example variable hourly demand profile
hourly_demand = np.random.rand(num_hours) * 50 + 100  # Example: random electrical demand fluctuating around 100-150 MW
thermal_demand = np.random.rand(num_hours) * 30 + 50  # Example: random thermal demand fluctuating around 50-80 MW

# Example usage of the function with the variable hourly demand
run_simulation(start_date=start_date, end_date=end_date,
               solar_capacity=100, wind_capacity=150, chp_capacity=50,
               battery_capacity=200, battery_efficiency=0.9,
               thermal_storage_capacity=100, thermal_storage_efficiency=0.85,
               demand_profile=hourly_demand, thermal_demand_profile=thermal_demand,
               use_solar=True, use_wind=True, use_chp=True)
