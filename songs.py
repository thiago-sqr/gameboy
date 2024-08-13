from micropython import const
from PicoGameBoy import PicoGameBoy
from framebuf import FrameBuffer
import time
from random import randint
import _thread
import gc
import adaptation
import tetris

def tetris(pgb):
    while True:
        pgb.play_sound("tetris.wav", readbytes=1, sleep = True)
        if (GAME_OVER == True):
            break