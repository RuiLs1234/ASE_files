#include "bme280.h"
#include "freertos/task.h"
#include "esp_random.h"  // <- Adicionado aqui

static i2c_port_t i2c_port;

esp_err_t bme280_init(i2c_port_t port, gpio_num_t sda, gpio_num_t scl) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = sda,
        .scl_io_num = scl,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 100000,
    };
    i2c_port = port;
    ESP_ERROR_CHECK(i2c_param_config(port, &conf));
    return i2c_driver_install(port, conf.mode, 0, 0, 0);
}

// Simulação de leitura (para testes)
esp_err_t bme280_read(float *temperature, float *humidity) {
    *temperature = 22.5 + (esp_random() % 100) / 10.0;
    *humidity = 55.0 + (esp_random() % 100) / 10.0;
    return ESP_OK;
}
