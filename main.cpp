// #include "stdio.h" // for printf
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "midi_data.h"

/*
    In case of build issues after copying the template, delete the entire build directory and in VSCode:
    Restart VSCode, click on "Terminal" on the top bar, and select GCC 10.2.1 arm-none-eabi

    Overclocking: https://youtu.be/G2BuoFNLoDM (The "catch" is already fixed in CMakeLists.txt, uncomment the three lines at the bottom)
    PIO: https://youtu.be/JSis2NU65w8
    Explaining PIO ASM instructions: https://youtu.be/yYnQYF_Xa8g

    - Max X, 2022-01-07
*/

uint pwm_slice_num;

struct repeating_timer timer;

void setUpPWM() {
    gpio_set_function(17, GPIO_FUNC_PWM);
    pwm_slice_num = pwm_gpio_to_slice_num(17);
    pwm_set_wrap(pwm_slice_num, 1023);
    pwm_set_chan_level(pwm_slice_num, PWM_CHAN_B, 0);
    pwm_set_enabled(pwm_slice_num, true);
}

void changePWM(uint8_t dutyCycle) {
    pwm_set_chan_level(pwm_slice_num, PWM_CHAN_B, 4 * dutyCycle);
}
bool testf = 1;

uint16_t sample_index = 0;
uint16_t midi_index = 0;
bool note_states[128];

bool timer_isr(struct repeating_timer *t) {
    gpio_put(16, testf);
    testf = 1 - testf;

    uint32_t midi_data = midi_array[midi_index];
    
    /*
        MIDI text format:
        MSB = note on/off
        7 bits to the left of that = the MIDI note affected
        the rest of the bits = absolute time in milliseconds of the event

        bool action = value & (uint32_t 1 << 31);

    */

    uint32_t millis = to_ms_since_boot(get_absolute_time());
    uint32_t midi_time = midi_data & 0x00FFFFFF;
    uint32_t intermediate0 = midi_data & 0b01111111000000000000000000000000;
    uint8_t note = (uint8_t) (intermediate0 >> 24);
    
    if (millis >= midi_time) {
        if (midi_data & ((uint32_t) 1 << 31)) {
            note_states[note] = true;
        }
        else {
            note_states[note] = false;
        }
        midi_index++;
    }

    uint8_t pwm_output_value = 0;

    int32_t average_table_val = 0;

    uint8_t number_of_notes = 0;
    for (uint16_t i = 0; i < 128; i++) {
        if (note_states[i]) {
            average_table_val += wave_table[i][sample_index];
            number_of_notes++;
        }
    }

    average_table_val = (average_table_val - 128) / (number_of_notes + 1);
    average_table_val /= 2.0f;
    average_table_val += 128;

    sample_index++;
    if (sample_index >= wave_table_length) {
        sample_index = 0;
    }

    changePWM(average_table_val);
    return true;
}

void setUpTimer(int64_t delay_us) {
    add_repeating_timer_us(-50, timer_isr, NULL, &timer);
    timer.delay_us = delay_us;
}

int main() {
    
    // stdio_init_all(); // for printf

    gpio_init(25);
    gpio_set_dir(25, GPIO_OUT);

    gpio_init(16);
    gpio_set_dir(16, GPIO_OUT);

    setUpPWM();

    setUpTimer(-40);

    while(1) {
        gpio_put(25, 1);
        sleep_ms(200);
        gpio_put(25, 0);
        sleep_ms(200);
    }
}