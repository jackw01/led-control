// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

#ifndef __ANIMATION_UTILS_H__
#define __ANIMATION_UTILS_H__

#include <math.h>

// Optimized C utility functions
// Waveforms for pattern generation. All have a period of 1 time unit and range from 0-1.

// Pulse with duty cycle
float wave_pulse(float t, float duty_cycle) {
  return ceil(duty_cycle - fmod(t, 1.0));
}

// Triangle
float wave_triangle(float t) {
  return fabs(fmod(2.0 * t, 2.0) - 1.0);
}

// Sine
float wave_sine(float t) {
  return cos(6.283 * t) / 2.0 + 0.5;
}

// Sine approximation (triangle wave with cubic in-out easing)
float wave_cubic(float t) {
  float tri = fabs(fmod(2.0 * t, 2.0) - 1.0);
  if (tri > 0.5) {
    float t2 = 1.0 - tri;
    return 1.0 - 4.0 * t2 * t2 * t2;
  } else {
    return 4.0 * tri * tri * tri;
  }
}

// Sum of sines for creating RGB plasma shader effects
// See https://www.bidouille.org/prog/plasma
float plasma_sines(float x, float y, float t,
                   float coeff_x, float coeff_y, float coeff_x_y, float coeff_dist_xy) {
  float v = 0.0;
  v += sin((x + t) * coeff_x);
  v += sin((y + t) * coeff_y);
  v += sin((x + y + t) * coeff_x_y);
  v += sin((sqrtf(x * x + y * y) + t) * coeff_dist_xy);
  return v;
}

// Plasma sines plus RGB color generation
color_rgb_float plasma_rgb(float x, float y, float t,
                           float coeff_x, float coeff_y, float coeff_x_y, float coeff_dist_xy,
                           float delay_r, float delay_g, float delay_b,
                           float freq_r, float freq_g, float freq_b) {
  float v = plasma_sines(x, y, t, coeff_x, coeff_y, coeff_x_y, coeff_dist_xy);
  float r = wave_sine(v * freq_r + delay_r);
  float g = wave_sine(v * freq_g + delay_g);
  float b = wave_sine(v * freq_b + delay_b);
  return (color_rgb_float){ r, g, b };
}

#endif
