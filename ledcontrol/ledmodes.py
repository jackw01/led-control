from enum import IntEnum

class LEDColorAnimationMode(IntEnum):
    SolidColor = 0
    CycleHue = 1
    Sines = 2

class LEDSecondaryAnimationMode(IntEnum):
    Static = 0
    Wave = 1
    Trail = 2
    Twinkle = 3
