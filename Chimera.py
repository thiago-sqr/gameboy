from machine import Pin, PWM, SPI
from time import sleep
import framebuf
import gc

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class Chimera(framebuf.FrameBuffer):
    
    ANGLES = {
        0: 0x88,
        90: 0xE8,
        180: 0x48,
        270: 0x28
    }

    # Command constants from ILI9341 datasheet
    NOP = b'\x00'  # No-op
    SWRESET = b'\x01'  # Software reset
    RDDID = b'\x04'  # Read display ID info
    RDDST = b'\x09'  # Read display status
    SLPIN = b'\x10'  # Enter sleep mode
    SLPOUT = b'\x11'  # Exit sleep mode
    PTLON = b'\x12'  # Partial mode on
    NORON = b'\x13'  # Normal display mode on
    RDMODE = b'\x0A'  # Read display power mode
    RDMADCTL = b'\x0B'  # Read display MADCTL
    RDPIXFMT = b'\x0C'  # Read display pixel format
    RDIMGFMT = b'\x0D'  # Read display image format
    RDSELFDIAG = b'\x0F'  # Read display self-diagnostic
    INVOFF = b'\x20'  # Display inversion off
    INVON = b'\x21'  # Display inversion on
    GAMMASET = b'\x26'  # Gamma set
    DISPLAY_OFF = b'\x28'  # Display off
    DISPLAY_ON = b'\x29'  # Display on
    SET_COLUMN = b'\x2A'  # Column address set
    SET_PAGE = b'\x2B'  # Page address set
    WRITE_RAM = b'\x2C'  # Memory write
    READ_RAM = b'\x2E'  # Memory read
    PTLAR = b'\x30'  # Partial area
    VSCRDEF = b'\x33'  # Vertical scrolling definition
    MADCTL = b'\x36'  # Memory access control
    VSCRSADD = b'\x37'  # Vertical scrolling start address
    PIXFMT = b'\x3A'  # COLMOD: Pixel format set
    WRITE_DISPLAY_BRIGHTNESS = b'\x51'  # Brightness hardware dependent!
    READ_DISPLAY_BRIGHTNESS = b'\x52'
    WRITE_CTRL_DISPLAY = b'\x53'
    READ_CTRL_DISPLAY = b'\x54'
    WRITE_CABC = b'\x55'  # Write Content Adaptive Brightness Control
    READ_CABC = b'\x56'  # Read Content Adaptive Brightness Control
    WRITE_CABC_MINIMUM = b'\x5E'  # Write CABC Minimum Brightness
    READ_CABC_MINIMUM = b'\x5F'  # Read CABC Minimum Brightness
    FRMCTR1 = b'\xB1'  # Frame rate control (In normal mode/full colors)
    FRMCTR2 = b'\xB2'  # Frame rate control (In idle mode/8 colors)
    FRMCTR3 = b'\xB3'  # Frame rate control (In partial mode/full colors)
    INVCTR = b'\xB4'  # Display inversion control
    DFUNCTR = b'\xB6'  # Display function control
    PWCTR1 = b'\xC0'  # Power control 1
    PWCTR2 = b'\xC1'  # Power control 2
    PWCTRA = b'\xCB'  # Power control A
    PWCTRB = b'\xCF'  # Power control B
    VMCTR1 = b'\xC5'  # VCOM control 1
    VMCTR2 = b'\xC7'  # VCOM control 2
    RDID1 = b'\xDA'  # Read ID 1
    RDID2 = b'\xDB'  # Read ID 2
    RDID3 = b'\xDC'  # Read ID 3
    RDID4 = b'\xDD'  # Read ID 4
    GMCTRP1 = b'\xE0'  # Positive gamma correction
    GMCTRN1 = b'\xE1'  # Negative gamma correction
    DTCA = b'\xE8'  # Driver timing control A
    DTCB = b'\xEA'  # Driver timing control B
    POSC = b'\xED'  # Power on sequence control
    ENABLE3G = b'\xF2'  # Enable 3 gamma control
    PUMPRC = b'\xF7'  # Pump ratio control


    def __init__(self, width=320, height=240, id_=0, sck=18, mosi=19,
                 dc=15, rst=14, cs=17, baudrate=62500000, rotation=90):

        self.width = width
        self.height = height
        self.spi = SPI(id_, sck=Pin(sck), mosi=Pin(mosi), baudrate=baudrate, polarity=0, phase=0)
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        
        if rotation not in self.ANGLES.keys():
            raise RuntimeError('Rotation must be 0, 90, 180 or 270.')
        else:
            self.rotation = self.ANGLES[rotation]
        
        self.create_buffer()
        self.init_display()


    def init_display(self):

        # Hardware reset
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)

        # Send initialization commands
        self.write_cmd(self.SWRESET)  # Software reset
        sleep(.1)
        self.write_cmd(self.PWCTRB, b'\x00\xC1\x30')  # Pwr ctrl B
        self.write_cmd(self.POSC, b'\x64\x03\x12\x81')  # Pwr on seq. ctrl
        self.write_cmd(self.DTCA, b'\x85\x00\x78')  # Driver timing ctrl A
        self.write_cmd(self.PWCTRA, b'\x39\x2C\x00\x34\x02')  # Pwr ctrl A
        self.write_cmd(self.PUMPRC, b'\x20')  # Pump ratio control
        self.write_cmd(self.DTCB, b'\x00\x00')  # Driver timing ctrl B
        self.write_cmd(self.PWCTR1, b'\x23')  # Pwr ctrl 1
        self.write_cmd(self.PWCTR2, b'\x10')  # Pwr ctrl 2
        self.write_cmd(self.VMCTR1, b'\x3E\x28]')  # VCOM ctrl 1
        self.write_cmd(self.VMCTR2, b'0\x86')  # VCOM ctrl 2
        self.write_cmd(self.MADCTL, bytes([self.rotation]))  # Memory access ctrl
        sleep(0.1)
        self.write_cmd(self.VSCRSADD, b'\x00')  # Vertical scrolling start address
        self.write_cmd(self.PIXFMT, b'\x55')  # COLMOD: Pixel format
        self.write_cmd(self.FRMCTR1, b'\x00\x18')  # Frame rate ctrl
        self.write_cmd(self.DFUNCTR, b'\x08\x82\x27')
        self.write_cmd(self.ENABLE3G, b'\0x00')  # Enable 3 gamma ctrl
        self.write_cmd(self.GAMMASET, b'\x01')  # Gamma curve selected
        self.write_cmd(self.GMCTRP1, b'\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00')
        self.write_cmd(self.GMCTRN1, b'\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F')

        self.write_cmd(self.SLPOUT)  # Exit sleep
        sleep(.1)
        self.write_cmd(self.DISPLAY_ON)  # Display on
        sleep(.1)
        super().fill(0)
        self.show()
        
        
    def reset_buffer(self):
        """
        Reduce the buffer to store two bytes (minimum), freeing up space for other things
        """
        self.buffer = memoryview(bytearray(b'\x00\x00'))
        super().__init__(self.buffer, 1, 1, framebuf.RGB565)
        gc.collect()
        
        
    def create_buffer(self):
        self.buffer = memoryview(bytearray(self.width * self.height * 2))
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
         
         
    def reset(self):
        # Perform reset: Low=initialization, High=normal operation.
        self.rst(0)
        sleep(.05)
        self.rst(1)
        sleep(.05)
    
    
    def write_cmd(self, cmd=None, data=None):
        self.cs(0)
        if cmd:
            self.dc(0) # command mode
            self.spi.write(cmd)
        if data:
            self.dc(1) # data mode
            self.spi.write(data)
        self.cs(1)


    def rotate(self , angle):
        # Apply a new rotation to the screen
        newAngle = 0x00
        if angle not in self.ANGLES.keys():
            raise RuntimeError('Angle must be 0, 90, 180 or 270.')
        else:
            newAngle = self.ANGULOS[angle]
        self.write_cmd(self.MADCTL, bytes([newAngle]))


    def show(self):
        self.write_cmd(self.WRITE_RAM, self.buffer)
        
        
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
        # Apparently, this function does not work as it should; the image comes out corrupted
        with open(filename , "rb") as file:
            file.readinto(self.buffer)


    def get_pixel(self , x , y):
        byte1 = self.buffer[2 * (y * self.width + x)]
        byte2 = self.buffer[2 * (y * self.width + x) + 1]
        return byte2 * 256 + byte1
    
    
    def __del__ (self):
        self.reset_buffer()
        
    