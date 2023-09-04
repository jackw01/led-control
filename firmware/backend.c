#include "ws2812b.pio.h"
#include "backend.h"

// PIO

const PIO PIOBlock = pio0;
const uint PIOStateMachine = 0;

// LEDs

uint shift_r, shift_g, shift_b, shift_w;
uint32_t frame_buffer[LEDCount];
bool has_white;

uint8_t backend_incoming_data_buffer[BackendIncomingDataBufferSize];

uint32_t pack_rgbw(uint8_t r, uint8_t g, uint8_t b, uint8_t w) {
  return (w << shift_w) | (r << shift_r) | (g << shift_g) | (b << shift_b);
}

uint8_t scale_8(uint8_t a, uint8_t b) {
  return ((uint16_t)a * (uint16_t)b) >> 8;
}

void backend_write_frame_buffer() {
  for (uint i = 0; i < LEDCount; i++) {
    pio_sm_put_blocking(PIOBlock, PIOStateMachine, frame_buffer[i]);
  }
}

uint32_t render_hsv2rgb_rainbow(uint8_t h, uint8_t s, uint8_t v,
                                uint8_t corr_r, uint8_t corr_g, uint8_t corr_b,
                                uint8_t saturation, uint8_t brightness) {
  uint8_t hue = h;
  uint8_t sat = scale_8(s, saturation);
  uint8_t val = scale_8(v, v);
  if (val > 0 && val < 255) val += 1;
  val = scale_8(val, brightness);
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

  r = scale_8(r, corr_r);
  g = scale_8(g, corr_g);
  b = scale_8(b, corr_b);

  return pack_rgbw(r, g, b, w);
}

uint32_t render_rgb(uint8_t r, uint8_t g, uint8_t b,
                    uint8_t corr_r, uint8_t corr_g, uint8_t corr_b,
                    uint8_t saturation, uint8_t brightness) {
  uint8_t w = 0;

  if (has_white) {
    uint8_t max = r > g ? (r > b ? r : b) : (g > b ? g : b);
    uint8_t min;
    if (saturation == 0) {
      r = 0;
      g = 0;
      b = 0;
      min = max;
    } else {
      r = (int)r - max * (int)saturation / 255 + max;
      g = (int)g - max * (int)saturation / 255 + max;
      b = (int)b - max * (int)saturation / 255 + max;
      min = r < g ? (r < b ? r : b) : (g < b ? g : b);
      r -= min;
      g -= min;
      b -= min;
    }
    w = scale_8(min, min);
  } else {
    // If saturation is not 1, desaturate the color
    // Moves r/g/b values closer to their average
    // Not sure if this is the technically correct way but it seems to work?
    if (saturation != 255) {
      uint8_t v = (r + g + b) / 3;
      if (saturation == 0) {
        r = v;
        b = v;
        g = v;
      } else {
        r = scale_8(r - v, saturation) + v;
        g = scale_8(g - v, saturation) + v;
        b = scale_8(b - v, saturation) + v;
      }
    }
  }

  r = ((uint32_t)r * (uint32_t)brightness * (uint32_t)corr_r) >> 16;
  g = ((uint32_t)g * (uint32_t)brightness * (uint32_t)corr_g) >> 16;
  b = ((uint32_t)b * (uint32_t)brightness * (uint32_t)corr_b) >> 16;
  w = scale_8(w, brightness);

  return pack_rgbw(r, g, b, w);
}

void rgb_render_calibration(uint8_t corr_r, uint8_t corr_g, uint8_t corr_b,
                            uint8_t brightness) {
  uint8_t r = scale_8(corr_r, brightness);
  uint8_t g = scale_8(corr_g, brightness);
  uint8_t b = scale_8(corr_b, brightness);
  uint32_t c = pack_rgbw(r, g, b, 0);
  for (int i = 0; i < LEDCount; i++) {
    frame_buffer[i] = c;
  }
}

void backend_handle_command() {
  if (backend_incoming_data_buffer[0] != PacketStartByte) return;
  uint8_t command_type = backend_incoming_data_buffer[1];
  if (command_type == CmdTypeCalibration) {
    rgb_render_calibration(backend_incoming_data_buffer[4],
                           backend_incoming_data_buffer[5],
                           backend_incoming_data_buffer[6],
                           backend_incoming_data_buffer[7]);
    backend_write_frame_buffer();
  } else if (command_type == CmdTypeRenderRGB ||
             command_type == CmdTypeRenderHSV) {
    uint start = backend_incoming_data_buffer[9] << 8 | backend_incoming_data_buffer[10];
    uint end = backend_incoming_data_buffer[11] << 8 | backend_incoming_data_buffer[12];
    start = MIN(start, LEDCount);
    end = MIN(end, LEDCount);
    if (start >= end) return;
    if (command_type == CmdTypeRenderRGB) {
      for (int i = start; i < end; i++) {
        uint pos = (i - start) * 3 + 13;
        frame_buffer[i] = render_rgb(backend_incoming_data_buffer[pos],
                                     backend_incoming_data_buffer[pos + 1],
                                     backend_incoming_data_buffer[pos + 2],
                                     backend_incoming_data_buffer[4],
                                     backend_incoming_data_buffer[5],
                                     backend_incoming_data_buffer[6],
                                     backend_incoming_data_buffer[7],
                                     backend_incoming_data_buffer[8]);
      }
    } else if (command_type == CmdTypeRenderHSV) {
      for (int i = start; i < end; i++) {
        uint pos = (i - start) * 3 + 13;
        frame_buffer[i] = render_hsv2rgb_rainbow(backend_incoming_data_buffer[pos],
                                                 backend_incoming_data_buffer[pos + 1],
                                                 backend_incoming_data_buffer[pos + 2],
                                                 backend_incoming_data_buffer[4],
                                                 backend_incoming_data_buffer[5],
                                                 backend_incoming_data_buffer[6],
                                                 backend_incoming_data_buffer[7],
                                                 backend_incoming_data_buffer[8]);
      }
    }
  } else if (command_type == CmdTypeWriteLEDs) {
    backend_write_frame_buffer();
  }
}

void backend_init() {
  uint offset = pio_add_program(PIOBlock, &WS2812B_program);
  has_white = StripType & 0xf0000000;
  WS2812B_program_init(PIOBlock, PIOStateMachine,
                       offset, LEDPin,
                       800000, has_white ? 32 : 24);

  shift_w = 0;
  shift_r = ((StripType >> 16) & 0xff) + (has_white ? 8 : 0);
  shift_g = ((StripType >> 8) & 0xff) + (has_white ? 8 : 0);
  shift_b = ((StripType >> 0) & 0xff) + (has_white ? 8 : 0);

  for (uint i = 0; i < LEDCount; i++) {
    frame_buffer[i] = 0x00000000;
  }

  backend_write_frame_buffer();
}
