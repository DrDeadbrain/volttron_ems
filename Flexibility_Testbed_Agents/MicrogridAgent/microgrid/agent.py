"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def microgrid(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Microgrid
    :rtype: Microgrid
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    setting1 = int(config.get('setting1'))
    setting2 = config.get('setting2')
    setting3 = config.get('setting3')
    setting4 = config.get('setting4')
    setting5 = int(config.get('setting5'))
    setting6 = int(config.get('setting6'))
    setting7 = int(config.get('setting7'))
    setting8 = int(config.get('setting8'))
    setting9 = float(config.get('setting9'))
    setting10 = int(config.get('setting10'))
    setting11 = float(config.get('setting11'))
    setting12 = bool(config.get('setting12'))
    setting13 = bool(config.get('setting13'))
    setting14 = bool(config.get('setting14'))

    return Microgrid(setting1, setting2, setting3, setting4, setting5, setting6, setting7, setting8, setting9,
                     setting10, setting11, setting12, setting13, setting14, **kwargs)


def simulate_wind_generation(time_steps, wind_capacity):
    np.random.seed(0)
    wind_generation = wind_capacity * np.abs(np.random.randn(len(time_steps)))
    return wind_generation


def simulate_solar_generation(time_steps, solar_capacity):
    solar_generation = []
    for time in time_steps:
        hour = time.hour
        if 6 <= hour <= 18:  # Annahme, dass Solarstromerzeugung nur von 6 Uhr bis 18 Uhr erfolgt
            solar_gen = solar_capacity * np.sin((hour - 6) * np.pi / 12)
        else:
            solar_gen = 0
        solar_generation.append(solar_gen)
    return np.array(solar_generation)


def run_simulation(num_time_points, time_resolution, solar_capacity, wind_capacity, chp_capacity, battery_capacity,
                   battery_efficiency, demand_series, use_solar=True, use_wind=True, use_chp=True):
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
    else:
        wind_generation = np.zeros(len(time_steps))

    if use_chp:
        chp_generation = np.full(len(time_steps), chp_capacity)
    else:
        chp_generation = np.zeros(len(time_steps))

    if len(demand_series) != len(time_steps):
        raise ValueError("Length of demand_series must match the number of time steps.")

    df = pd.DataFrame({
        'Solar_Generation': solar_generation,
        'Wind_Generation': wind_generation,
        'CHP_Generation': chp_generation,
        'Demand': demand_series
    }, index=time_steps)
    df['Total_Generation'] = df['Solar_Generation'] + df['Wind_Generation'] + df['CHP_Generation']

    df['Battery_Storage'] = 0
    df['Battery_Change'] = 0

    battery_storage = 0
    thermal_storage = 0
    generation_off = False

    for j, i in enumerate(df.index):
        net_generation = df.at[i, 'Total_Generation']
        net_demand = df.at[i, 'Demand']

        if generation_off:
            net_generation = 0

        # Aktualisierung der Batteriekapazität
        if net_generation > net_demand:
            excess_energy = net_generation - net_demand
            charge = min(excess_energy * battery_efficiency, battery_capacity - battery_storage)
            battery_storage += charge
            df.at[i, 'Battery_Change'] = charge
        else:
            energy_deficit = net_demand - net_generation
            discharge = min(energy_deficit, battery_storage)
            battery_storage -= discharge
            df.at[i, 'Battery_Change'] = -discharge

        df.at[i, 'Battery_Storage'] = battery_storage

        # Steuerung der Erzeugung basierend auf dem Batteriekapazitätsniveau
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
    return df

    # plt.figure(figsize=(14, 10))
    #
    # plt.subplot(3, 1, 1)
    # if use_solar:
    #     plt.plot(df.index, df['Solar_Generation'], label='Solar Generation')
    # if use_wind:
    #     plt.plot(df.index, df['Wind_Generation'], label='Wind Generation')
    # if use_chp:
    #     plt.plot(df.index, df['CHP_Generation'], label='CHP Generation')
    # plt.plot(df.index, df['Demand'], label='Electrical Demand', linestyle='--')
    # plt.ylabel('MW')
    # plt.title('Electrical Generation vs. Demand')
    # plt.legend()
    #
    # plt.subplot(3, 1, 2)
    # plt.plot(df.index, df['Battery_Storage'], color='purple', label='Battery Storage')
    # plt.fill_between(df.index, 0, df['Battery_Storage'], color='purple', alpha=0.3)
    # plt.ylabel('MWh')
    # plt.title('Battery Storage Level Over Time')
    # plt.legend()
    #
    # plt.tight_layout()
    # plt.show()


class Microgrid(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, setting1=1, setting2="neighborhood/totalEnergy", setting3="microgrid/data", setting4='hourly',
                 setting5=3000, setting6=3000, setting7=3000, setting8=10000, setting9=0.9, setting10=5000,
                 setting11=0.85, setting12="true", setting13="true", setting14="true", **kwargs):
        super(Microgrid, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting3 = setting3
        self.setting4 = setting4
        self.setting5 = setting5
        self.setting6 = setting6
        self.setting7 = setting7
        self.setting8 = setting8
        self.setting9 = setting9
        self.setting10 = setting10
        self.setting11 = setting11
        self.setting12 = setting12
        self.setting13 = setting13
        self.setting14 = setting14

        self.default_config = {"setting1": setting1,
                               "setting2": setting2,
                               "setting3": setting3,
                               "setting4": setting4,
                               "setting5": setting5,
                               "setting6": setting6,
                               "setting7": setting7,
                               "setting8": setting8,
                               "setting9": setting9,
                               "setting10": setting10,
                               "setting11": setting11,
                               "setting12": setting12,
                               "setting13": setting13,
                               "setting14": setting14}

        self.message_received = 0
        self.num_time_points = 0
        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        self.vip.config.set_default("config", self.default_config)
        # Hook self.configure up to changes to the configuration file "config".
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

    def configure(self, config_name, action, contents):
        """
        Called after the Agent has connected to the message bus. If a configuration exists at startup
        this will be called before onstart.

        Is called every time the configuration in the store changes.
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.debug("Configuring Agent")

        try:
            setting1 = int(config["setting1"])
            setting2 = str(config["setting2"])
            setting3 = str(config["setting3"])
            setting4 = str(config["setting4"])
            setting5 = int(config["setting5"])
            setting6 = int(config["setting6"])
            setting7 = int(config["setting7"])
            setting8 = int(config["setting8"])
            setting9 = float(config["setting9"])
            setting10 = int(config["setting10"])
            setting11 = float(config["setting11"])
            setting12 = bool(config["setting12"])
            setting13 = bool(config["setting13"])
            setting14 = bool(config["setting14"])
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting3 = setting3
        self.setting4 = setting4
        self.setting5 = setting5
        self.setting6 = setting6
        self.setting7 = setting7
        self.setting8 = setting8
        self.setting9 = setting9
        self.setting10 = setting10
        self.setting11 = setting11
        self.setting12 = setting12
        self.setting13 = setting13
        self.setting14 = setting14

        self._create_subscriptions(self.setting2)

    def _create_subscriptions(self, topic):
        """
        Unsubscribe from all pub/sub topics and create a subscription to a topic in the configuration which triggers
        the _handle_publish callback
        """
        self.vip.pubsub.unsubscribe("pubsub", None, None)

        self.vip.pubsub.subscribe(peer='pubsub',
                                  prefix=topic,
                                  callback=self._handle_publish)

    def _handle_publish(self, peer, sender, bus, topic, headers, message):
        """
        Callback triggered by the subscription setup using the topic from the agent's config file
        """
        if self.setting4 == 'hourly':
            self.num_time_points = 24 * 7
        elif self.setting4 == '15-min':
            self.num_time_points = 96 * 7

        if self.message_received == 0:
            message_received = 1
            data_dict = message
            data = run_simulation(self.num_time_points, 'hourly', self.setting5, self.setting6, self.setting7,
                           self.setting8, self.setting9, data_dict, True, True, True)

            #maybe need to transform the df to message it
            #dict_of_dfs = {col: df[[col]] for col in df.columns}

            #if multi index
            #dict_of_dicts = df.groupby(level=0).apply(lambda x: x.droplevel(0).to_dict()).to_dict()

            #convert whole df
            #dict_from_df = df.to_dict()

            self.vip.pubsub.publish('pubsub', self.setting3, message=data)

        pass

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        This is method is called once the Agent has successfully connected to the platform.
        This is a good place to setup subscriptions if they are not dynamic or
        do any other startup activities that require a connection to the message bus.
        Called after any configurations methods that are called at startup.

        Usually not needed if using the configuration store.
        """
        # Example publish to pubsub
        self.vip.pubsub.publish('pubsub', "some/random/topic", message="HI!")

        # Example RPC call
        # self.vip.rpc.call("some_agent", "some_method", arg1, arg2)
        pass

    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        This method is called when the Agent is about to shutdown, but before it disconnects from
        the message bus.
        """
        pass

    @RPC.export
    def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        return self.setting1 + arg1 - arg2


def main():
    """Main method called to start the agent."""
    utils.vip_main(microgrid,
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
