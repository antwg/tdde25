import time

from scai_backbone import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def awake(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        pass

    def update(self):
        """Called each cycle, passed from IDABot.on_step()."""
        pass


if __name__ == "__main__":
    MyAgent.bootstrap()
