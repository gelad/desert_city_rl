import game_view
import dataset
import messages

# HERE PROGRAM RUN STARTS
dataset.initialize()
loop = game_view.GameLoop()
loop.run()
