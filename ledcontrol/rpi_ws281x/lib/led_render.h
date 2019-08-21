#ifndef __LED_RENDER_H__
#define __LED_RENDER_H__

ws2811_channel_t *ws2811_channel_get(ws2811_t *ws, int channelnum) {
  return &ws->channel[channelnum];
}

uint32_t ws2811_led_get(ws2811_channel_t *channel, int lednum) {
  if (lednum >= channel->count) return -1;
  return channel->leds[lednum];
}

int ws2811_led_set(ws2811_channel_t *channel, int lednum, uint32_t color) {
  if (lednum >= channel->count) return -1;
  channel->leds[lednum] = color;
  return 0;
}

typedef struct color_hsv {
  union {
    struct {
      union {
        uint8_t hue;
        uint8_t h;
      };
      union {
        uint8_t saturation;
        uint8_t sat;
        uint8_t s;
      };
      union {
        uint8_t value;
        uint8_t val;
        uint8_t v;
      };
    };
    uint8_t raw[3];
  };
} color_hsv;

color_hsv unpack_hsv(uint32_t in) {
  uint8_t h = in >> 16 & 0xff;
  uint8_t s = in >> 8 & 0xff;
  uint8_t v = in & 0xff;
  return (color_hsv) { h, s, v };
}

uint32_t pack_rgb(uint8_t r, uint8_t g, uint8_t b) {
  return (r << 16) | (g << 8) | b;
}

// "Rainbow" color transform from FastLED
uint32_t hsv2rgb_rainbow(color_hsv hsv) {
  uint8_t hue = hsv.hue;
  uint8_t sat = hsv.sat;
  uint8_t val = hsv.val;
  uint8_t r, g, b;

  uint8_t offset = hue & 0x1F; // 0..31
  uint8_t offset8 = offset << 3;

  uint8_t third = offset8 / 3;

  if (!(hue & 0x80)) {
    // 0XX
    if (!(hue & 0x40)) {
      // 00X
      // section 0-1
      if (!(hue & 0x20)) {
        // 000
        // case 0: // R -> O
        r = 255 - third;
        g = third;
        b = 0;
      } else {
        // 001
        // case 1: // O -> Y
        r = 171;
        g = 85 + third;
        b = 0;
      }
    } else {
      // 01X
      // section 2-3
      if (!(hue & 0x20)) {
        // 010
        // case 2: // Y -> G
        r = 171 - third * 2;
        g = 170 + third;
        b = 0;
      } else {
        // 011
        // case 3: // G -> A
        r = 0;
        g = 255 - third;
        b = third;
      }
    }
  } else {
    // section 4-7
    // 1XX
    if (!(hue & 0x40))  {
      // 10X
      if (!(hue & 0x20)) {
        // 100
        // case 4: // A -> B
        r = 0;
        uint8_t twothirds = third * 2;
        g = 171 - twothirds; // K170?
        b = 85 + twothirds;
      } else {
        // 101
        // case 5: // B -> P
        r = third;
        g = 0;
        b = 255 - third;
      }
    } else {
      if (!(hue & 0x20)) {
        // 110
        // case 6: // P -- K
        r = 85 + third;
        g = 0;
        b = 171 - third;
      } else {
        // 111
        // case 7: // K -> R
        r = 170 + third;
        g = 0;
        b = 85 - third;
      }
    }
  }

  // Scale down colors if we're desaturated at all
  // and add the brightness_floor to r, g, and b.
  if (sat != 255) {
    if (sat == 0) {
      r = 255;
      b = 255;
      g = 255;
    } else {
      uint8_t desat = 255 - sat;
      desat = desat * desat / 255;
      r = r * sat / 255 + desat;
      g = g * sat / 255 + desat;
      b = b * sat / 255 + desat;
    }
  }

  // Now scale everything down if we're at value < 255.
  if (val != 255) {
    val = val * val / 255;
    if (val == 0) {
      r = 0;
      g = 0;
      b = 0;
    } else {
      r = r * val / 255;
      g = g * val / 255;
      b = b * val / 255;
    }
  }

  return pack_rgb(r, g, b);
}

int ws2811_led_array_hsv_set(ws2811_t *ws2811, ws2811_channel_t *channel, uint32_t values[], int count)
{
  if (count > channel->count) return -1;
  for (int i = 0; i < count; i++) {
    channel->leds[i] = hsv2rgb_rainbow(unpack_hsv(values[i]));
  }
  ws2811_render(ws2811);
  return count;
}

#endif
