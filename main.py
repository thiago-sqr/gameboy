from PicoGameBoy import PicoGameBoy
import time
import gc
import Tetris
import GameOfLife
import FlapBird

menu_itens = ["Tetris", "GameOfLife", "FlapBird", "Exit"]

def display_menu(pgb, items):
    selected = 0
    while True:
        pgb.fill(PicoGameBoy.color(0, 0, 0))
        for i, item in enumerate(items):
            color = PicoGameBoy.color(255, 255, 255) if i == selected else PicoGameBoy.color(100, 100, 100)
            pgb.text("-> " + item if i == selected else "   " + item, 10, 10 + i * 10, color)
        pgb.show()

        if pgb.button_up():
            selected = (selected - 1) % len(items)
            time.sleep(0.2)  # Debounce
        elif pgb.button_down():
            selected = (selected + 1) % len(items)
            time.sleep(0.2)  # Debounce
        elif pgb.button_A():
            time.sleep(0.2)  # Debounce
            return items[selected]
def main():
    """
        Do not ever do it again. It's a one time event.
        a thing that only happens once in a million years,
        when the sun and the moon rise on the noth
        and 45 virgins gave birth at the same time 
    """
    pgb = PicoGameBoy()
    del pgb
    pgb = PicoGameBoy()
    
    BLACK = PicoGameBoy.color(0, 0, 0)
    WHITE = PicoGameBoy.color(255, 255, 255)
    pgb.fill(BLACK)
    pgb.show()
    

    while True:
        gc.collect()
        selected_option = display_menu(pgb, menu_itens)

        if selected_option == "Tetris":
            # Example of a game that receives PGB as a parameter
            Tetris.tetris_main(pgb)
            
        elif selected_option == "GameOfLife":
            GameOfLife.gameoflife_main(pgb)
            
        elif selected_option == "FlapBird":
            # Example of a game that does not receives PGB as a parameter
            # First, delete the buffer of the current program
            pgb.reset_buffer()
            # Call the game program
            FlapBird.FlapBird_main()
            # Then, recreate the buffer for this program
            pgb.create_buffer()
            
        elif selected_option == "Exit":
            pgb.fill(BLACK)
            pgb.center_text("Exiting...", WHITE)
            pgb.show()
            time.sleep(2)
            

if __name__ == "__main__":
    main() 