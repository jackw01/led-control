// led-control WS2812B LED Controller Server
// Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

#ifndef __COLOR_TYPES_H__
#define __COLOR_TYPES_H__

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

typedef struct color_hsv_float {
  union {
    struct {
      union {
        float hue;
        float h;
      };
      union {
        float saturation;
        float sat;
        float s;
      };
      union {
        float value;
        float val;
        float v;
      };
    };
    float raw[3];
  };
} color_hsv_float;

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

typedef struct color_rgb_float {
  union {
    struct {
      union {
        float red;
        float r;
      };
      union {
        float green;
        float g;
      };
      union {
        float blue;
        float b;
      };
    };
    float raw[3];
  };
} color_rgb_float;

#endif
