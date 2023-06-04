class GameConfiguration:
    def __init__(self, game):
        self.game = game


    def game_admin(self):
        value = [config.value for config in self.game.game_config if config.configuration.name == 'game_admin']
        if value is not None:
            value = value[0]
        return value == '1'

