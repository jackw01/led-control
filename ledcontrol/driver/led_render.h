// led-control WS2812B LED Controller Server
// Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

#ifndef __LED_RENDER_H__
#define __LED_RENDER_H__

#include <math.h>

const uint8_t debug = 0;

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

// Unpack 24 bit rgb from int
color_rgb unpack_rgb(uint32_t in) {
  uint8_t r = in >> 16 & 0xff;
  uint8_t g = in >> 8 & 0xff;
  uint8_t b = in & 0xff;
  return (color_rgb){ r, g, b };
}

// Pack 32 bit rgbw to int
uint32_t pack_rgbw(uint8_t r, uint8_t g, uint8_t b, uint8_t w) {
  return (w << 24) | (r << 16) | (g << 8) | b;
}

// Scale one 8 bit int by another (a * b / 255)
uint8_t scale_8(uint8_t a, uint8_t b) {
  return ((uint16_t)a * (uint16_t)b) >> 8;
}

// Float clamp
float clamp(float d, float min, float max) {
  const float t = d < min ? min : d;
  return t > max ? max : t;
}

color_rgb_float blackbody_to_rgb(float kelvin) {
  // See http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
  // See http://www.zombieprototypes.com/?p=210

  float tmp_internal = kelvin / 100.0;
  float r_out = 0.0;
  float g_out = 0.0;
  float b_out = 0.0;

  if (tmp_internal <= 66) {
    float xg = tmp_internal - 2.0;
    r_out = 1.0;
    g_out = clamp((-155.255 - 0.446 * xg + 104.492 * logf(xg)) / 255.0, 0, 1);
  } else {
    float xr = tmp_internal - 55.0;
    float xg = tmp_internal - 50.0;
    r_out = clamp((351.977 + 0.114 * xr - 40.254 * logf(xr)) / 255.0, 0, 1);
    g_out = clamp((325.449 + 0.079 * xg - 28.085 * logf(xg)) / 255.0, 0, 1);
  }

  if (tmp_internal >= 66) {
    b_out = 1.0;
  } else if (tmp_internal <= 19) {
    b_out = 0.0;
  } else {
    float xb = tmp_internal - 10.0;
    b_out = clamp((-254.769 + 0.827 * xb + 115.680 * logf(xb)) / 255.0, 0, 1);
  }

  return (color_rgb_float){r_out, g_out, b_out};
}

color_rgb_float blackbody_correction_rgb(color_rgb_float rgb, float kelvin) {
  color_rgb_float bb = blackbody_to_rgb(kelvin);
  return (color_rgb_float){bb.r * rgb.r, bb.g * rgb.g, bb.b * rgb.b};
}

// Render float HSV to LEDs with "Rainbow" color transform from FastLED
uint32_t render_hsv2rgb_rainbow_float(color_hsv_float hsv,
                                      color_rgb corr_rgb, float saturation,
                                      float brightness, float gamma,
                                      uint8_t has_white) {
  uint8_t hue = fmod(hsv.hue, 1.0) * 255.0;
  uint8_t sat = hsv.sat * saturation * 255.0;
  uint8_t val = (hsv.val * hsv.val) * 255;
  if (val > 0 && val < 255) val += 1;
  val = scale_8(val, brightness * 255);
  uint8_t r, g, b, w;

  w = 0;

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
  if (has_white) {
    if (sat != 255) {
      if (sat == 0) {
        r = 0;
        b = 0;
        g = 0;
        w = 255;
      } else {
        uint8_t desat = 255 - sat;
        desat = scale_8(desat, desat);
        r = scale_8(r, sat);
        g = scale_8(g, sat);
        b = scale_8(b, sat);
        w = desat;
      }
    }
  } else {
    if (sat != 255) {
      if (sat == 0) {
        r = 255;
        b = 255;
        g = 255;
      } else {
        uint8_t desat = 255 - sat;
        desat = scale_8(desat, desat);
        r = scale_8(r, sat) + desat;
        g = scale_8(g, sat) + desat;
        b = scale_8(b, sat) + desat;
      }
    }
    /*
    if (gamma != 1) {
      r = pow((float)r / 255.0, gamma) * 255;
      g = pow((float)g / 255.0, gamma) * 255;
      b = pow((float)b / 255.0, gamma) * 255;
    }
    */
  }

  // Now scale everything down if we're at value < 255.
  if (val != 255) {
    if (val == 0) {
      r = 0;
      g = 0;
      b = 0;
      w = 0;
    } else {
      r = scale_8(r, val);
      g = scale_8(g, val);
      b = scale_8(b, val);
      w = scale_8(w, val);
    }
  }

  r = scale_8(r, corr_rgb.r);
  g = scale_8(g, corr_rgb.g);
  b = scale_8(b, corr_rgb.b);

  if (debug) printf("%d %d %d %d\n", r, g, b, w);
  return pack_rgbw(r, g, b, w);
}

// Render float RGB to LEDs
uint32_t render_rgb_float(color_rgb_float rgb,
                          color_rgb corr_rgb, float saturation,
                          float brightness, float gamma,
                          uint8_t has_white) {
  float r = clamp(rgb.r, 0, 1);
  float g = clamp(rgb.g, 0, 1);
  float b = clamp(rgb.b, 0, 1);
  float w = 0;
  uint8_t sat = saturation * 255.0;
  if (debug) printf("%d %d %d %d\n", r, g, b, sat);

  if (has_white) {
    float max = r > g ? (r > b ? r : b) : (g > b ? g : b);
    float min;
    if (sat == 0) {
      r = 0;
      g = 0;
      b = 0;
      min = max;
    } else {
      r = (r - max) * saturation + max;
      g = (g - max) * saturation + max;
      b = (b - max) * saturation + max;
      min = r < g ? (r < b ? r : b) : (g < b ? g : b);
      //r -= min;
      //g -= min;
      //b -= min;
    }
    w = min * min;
  } else {
    // If saturation is not 1, desaturate the color
    // Moves r/g/b values closer to their average
    // Not sure if this is the technically correct way but it seems to work?
    if (sat != 255) {
      float v = (r + g + b) / 3.0;
      if (sat == 0) {
        r = v;
        b = v;
        g = v;
      } else {
        r = (r - v) * saturation + v;
        g = (g - v) * saturation + v;
        b = (b - v) * saturation + v;
      }
    }
  }

  /*
  if (gamma != 1) {
    r = pow(r, gamma);
    g = pow(g, gamma);
    b = pow(b, gamma);
  }
  */

  uint8_t r8 = r * brightness * 255;
  uint8_t g8 = g * brightness * 255;
  uint8_t b8 = b * brightness * 255;
  uint8_t w8 = w * brightness * 255;

  r8 = scale_8(r8, corr_rgb.r);
  g8 = scale_8(g8, corr_rgb.g);
  b8 = scale_8(b8, corr_rgb.b);

  if (debug) printf("%d %d %d %d\n", r8, g8, b8, w8);
  return pack_rgbw(r8, g8, b8, w8);
}

// Render array of hsv pixels and display
int ws2811_hsv_render_array_float(ws2811_t *ws, ws2811_channel_t *channel,
                                  color_hsv_float values[], int count,
                                  uint32_t correction, float saturation,
                                  float brightness, float gamma,
                                  uint8_t has_white){
  if (count > channel->count) return -1;
  color_rgb corr_rgb = unpack_rgb(correction);
  for (int i = 0; i < count; i++) {
    channel->leds[i] = render_hsv2rgb_rainbow_float(values[i], corr_rgb,
                                                    saturation, brightness,
                                                    gamma, has_white);
  }
  ws2811_render(ws);
  return 1;
}

// Render array of rgb pixels and display
int ws2811_rgb_render_array_float(ws2811_t *ws, ws2811_channel_t *channel,
                                  color_rgb_float values[], int count,
                                  uint32_t correction, float saturation,
                                  float brightness, float gamma,
                                  uint8_t has_white){
  if (count > channel->count) return -1;
  color_rgb corr_rgb = unpack_rgb(correction);
  for (int i = 0; i < count; i++) {
    channel->leds[i] = render_rgb_float(values[i], corr_rgb,
                                        saturation, brightness,
                                        gamma, has_white);
  }
  ws2811_render(ws);
  return 1;
}

#endif
