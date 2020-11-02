from scai_bootstrap import *


class MyAgent(ScaiBootstrap):

    def awake(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        pass

    def update(self):
        """Called each cycle, passed from IDABot.on_step()."""
        pass


if __name__ == "__main__":
    MyAgent.main()
