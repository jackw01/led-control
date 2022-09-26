import signal
import random

from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

class LEDControlHomeKitAccessory(Accessory):

    category = CATEGORY_LIGHTBULB  # This is for the icon in the iOS Home app.

    def __init__(self, *args, **kwargs):
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        # Add the services that this Accessory will support with add_preload_service here
        serv_light = self.add_preload_service('Lightbulb', chars=['On', 'Brightness'])
        self.char_on = serv_light.configure_char('On', value=1)
        self.char_brightness = serv_light.configure_char('Brightness', value=100)

        serv_light.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "On" in char_values:
            print('On changed to: ', char_values["On"])
        if "Brightness" in char_values:
            print('Brightness changed to: ', char_values["Brightness"])

    @Accessory.run_at_interval(3)  # Run this method every 3 seconds
    # The `run` method can be `async` as well
    def run(self):
        self.char_on.set_value(random.randint(0, 1))
        self.char_brightness.set_value(random.randint(1, 100))

    # The `stop` method can be `async` as well
    def stop(self):
        print('Stopping accessory.')

def homekit_start():
    # Start the accessory on port 51826
    driver = AccessoryDriver(port=51826)

    # Change `get_accessory` to `get_bridge` if you want to run a Bridge.
    driver.add_accessory(accessory=LEDControlHomeKitAccessory(driver, 'LEDControl'))

    # We want SIGTERM (terminate) to be handled by the driver itself,
    # so that it can gracefully stop the accessory, server and advertising.
    signal.signal(signal.SIGTERM, driver.signal_handler)

    # Start it!
    driver.start()

