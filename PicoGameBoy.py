# PicoGameBoy.py by Vincent Mistler for YouMakeTech
# A class to easily write games for the Raspberry Pi Pico Game Boy
from machine import Pin , PWM , SPI, reset
from framebuf import FrameBuffer , RGB565
from Quimera import Quimera
from time import sleep, sleep_us
import struct


class PicoGameBoy(Quimera):
    def __init__(self):
        self.__up = Pin(2, Pin.IN , Pin.PULL_UP)
        self.__down = Pin(3, Pin.IN , Pin.PULL_UP)
        self.__left = Pin(4, Pin.IN , Pin.PULL_UP)
        self.__right = Pin(5, Pin.IN , Pin.PULL_UP)
        self.__button_A = Pin(6, Pin.IN , Pin.PULL_UP)
        self.__button_B = Pin(7, Pin.IN , Pin.PULL_UP)
        self.__button_off = Pin(8, Pin.IN, Pin.PULL_UP)
        self.__buzzer = PWM(Pin(13))
        self.__speaker = PWM(Pin(26))
        

        super().__init__(cs=17, dc=15, rst=14, sck=18, mosi=19)

        self.__fb = []  # Array of FrameBuffer objects for sprites
        self.__w = []
        self.__h = []
        
        self.SAMPLE_RATE = 44100
        self.VOLUME = 1
        self.__speaker.freq(self.SAMPLE_RATE)
        

    # center_text(s,color) displays a text in the middle of 
    # the screen with the specified color
    def center_text(self , s , color=1):
        x = int(self.width / 2) - int(len(s) / 2 * 8)
        y = int(self.height / 2) - 8
        self.text(s , x , y , color)

    # center_text(s,color) displays a text in the right corner of 
    # the screen with the specified color
    def top_right_corner_text(self , s , color=1):
        x = self.width - int(len(s) * 8)
        y = 0
        self.text(s , x , y , color)

    # add_sprite(buffer,w,h) creates a new sprite from framebuffer
    # with a width of w and a height of h
    # The first sprite is #0 and can be displayed by sprite(0,x,y)
    def add_sprite(self , buffer , w , h):
        fb = FrameBuffer(buffer , w , h , RGB565)
        self.__fb.append(fb)
        self.__w.append(w)
        self.__h.append(h)

    # add_rect_sprite(color,w,h) creates a new rectangular sprite
    # with the specified color, width and height
    def add_rect_sprite(self , color , w , h):
        buffer = bytearray(w * h * 2)  # 2 bytes per pixel
        # fill the buffer with the specified color
        lsb = (color & 0b0000000011111111)
        msb = (color & 0b1111111100000000) >> 8
        for i in range(0 , w * h * 2 , 2):
            buffer[i] = lsb
            buffer[i + 1] = msb
        fb = FrameBuffer(buffer , w , h , RGB565)
        self.__fb.append(fb)
        self.__w.append(w)
        self.__h.append(h)

    # sprite(n,x,y) displays the nth sprite at coordinates (x,y)
    # the sprite must be created first by method add_sprite
    def sprite(self , n , x , y):
        self.blit(self.__fb[n] , x , y)

    # sprite_width(n) returns the width of the nth sprite in pixels
    def sprite_width(self , n):
        return self.__w[n]

    # sprite_height(n) returns the height of the nth sprite in pixels
    def sprite_height(self , n):
        return self.__h[n]

    # button_up() returns True when the player presses the up button
    def button_up(self):
        return self.__up.value() == 0

    # button_down() returns True when the player presses the down button
    def button_down(self):
        return self.__down.value() == 0

    # button_left() returns True when the player presses the left button
    def button_left(self):
        return self.__left.value() == 0

    # button_right() returns True when the player presses the right button
    def button_right(self):
        return self.__right.value() == 0

    # button_A() returns True when the player presses the A button
    def button_A(self):
        return self.__button_A.value() == 0

    # button_B() returns True when the player presses the B button
    def button_B(self):
        return self.__button_B.value() == 0
    
    def button_off(self):
        return self.__button_off.value() == 0

    # any_button() returns True if any button is pressed
    def any_button(self):
        button_pressed = False
        if self.button_up():
            button_pressed = True
        if self.button_down():
            button_pressed = True
        if self.button_left():
            button_pressed = True
        if self.button_right():
            button_pressed = True
        if self.button_A():
            button_pressed = True
        if self.button_B():
            button_pressed = True
        return button_pressed

    # sound(freq) makes a sound at the selected frequency in Hz
    # call sound(0) to stop playing the sound
    def sound(self , freq , duty_u16=5000):
        if freq > 0:
            self.__buzzer.freq(freq)
            self.__buzzer.duty_u16(duty_u16)
        else:
            self.__buzzer.duty_u16(0)
    
    
    def enter_low_power(self):
        while True:
            True
            if self.button_off():
                sleep(1)  # Debouncing or holding the button for 1 second
                reset()  # This resets the Pico, effectively shutting it down
            time.sleep(0.1)
        
    def play_sound(self, audio):
        with open(audio, 'rb') as f:
            f.read(44)  # Skip the 44-byte WAV header
            while True:
                byte = f.read(1)  # Read one byte at a time
                if not byte:
                    break
                sample = struct.unpack('<B', byte)[0]  # Convert byte to int
                sample = int(sample * self.VOLUME)
                self.__speaker.duty_u16(sample * 256)  # Convert 8-bit sample to 16-bit PWM duty
                sleep_us(int(1e6 / self.SAMPLE_RATE))
                
                
                
                
if __name__ == "__main__":
    pgb = PicoGameBoy()

    # Colors (RGB)
    # Note that color is a static method and can be called
    # without creating an object (PicoGameBoy.color instead of pgb.color)
    BLACK = PicoGameBoy.color(0 , 0 , 0)
    WHITE = PicoGameBoy.color(255 , 255 , 255)
    RED = PicoGameBoy.color(255 , 0 , 0)
    GREEN = PicoGameBoy.color(0 , 255 , 0)
    BLUE = PicoGameBoy.color(0 , 0 , 255)

    # PicoGameBoy inherits all methods from the FrameBuffer class
    # see https://docs.micropython.org/en/latest/library/framebuf.html

    pgb.fill(BLACK)

    # The Raspberry Pi Pico GameBoy uses a framebuffer
    # The framebuffer is only transfered to the actual screen and become visible
    # when calling show()
    pgb.show()
    
    pgb.play_sound('tetris.wav')

    # Drawing primitive shapes
    # The screen resolution is 240x240 pixels but Python like many programming 
    # languages starts counting from zero, not one.
    # The top left corner is (0,0) and bottom right is (239,239)
    pgb.pixel(0 , 0 , WHITE)
    pgb.pixel(239 , 239 , BLUE)
    pgb.show()
    sleep(1)

    pgb.line(0 , 239 , 239 , 0 , RED)
    pgb.show()
    sleep(1)

    pgb.rect(10 , 10 , 220 , 220 , WHITE)
    pgb.show()
    sleep(1)

    pgb.fill_rect(10 , 10 , 220 , 220 , WHITE)
    pgb.show()
    sleep(1)

    # text
    pgb.fill(BLACK)
    pgb.text('Hello from Pi Pico GameBoy!' , 0 , 0 , GREEN)
    pgb.show()
    sleep(1)

    pgb.center_text('GAME OVER' , WHITE)
    pgb.show()
    sleep(1)

    # sprites
    x = 120
    y = 120
    pgb.fill(BLACK)
    pgb.add_rect_sprite(GREEN , 12 , 12)  # Create sprite #0
    while True:
        pgb.sprite(0 , x , y)
        pgb.show()
        while not pgb.any_button():
            sleep(0.020)
        if pgb.button_right():
            x = x + 1
        elif pgb.button_left():
            x = x - 1
        elif pgb.button_up():
            y = y - 1
        elif pgb.button_down():
            y = y + 1

