#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"

#include "lwip/netif.h"
#include "lwip/ip4_addr.h"
#include "lwip/pbuf.h"
#include "lwip/udp.h"

#include "backend.h"
#include "wifi.h"
#include "wifi_config.h"

#define CYW43_LWIP 1

struct udp_pcb *pcb;

static void udp_receive(void *arg, struct udp_pcb *pcb, struct pbuf *p, const struct ip4_addr *addr, unsigned short port) {
  if(p == NULL) return;

  uint8_t *req_data = (uint8_t *)p->payload;
  memcpy(backend_incoming_data_buffer, req_data, MIN(p->len, BackendIncomingDataBufferSize));
  backend_handle_command();

  pbuf_free(p);
}

void wifi_init() {
  if (cyw43_arch_init()) {
    printf("cyw43_arch failed to initialize.\n");
    return;
  }

  cyw43_arch_enable_sta_mode();
  printf("Connecting to Wi-Fi...\n");
  if (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK, 30000)) {
      printf("Failed to connect.\n");
        return;
  } else {
      printf("Connected.\n");
  }

  cyw43_arch_lwip_begin();

  printf("IP address: %s\n", ip4addr_ntoa(netif_ip4_addr(netif_list)));

  pcb = udp_new();
  udp_bind(pcb, IP_ADDR_ANY, PORT);
  udp_recv(pcb, udp_receive, 0);

  cyw43_arch_lwip_end();
}

void wifi_deinit() {
  cyw43_arch_lwip_begin();
  cyw43_arch_deinit();
  cyw43_arch_lwip_end();
}
