"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def building(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Building
    :rtype: Building
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

    return Building(setting1, setting2, setting3, **kwargs)


class Building(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, setting1, setting2, setting3, **kwargs):
        super(Building, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting3 = setting3

        self.default_config = {"setting1": setting1,
                               "setting2": setting2,
                               "setting3": setting3}

        self.message_processed = False

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
            settings3 = str(config["setting3"])
            # base_topic_pub = "neighborhood/energyconsumption/building{]"
            # base_topic_sub = "devices/buildings/building{}"
            # self.topic_pub = base_topic_pub.format(setting1)
            # topic_sub = base_topic_sub.format(setting1)
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

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
        building_dict = {}
        if not self.message_processed:
            self.message_processed = True
            # print(
            #     # "Peer: {0}, Sender: {1}:, Bus: {2}, Topic: {3}, Headers: {4}, "
            #     "Message: \n{5}".format(peer, sender, bus, topic, headers, pformat(message))
            # )
            building_data = message
            building_dict = building_data
            print(building_dict)
            #do method??!
        #df = pd.DataFrame(data=d)
        #print(message)
        data = [1, 2, 3, 4]
        #print(message)
        #handle incoming messages
        #filter content
        #use calculation methods
        #forward messages to other topic
        self.vip.pubsub.publish('pubsub', self.setting3, message=building_dict)
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
        #define topics in eplus agents
        #subscribe to that topics
        #fi
        self.vip.pubsub.publish('pubsub', "devices/PNNL/BUILDING1/METERS/all", message="HI!")
        print("hello fucker")

        # Example RPC call
        # self.vip.rpc.call("some_agent", "some_method", arg1, arg2)
        pass

    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        This method is called when the Agent is about to shutdown, but before it disconnects from
        the message bus.
        """
        print("fuck you")
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
    utils.vip_main(building,
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
