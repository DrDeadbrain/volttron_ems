from opcua import ua, Server

# Create a new OPC UA server instance
server = Server()

# Set the endpoint URL for the server
server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

# Set the server name
server.set_server_name("Energy Flexibility OPC UA Server")

# Register a namespace
uri = "http://example.org/energyflexibility"
idx = server.register_namespace(uri)

# Get the Objects node, which is the root of the address space
objects = server.get_objects_node()

# Create the root object "Energy Flexibility"
energy_flexibility = objects.add_object(idx, "EnergyFlexibility")

# Add variables to the "Energy Flexibility" object
flexibility = energy_flexibility.add_variable(idx, "Flexibility", 0.0)
generated_energy = energy_flexibility.add_variable(idx, "GeneratedEnergy", 0.0)
flexible_load = energy_flexibility.add_variable(idx, "FlexibleLoad", 0.0)

# Define the "calculateFlex" method
def calculate_flex_method(parent):
    # Implement the method logic here
    print("calculateFlex method called")
    return [ua.Variant(True, ua.VariantType.Boolean)]

# Add the "calculateFlex" method to the "Energy Flexibility" object
energy_flexibility.add_method(idx, "calculateFlex", calculate_flex_method, [], [ua.VariantType.Boolean])

# Create the "Building" object
building = energy_flexibility.add_object(idx, "Building")
building_id = building.add_variable(idx, "BuildingID", 0)
flexible_load_building = building.add_variable(idx, "FlexibleLoad", 0.0)
datetime_building = building.add_variable(idx, "DateTime", "")
# Add other properties as needed...

# Create the "District" object
district = energy_flexibility.add_object(idx, "District")
buildings = district.add_variable(idx, "Buildings", "")
load_id = district.add_variable(idx, "LoadID", 0)
loads = district.add_variable(idx, "Loads", 0.0)
total_load = district.add_variable(idx, "TotalLoad", 0.0)
# Add other properties as needed...

# Create the "Microgrid" object
microgrid = energy_flexibility.add_object(idx, "Microgrid")

# Add "Solar Generator" to "Microgrid"
solar_generator = microgrid.add_object(idx, "SolarGenerator")
current_gen_solar = solar_generator.add_variable(idx, "CurrentGen", 0.0)
efficiency_coeff_solar = solar_generator.add_variable(idx, "EfficiencyCoeff", 0.0)
time_solar = solar_generator.add_variable(idx, "Time", "")
# Add other properties as needed...

# Add "Wind Generator" to "Microgrid"
wind_generator = microgrid.add_object(idx, "WindGenerator")
current_gen_wind = wind_generator.add_variable(idx, "CurrentGen", 0.0)
efficiency_coeff_wind = wind_generator.add_variable(idx, "EfficiencyCoeff", 0.0)
time_wind = wind_generator.add_variable(idx, "Time", "")
# Add other properties as needed...

# Add "Battery Storage" to "Microgrid"
battery_storage = microgrid.add_object(idx, "BatteryStorage")
storage_id = battery_storage.add_variable(idx, "StorageID", 0)
capacity = battery_storage.add_variable(idx, "Capacity", 0.0)
initial_energy = battery_storage.add_variable(idx, "InitialEnergy", 0.0)
target_energy = battery_storage.add_variable(idx, "TargetEnergy", 0.0)
holding_duration = battery_storage.add_variable(idx, "HoldingDuration", 0.0)
energy_loss = battery_storage.add_variable(idx, "EnergyLoss", 0.0)
# Add other properties as needed...

# Set variables to be writable by clients
for var in [flexibility, generated_energy, flexible_load, building_id, flexible_load_building, datetime_building,
            buildings, load_id, loads, total_load, current_gen_solar, efficiency_coeff_solar, time_solar,
            current_gen_wind, efficiency_coeff_wind, time_wind, storage_id, capacity, initial_energy,
            target_energy, holding_duration, energy_loss]:
    var.set_writable()

# Start the server
server.start()
print("OPC UA Server is running at opc.tcp://0.0.0.0:4840/freeopcua/server/")

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Server stopped by user")
finally:
    # Stop the server
    server.stop()
