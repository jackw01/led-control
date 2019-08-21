// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

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

// Important stuff starts here

// HSV/RGB types based on FastLED
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

typedef struct color_rgb {
  union {
    struct {
      union {
        uint8_t red;
        uint8_t r;
      };
      union {
        uint8_t green;
        uint8_t g;
      };
      union {
        uint8_t blue;
        uint8_t b;
      };
    };
    uint8_t raw[3];
  };
} color_rgb;

// Unpack 24 bit colors from int
color_hsv unpack_hsv(uint32_t in) {
  uint8_t h = in >> 16 & 0xff;
  uint8_t s = in >> 8 & 0xff;
  uint8_t v = in & 0xff;
  return (color_hsv){ h, s, v };
}

color_rgb unpack_rgb(uint32_t in) {
  uint8_t r = in >> 16 & 0xff;
  uint8_t g = in >> 8 & 0xff;
  uint8_t b = in & 0xff;
  return (color_rgb){ r, g, b };
}

// Pack 24 bit rgb to int
uint32_t pack_rgb(uint8_t r, uint8_t g, uint8_t b) {
  return (r << 16) | (g << 8) | b;
}

// "Rainbow" color transform from FastLED
uint32_t render_hsv2rgb_rainbow(color_hsv hsv, color_rgb corr_rgb) {
  uint8_t hue = hsv.hue;
  uint8_t sat = hsv.sat;
  uint8_t val = hsv.val;
  uint8_t r, g, b;

  uint8_t offset = hue & 0x1F; // 0..31
  uint8_t offset8 = offset << 3;
  uint8_t third = offset8 / 3;

  if (!(hue & 0x80)) {
    if (!(hue & 0x40)) {
      // section 0-1
      if (!(hue & 0x20)) {
        // case 0: // R -> O
        r = 255 - third;
        g = third;
        b = 0;
      } else {
        // case 1: // O -> Y
        r = 171;
        g = 85 + third;
        b = 0;
      }
    } else {
      // section 2-3
      if (!(hue & 0x20)) {
        // case 2: // Y -> G
        r = 171 - third * 2;
        g = 170 + third;
        b = 0;
      } else {
        // case 3: // G -> A
        r = 0;
        g = 255 - third;
        b = third;
      }
    }
  } else {
    // section 4-7
    if (!(hue & 0x40))  {
      if (!(hue & 0x20)) {
        // case 4: // A -> B
        r = 0;
        uint8_t twothirds = third * 2;
        g = 171 - twothirds; // K170?
        b = 85 + twothirds;
      } else {
        // case 5: // B -> P
        r = third;
        g = 0;
        b = 255 - third;
      }
    } else {
      if (!(hue & 0x20)) {
        // case 6: // P -- K
        r = 85 + third;
        g = 0;
        b = 171 - third;
      } else {
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

  r = r * corr_rgb.r / 255;
  g = g * corr_rgb.g / 255;
  b = b * corr_rgb.b / 255;

  return pack_rgb(r, g, b);
}

// Render array of hsv pixels and display
int ws2811_hsv_render(ws2811_t *ws, ws2811_channel_t *channel,
                      uint32_t values[], int count, uint32_t correction){
  if (count > channel->count) return -1;
  color_rgb corr_rgb = unpack_rgb(correction);
  for (int i = 0; i < count; i++) {
    channel->leds[i] = render_hsv2rgb_rainbow(unpack_hsv(values[i]), corr_rgb);
  }
  ws2811_render(ws);
  return 1;
}

// Render array of hsv pixels and display
int ws2811_hsv_render_array(ws2811_t *ws, ws2811_channel_t *channel,
                            color_hsv values[], int count, uint32_t correction){
  if (count > channel->count) return -1;
  color_rgb corr_rgb = unpack_rgb(correction);
  for (int i = 0; i < count; i++) {
    channel->leds[i] = render_hsv2rgb_rainbow(values[i], corr_rgb);
  }
  ws2811_render(ws);
  return 1;
}

#endif
