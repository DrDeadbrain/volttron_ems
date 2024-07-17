"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from threading import Timer

from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def neighborhood(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Neighborhood
    :rtype: Neighborhood
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

    return Neighborhood(setting1, setting2, setting3, **kwargs)


class Neighborhood(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, setting1, setting2, setting3, timeout=10, **kwargs):
        super(Neighborhood, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting3 = setting3

        self.default_config = {"setting1": setting1,
                               "setting2": setting2,
                               "setting3": setting3}

        #Dictionary that holds all Messages from the device buildings
        #each device sends their building data as a dictionary -> so this is a dictionary of dictionarys
        self.message_store = {}
        self.expected_messages = setting1  #adjust in config to number of buildings
        self.received_messages = 0  # counter for received messages
        self.timeout = timeout
        self.timer = Timer(self.timeout, self.on_timeout)  # Timer to wait for message delay

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
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting3 = setting3

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
        #get all building data dictionaries and merge them to get one dictionary that gets forwarded to the microgrid agent and the flex agent
        print("Neighborhood joined the battle")
        if topic not in self.message_store:
            self.message_store[topic] = message
            _log.info(f"Stored message from {topic}: {message}")

        #check if all expected messages have been received
        if self.received_messages >= self.expected_messages and self.timer.is_alive():
            self.timer.cancel()
            merged_building_data = self.handle_building_data()
            self.vip.pubsub.publish('pubsub', self.setting3, message=merged_building_data)
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

    def handle_building_data(self):
        merged_message = {}  # dictionary that holds the neighborhood energy consumption for time interval
        for topic, message in self.message_store.items():
            for key, value in message.items():
                if key in merged_message:
                    # handle duplicate keys as needed
                    # here we assume the latest messages value
                    _log.warning(f"Duplicate key {key} in {topic}")
                merged_message[key] = value
        # handle missing keys be setting them to None
        all_keys = set()
        for message in self.message_store.values():
            all_keys.update(message.keys())

        for key in all_keys:
            if key not in merged_message:
                merged_message[key] = None  # or set default value

        return merged_message

    def on_timeout(self):
        _log.info("Timeout reached. Proceeding with available messages.")
        self.handle_building_data()


def main():
    """Main method called to start the agent."""
    utils.vip_main(neighborhood,
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
