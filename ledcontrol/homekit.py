import threading
import signal

from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

class LEDControlHomeKitAccessory(Accessory):

    category = CATEGORY_LIGHTBULB  # This is for the icon in the iOS Home app.

    def __init__(self, *args, **kwargs):
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        # Add the services that this Accessory will support with add_preload_service here
        self._serv_light = self.add_preload_service('Lightbulb', chars=['On', 'Brightness', 'Saturation'])
        self.on = self._serv_light.configure_char('On', value=1)
        self.brightness = self._serv_light.configure_char('Brightness', value=100)
        self.saturation = self._serv_light.configure_char('Saturation', value=100)

    def set_setter_callback(self, callback):
        self._serv_light.setter_callback = callback

def homekit_start(setter_callback):
    # Start the accessory on port 51826
    driver = AccessoryDriver(port=51826)

    accessory = LEDControlHomeKitAccessory(driver, 'LEDControl')
    accessory.set_setter_callback(setter_callback)
    driver.add_accessory(accessory=accessory)

    # We want SIGTERM (terminate) to be handled by the driver itself,
    # so that it can gracefully stop the accessory, server and advertising.
    signal.signal(signal.SIGTERM, driver.signal_handler)

    # Start it!
    thread = threading.Thread(target=driver.start)
    thread.start()

    return accessory
