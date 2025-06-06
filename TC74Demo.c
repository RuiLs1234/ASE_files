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

// Valores iniciais padrão (iguais ao servidor)
static float tmax = 30.0;
static float tmin = 15.0;
static float hmax = 80.0;
static float hmin = 30.0;

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

    ESP_LOGI("wifi", "A ligar ao Wi-Fi...");
    xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI("wifi", "Ligado ao Wi-Fi!");
}

int connect_to_server() {
    struct sockaddr_in server_addr = {
        .sin_family = AF_INET,
        .sin_port = htons(SERVER_PORT),
        .sin_addr.s_addr = inet_addr(SERVER_IP),
    };

    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE("socket", "Erro ao criar socket");
        return -1;
    }

    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) != 0) {
        ESP_LOGW("socket", "Erro ao ligar ao servidor");
        close(sock);
        return -1;
    }

    ESP_LOGI("socket", "Ligado ao servidor");
    return sock;
}

bool verificar_alerta(float temp, float hum) {
    return (temp > tmax || temp < tmin || hum > hmax || hum < hmin);
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

    char recv_buf[64];

    while (1) {
        float temp, hum;
        if (bme280_read(&temp, &hum) == ESP_OK) {
            char msg[64];

            if (verificar_alerta(temp, hum)) {
                snprintf(msg, sizeof(msg), "ALERTA;%.2f;%.2f", temp, hum);
            } else {
                snprintf(msg, sizeof(msg), "%.2f;%.2f", temp, hum);
            }

            send(sock, msg, strlen(msg), 0);
            ESP_LOGI("DATA", "Enviado: %s", msg);

            // Recebe resposta do servidor
            int len = recv(sock, recv_buf, sizeof(recv_buf) - 1, 0);
            if (len > 0) {
                recv_buf[len] = '\0';
                ESP_LOGI("DATA", "Resposta do servidor: %s", recv_buf);

                // Parse da resposta: "tmax;tmin;hmax;hmin"
                float new_tmax, new_tmin, new_hmax, new_hmin;
                if (sscanf(recv_buf, "%f;%f;%f;%f", &new_tmax, &new_tmin, &new_hmax, &new_hmin) == 4) {
                    tmax = new_tmax;
                    tmin = new_tmin;
                    hmax = new_hmax;
                    hmin = new_hmin;
                    ESP_LOGI("DATA", "Limites atualizados: tmax=%.2f, tmin=%.2f, hmax=%.2f, hmin=%.2f", tmax, tmin, hmax, hmin);
                } else {
                    ESP_LOGW("DATA", "Resposta do servidor com formato inválido");
                }
            } else {
                ESP_LOGW("socket", "Falha ao receber resposta do servidor");
            }
        } else {
            ESP_LOGW("sensor", "Erro ao ler do BME280");
        }

        vTaskDelay(pdMS_TO_TICKS(5000)); // envia a cada 5 segundos
    }
}
