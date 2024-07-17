import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_simulation(start_date, end_date, solar_capacity, wind_capacity, battery_capacity, battery_efficiency, demand_profile):
    time_steps = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Ensure the demand_profile matches the time_steps length
    if len(demand_profile) != len(time_steps):
        raise ValueError("Length of demand_profile must match the number of time steps between start_date and end_date.")
    
    # Simulate solar and wind power generation data (simplified model)
    solar_generation = solar_capacity * np.sin(np.linspace(0, np.pi, len(time_steps)))
    wind_generation = wind_capacity * np.sin(np.linspace(0, 2*np.pi, len(time_steps)))
    
    # Store in a DataFrame
    df = pd.DataFrame({'Solar_Generation': solar_generation, 'Wind_Generation': wind_generation, 'Demand': demand_profile}, index=time_steps)
    df['Total_Generation'] = df['Solar_Generation'] + df['Wind_Generation']

    # Initialize battery storage variables
    df['Battery_Storage'] = 0  # Initial battery storage
    df['Battery_Change'] = 0  # Change in battery storage (positive for charging, negative for discharging)

    battery_storage = 0  # Current battery storage

    for i in df.index:
        net_generation = df.at[i, 'Total_Generation'] - df.at[i, 'Demand']
        if net_generation > 0:
            # Excess generation, charge the battery
            charge = min(net_generation * battery_efficiency, battery_capacity - battery_storage)
            battery_storage += charge
            df.at[i, 'Battery_Change'] = charge
        else:
            # Demand exceeds generation, discharge the battery if possible
            discharge = max(net_generation, -battery_storage)
            battery_storage += discharge  # discharge is negative
            df.at[i, 'Battery_Change'] = discharge
            
        df.at[i, 'Battery_Storage'] = battery_storage

    # Plotting the results with battery storage
    plt.figure(figsize=(14, 8))

    plt.subplot(2, 1, 1)
    plt.plot(df.index, df['Solar_Generation'], label='Solar Generation')
    plt.plot(df.index, df['Wind_Generation'], label='Wind Generation')
    plt.plot(df.index, df['Demand'], label='Demand', linestyle='--')
    plt.ylabel('MW')
    plt.title('Generation vs. Demand')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(df.index, df['Battery_Storage'], color='purple', label='Battery Storage')
    plt.fill_between(df.index, 0, df['Battery_Storage'], color='purple', alpha=0.3)
    plt.ylabel('MWh')
    plt.title('Battery Storage Level Over Time')
    plt.legend()

    plt.tight_layout()
    plt.show()

# Calculate the number of hours between start_date and end_date
start_date = '2023-01-01'
end_date = '2023-01-14'
time_steps = pd.date_range(start=start_date, end=end_date, freq='H')
num_hours = len(time_steps)

# Generate an example variable hourly demand profile
hourly_demand = np.random.rand(num_hours) * 50 + 100  # Example: random demand fluctuating around 100-150 MW for the given period

# Example usage of the function with the variable hourly demand
run_simulation(start_date=start_date, end_date=end_date,
               solar_capacity=100, wind_capacity=150,
               battery_capacity=200, battery_efficiency=0.9,
               demand_profile=hourly_demand)
