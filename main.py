import time

from scai_backbone import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_game_start(self)

    def on_step(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_step(self)


if __name__ == "__main__":
    MyAgent.bootstrap()
