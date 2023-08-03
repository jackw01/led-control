#pragma once

#include "config.h"

enum CmdType {
    CmdTypeCalibration = 0,
    CmdTypeRenderRGB,
    CmdTypeRenderHSV,
    CmdTypeWriteLEDs,
    CmdTypeMax
};

#define PacketStartByte 0

#define BackendIncomingDataBufferSize (LEDCount * 3 + 64)
extern uint8_t backend_incoming_data_buffer[BackendIncomingDataBufferSize];

void backend_write_frame_buffer();
void backend_handle_command();
void backend_init();
