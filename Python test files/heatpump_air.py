from tespy.networks import Network
from tespy.components import Sink, Source, Compressor, Valve, HeatExchangerSimple
from tespy.connections import Connection
from tespy.tools import document_model

nw = Network(fluids=['water', 'air'], T_unit='C', p_unit='bar', h_unit='kJ / kg')

# Sources & Sinks
ambient_air = Source('ambient air')
heated_space = Sink('heated space')

# Heat Pump Components
compressor = Compressor('compressor')
valve = Valve('expansion valve')
evaporator = HeatExchangerSimple('evaporator')
condenser = HeatExchangerSimple('condenser')

# Evaporator Connections
c1 = Connection(ambient_air, 'out1', evaporator, 'in1')
c2 = Connection(evaporator, 'out1', valve, 'in1')

# Condenser Connections
c3 = Connection(valve, 'out1', condenser, 'in1')
c4 = Connection(condenser, 'out1', compressor, 'in1')
c5 = Connection(compressor, 'out1', evaporator, 'in1', label='cycle closer')

# Heating Space Connection
c6 = Connection(condenser, 'out1', heated_space, 'in1')

# Add connections to the network
nw.add_conns(c1, c2, c3, c4, c5, c6)

# Example parameter setting
compressor.set_attr(eta_s=0.85)
valve.set_attr(pr=0.95)
evaporator.set_attr(pr=0.98)
condenser.set_attr(pr=0.98)

nw.solve('design')
nw.save('heat_pump')
