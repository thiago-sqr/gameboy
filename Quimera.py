# st7789.py by Vincent Mistler for YouMakeTech
# MicroPython ST7789 OLED driver, SPI interfaces for the Raspberry Pi Pico Game Boy

from micropython import const
from machine import Pin, PWM, SPI
import framebuf
from time import sleep


# register definitions

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class Quimera(framebuf.FrameBuffer):   
    ROTATE = {
        0: 0x88,
        90: 0xE8,
        180: 0x48,
        270: 0x28
    }

    # Command constants from ILI9341 datasheet
    NOP = const(0x00)  # No-op
    SWRESET = const(0x01)  # Software reset
    RDDID = const(0x04)  # Read display ID info
    RDDST = const(0x09)  # Read display status
    SLPIN = const(0x10)  # Enter sleep mode
    SLPOUT = const(0x11)  # Exit sleep mode
    PTLON = const(0x12)  # Partial mode on
    NORON = const(0x13)  # Normal display mode on
    RDMODE = const(0x0A)  # Read display power mode
    RDMADCTL = const(0x0B)  # Read display MADCTL
    RDPIXFMT = const(0x0C)  # Read display pixel format
    RDIMGFMT = const(0x0D)  # Read display image format
    RDSELFDIAG = const(0x0F)  # Read display self-diagnostic
    INVOFF = const(0x20)  # Display inversion off
    INVON = const(0x21)  # Display inversion on
    GAMMASET = const(0x26)  # Gamma set
    DISPLAY_OFF = const(0x28)  # Display off
    DISPLAY_ON = const(0x29)  # Display on
    SET_COLUMN = const(0x2A)  # Column address set
    SET_PAGE = const(0x2B)  # Page address set
    WRITE_RAM = const(0x2C)  # Memory write
    READ_RAM = const(0x2E)  # Memory read
    PTLAR = const(0x30)  # Partial area
    VSCRDEF = const(0x33)  # Vertical scrolling definition
    MADCTL = const(0x36)  # Memory access control
    VSCRSADD = const(0x37)  # Vertical scrolling start address
    PIXFMT = const(0x3A)  # COLMOD: Pixel format set
    WRITE_DISPLAY_BRIGHTNESS = const(0x51)  # Brightness hardware dependent!
    READ_DISPLAY_BRIGHTNESS = const(0x52)
    WRITE_CTRL_DISPLAY = const(0x53)
    READ_CTRL_DISPLAY = const(0x54)
    WRITE_CABC = const(0x55)  # Write Content Adaptive Brightness Control
    READ_CABC = const(0x56)  # Read Content Adaptive Brightness Control
    WRITE_CABC_MINIMUM = const(0x5E)  # Write CABC Minimum Brightness
    READ_CABC_MINIMUM = const(0x5F)  # Read CABC Minimum Brightness
    FRMCTR1 = const(0xB1)  # Frame rate control (In normal mode/full colors)
    FRMCTR2 = const(0xB2)  # Frame rate control (In idle mode/8 colors)
    FRMCTR3 = const(0xB3)  # Frame rate control (In partial mode/full colors)
    INVCTR = const(0xB4)  # Display inversion control
    DFUNCTR = const(0xB6)  # Display function control
    PWCTR1 = const(0xC0)  # Power control 1
    PWCTR2 = const(0xC1)  # Power control 2
    PWCTRA = const(0xCB)  # Power control A
    PWCTRB = const(0xCF)  # Power control B
    VMCTR1 = const(0xC5)  # VCOM control 1
    VMCTR2 = const(0xC7)  # VCOM control 2
    RDID1 = const(0xDA)  # Read ID 1
    RDID2 = const(0xDB)  # Read ID 2
    RDID3 = const(0xDC)  # Read ID 3
    RDID4 = const(0xDD)  # Read ID 4
    GMCTRP1 = const(0xE0)  # Positive gamma correction
    GMCTRN1 = const(0xE1)  # Negative gamma correction
    DTCA = const(0xE8)  # Driver timing control A
    DTCB = const(0xEA)  # Driver timing control B
    POSC = const(0xED)  # Power on sequence control
    ENABLE3G = const(0xF2)  # Enable 3 gamma control
    PUMPRC = const(0xF7)  # Pump ratio control

    def __init__(self, width=240, height=240, id_=0, sck=18, mosi=19,
                 dc=15, rst=14, cs=17, baudrate=62500000, rotation=0):

        self.width = width
        self.height = height
        self.spi = SPI(id_, sck=Pin(sck), mosi=Pin(mosi), baudrate=baudrate, polarity=0, phase=0)
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        
        if rotation not in self.ROTATE.keys():
            raise RuntimeError('Rotation must be 0, 90, 180 or 90.')
        else:
            self.rotation = self.ROTATE[rotation]
        
        self.tamanho_buffer = 240 * 240 * 2
        self.buffer = bytearray(self.tamanho_buffer)
        super().__init__(self.buffer, 240, 240, framebuf.RGB565)

        self.init_display()

    def init_display(self):

        # Hardware reset
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        self.reset = self.reset_mpy
        self.write_cmd = self.write_cmd_mpy
        self.write_data = self.write_data_mpy

        # Send initialization commands
        self.write_cmd(self.SWRESET)  # Software reset
        sleep(.1)
        self.write_cmd(self.PWCTRB , 0x00 , 0xC1 , 0x30)  # Pwr ctrl B
        self.write_cmd(self.POSC , 0x64 , 0x03 , 0x12 , 0x81)  # Pwr on seq. ctrl
        self.write_cmd(self.DTCA , 0x85 , 0x00 , 0x78)  # Driver timing ctrl A
        self.write_cmd(self.PWCTRA , 0x39 , 0x2C , 0x00 , 0x34 , 0x02)  # Pwr ctrl A
        self.write_cmd(self.PUMPRC , 0x20)  # Pump ratio control
        self.write_cmd(self.DTCB , 0x00 , 0x00)  # Driver timing ctrl B
        self.write_cmd(self.PWCTR1 , 0x23)  # Pwr ctrl 1
        self.write_cmd(self.PWCTR2 , 0x10)  # Pwr ctrl 2
        self.write_cmd(self.VMCTR1 , 0x3E , 0x28)  # VCOM ctrl 1
        self.write_cmd(self.VMCTR2 , 0x86)  # VCOM ctrl 2
        self.write_cmd(self.MADCTL , self.rotation)  # Memory access ctrl
        self.write_cmd(self.VSCRSADD , 0x00)  # Vertical scrolling start address
        self.write_cmd(self.PIXFMT , 0x55)  # COLMOD: Pixel format
        self.write_cmd(self.FRMCTR1 , 0x00 , 0x18)  # Frame rate ctrl
        self.write_cmd(self.DFUNCTR , 0x08 , 0x82 , 0x27)
        self.write_cmd(self.ENABLE3G , 0x00)  # Enable 3 gamma ctrl
        self.write_cmd(self.GAMMASET , 0x01)  # Gamma curve selected
        self.write_cmd(self.GMCTRP1 , 0x0F , 0x31 , 0x2B , 0x0C , 0x0E , 0x08 , 0x4E ,
                      0xF1 , 0x37 , 0x07 , 0x10 , 0x03 , 0x0E , 0x09 , 0x00)
        self.write_cmd(self.GMCTRN1 , 0x00 , 0x0E , 0x14 , 0x03 , 0x11 , 0x07 , 0x31 ,
                      0xC1 , 0x48 , 0x08 , 0x0F , 0x0C , 0x31 , 0x36 , 0x0F)
        self.write_cmd(self.SLPOUT)  # Exit sleep
        sleep(.1)
        self.write_cmd(self.DISPLAY_ON)  # Display on
        sleep(.1)
        super().fill(0)
        self.show()
    
    def reset_mpy(self):
        """Perform reset: Low=initialization, High=normal operation.

        Notes: MicroPython implemntation
        """
        self.rst(0)
        sleep(.05)
        self.rst(1)
        sleep(.05)
    
    def write_data_mpy(self, data):
        self.dc(1)
        self.cs(0)
        if type(data[0]) == bytearray:
            self.spi.write(data[0])
        else:
            self.spi.write(bytearray(data))
        self.cs(1)
        
    def write_cmd_mpy(self, command, *args):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        # Handle any passed data
        if len(args) > 0:
            self.write_data(args)

    def power_off(self):
        super().fill(0)
        self.show()
        self.write_cmd(self.DISPLAY_OFF)  # Turn off the display
        sleep(.1)  # Small delay to ensure command is processed
        self.write_cmd(self.SLPIN)  # Enter sleep mode
        sleep(.1)  # Small delay to ensure command is processed


    def power_on(self):
        pass

    def contrast(self , contrast):
        pass

    def invert(self , invert):
        pass

    def rotate(self , rotate):
        pass

    def show(self):
        self.write_cmd(WRITE_RAM, self.buffer)
        
    def color(r , g , b):
        """
        color(r, g, b) returns a 16 bits integer color code for the ST7789 display


        where:
            r (int): Red value between 0 and 255
            g (int): Green value between 0 and 255
            b (int): Blue value between 0 and 255
        """
        # rgb (24 bits) -> rgb565 conversion (16 bits)
        # rgb = r(8 bits) + g(8 bits) + b(8 bits) = 24 bits
        # rgb565 = r(5 bits) + g(6 bits) + b(5 bits) = 16 bits
        r5 = (r & 0b11111000) >> 3
        g6 = (g & 0b11111100) >> 2
        b5 = (b & 0b11111000) >> 3
        rgb565 = (r5 << 11) | (g6 << 5) | b5

        # swap LSB and MSB bytes before sending to the screen
        lsb = (rgb565 & 0b0000000011111111)
        msb = (rgb565 & 0b1111111100000000) >> 8

        return (lsb << 8) | msb

    def load_image(self , filename):
        open(filename , "rb").readinto(self.buffer)

    def get_pixel(self , x , y):
        byte1 = self.buffer[2 * (y * self.width + x)]
        byte2 = self.buffer[2 * (y * self.width + x) + 1]
        return byte2 * 256 + byte1

