#pragma once

#include "driver/i2c.h"
#include "esp_err.h"

#define BME280_I2C_ADDR 0x76

esp_err_t bme280_init(i2c_port_t port, gpio_num_t sda, gpio_num_t scl);
esp_err_t bme280_read(float *temperature, float *humidity);
