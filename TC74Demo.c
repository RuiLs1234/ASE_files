#include <stdio.h>
#include <string.h>
#include "esp_err.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "lwip/sockets.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"  // Include the logging library

#define WIFI_SSID      "Unternet"
#define WIFI_PASS      "rudk0785"

#define SERVER_IP      "192.168.242.147"
#define SERVER_PORT    12346

#define TC74_SDA_IO    3
#define TC74_SCL_IO    2

#define TEMP_MIN       0
#define TEMP_MAX       32

#define LED_OUTPUT_IO  1
#define DUTY_CYCLE_RES LEDC_TIMER_10_BIT

#define LEDC_MODE      LEDC_LOW_SPEED_MODE
#define LEDC_TIMER     LEDC_TIMER_0
#define LEDC_CHANNEL   LEDC_CHANNEL_0

// WiFi Event Group
static EventGroupHandle_t wifi_event_group;
const int CONNECTED_BIT = BIT0;

// Wi-Fi Initialization
void wifi_init_sta(void) {
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };

    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_connect();
}

// Event Handler for WiFi connection
static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        char ip[16];
        esp_ip4addr_ntoa(&event->ip_info.ip, ip, sizeof(ip));
        ESP_LOGI("WiFi", "Got IP: %s", ip);  // Now this works since ESP_LOGI is defined
        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
    }
}

// Function to initialize Wi-Fi and wait for connection
void wait_for_wifi_connection() {
    // Create event group for Wi-Fi status
    wifi_event_group = xEventGroupCreate();

    // Register event handler
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id);
    esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip);

    // Wait for Wi-Fi to connect
    ESP_LOGI("WiFi", "Connecting to Wi-Fi...");
    xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI("WiFi", "Wi-Fi connected!");
}

// Function to connect to the server
int connect_to_server() {
    struct sockaddr_in dest_addr;
    dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(SERVER_PORT);

    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) != 0) {
        printf("Failed to connect to server. Retrying...\n");
        close(sock);
        return -1; // Connection failed
    }
    printf("Connected to server\n");
    return sock; // Successfully connected
}

// Function to send temperature data to the server
void send_temperature_data(int sock, uint8_t temperature) {
    char temp_str[32];
    snprintf(temp_str, sizeof(temp_str), "%d", temperature);
    send(sock, temp_str, strlen(temp_str), 0);
    printf("Sent temperature data: %d\n", temperature);
}

void app_main(void) {
    nvs_flash_init();

    // Initialize Wi-Fi and wait for connection
    wifi_init_sta();
    wait_for_wifi_connection();

    // Initialize I2C sensor (dummy code for initialization)
    uint8_t temperature = 25; // This is just a placeholder for the actual sensor reading code

    // Keep trying to connect to the server until successful
    int sock = -1;
    while (sock == -1) {
        sock = connect_to_server();
        vTaskDelay(2000 / portTICK_PERIOD_MS); // Delay before retrying if connection failed
    }

    // Once connected, send temperature data in a loop
    while (1) {
        send_temperature_data(sock, temperature);
        vTaskDelay(2000 / portTICK_PERIOD_MS); // Delay between sending temperature readings
    }
}
