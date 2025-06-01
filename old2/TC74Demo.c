#include <stdio.h>
#include <string.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_event.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lwip/sockets.h"
#include "bme280.h"

#define WIFI_SSID "Unternet"
#define WIFI_PASS "rudk0785"
#define SERVER_IP "192.168.242.147"
#define SERVER_PORT 12346

#define I2C_SDA GPIO_NUM_3
#define I2C_SCL GPIO_NUM_2

static EventGroupHandle_t wifi_event_group;
const int CONNECTED_BIT = BIT0;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
    }
}

void wifi_init() {
    wifi_event_group = xEventGroupCreate();
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL);

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };

    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();

    ESP_LOGI("wifi", "Waiting for connection...");
    xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI("wifi", "Connected!");
}

int connect_to_server() {
    struct sockaddr_in server_addr = {
        .sin_family = AF_INET,
        .sin_port = htons(SERVER_PORT),
        .sin_addr.s_addr = inet_addr(SERVER_IP),
    };

    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) != 0) {
        close(sock);
        return -1;
    }
    return sock;
}

void app_main() {
    nvs_flash_init();
    wifi_init();
    bme280_init(I2C_NUM_0, I2C_SDA, I2C_SCL);

    int sock = -1;
    while (sock == -1) {
        sock = connect_to_server();
        vTaskDelay(pdMS_TO_TICKS(2000));
    }

    while (1) {
        float temp, hum;
        if (bme280_read(&temp, &hum) == ESP_OK) {
            char msg[64];
            snprintf(msg, sizeof(msg), "%.2f;%.2f", temp, hum);
            send(sock, msg, strlen(msg), 0);
            ESP_LOGI("DATA", "Sent: %s", msg);
        }
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
