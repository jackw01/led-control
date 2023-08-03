#include <stdio.h>
#include <math.h>

#include "pico/stdlib.h"
#include "hardware/pio.h"

#include "backend.h"
#include "wifi.h"

// UART

uint uart_packet_index = 0;
uint uart_packet_length;

void handle_uart_input(char c) {
  backend_incoming_data_buffer[uart_packet_index] = c;
  if (uart_packet_index == 0 && c == PacketStartByte) {
    // Packet start
    uart_packet_index++;
    uart_packet_length = 0;
  } else if (uart_packet_index == 1) {
    // Packet type
    if (c < CmdTypeMax) {
      uart_packet_index++;
    } else uart_packet_index = 0;
  } else if (uart_packet_index == 2) {
    // Size byte 1
    uart_packet_length = c << 8;
    uart_packet_index++;
  } else if (uart_packet_index == 3) {
    // Size byte 2
    uart_packet_length |= c;
    uart_packet_index++;
  } else if (uart_packet_index >= 4) {
    // Data start
    uart_packet_index++;
    if (uart_packet_index == uart_packet_length ||
        uart_packet_index == BackendIncomingDataBufferSize + 2) {
      backend_handle_command();
      uart_packet_index = 0;
    }
  } else {
    // End
    uart_packet_index = 0;
  }
}

// Main loop

int main() {
  //set_sys_clock_khz(200000, true);

  stdio_init_all();

  backend_init();
  wifi_init();

  while (true) {
    int32_t c = getchar_timeout_us(0);
    if (c != PICO_ERROR_TIMEOUT) handle_uart_input(c);
  }
}
