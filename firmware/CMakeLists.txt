add_executable(${OUTPUT_NAME})

add_compile_options(
)

add_link_options(
)

pico_generate_pio_header(${OUTPUT_NAME} ${CMAKE_CURRENT_LIST_DIR}/ws2812b.pio)

pico_enable_stdio_usb(${OUTPUT_NAME} 1)
pico_enable_stdio_uart(${OUTPUT_NAME} 0)

target_compile_definitions(${OUTPUT_NAME} PRIVATE PICO_RP2040_USB_DEVICE_ENUMERATION_FIX=1)

target_sources(${OUTPUT_NAME}
    PRIVATE main.c backend.c wifi.c
)

target_include_directories(${OUTPUT_NAME} PRIVATE ${CMAKE_CURRENT_LIST_DIR})

target_link_libraries(${OUTPUT_NAME}
    pico_stdlib
    pico_multicore
    hardware_pio
    pico_cyw43_arch_lwip_threadsafe_background
)

pico_enable_stdio_usb(${OUTPUT_NAME} 1)

pico_add_extra_outputs(${OUTPUT_NAME})
