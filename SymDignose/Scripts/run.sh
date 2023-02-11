python3 SEmu-helper.py RaceTest/STM32G474_LL_USART_Race.elf RaceTest/STM32G474_uart_race.cfg --nlp=RaceTest/g474.txt --signal=RaceTest/uart_signal.txt --cc=RaceTest/uart_cc.txt --debug
./launch-SEmu.sh debug
mv s2e-out-0/ Statistics/unit-tests/save-k64-uart/

python3 SEmu-helper.py RaceTest/STM32F429I-HAL-SPI-EFlags.elf RaceTest/STM32G474_spi_race.cfg --nlp=RaceTest/f429.txt --signal=RaceTest/spi_signal.txt --cc=RaceTest/spi_cc.txt --debug
./launch-SEmu.sh debug
mv s2e-out-0/ Statistics/unit-tests/save-k64-spi/


python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-USART.elf MK64F-unit_tests/K64F_UART.cfg --nlp=MK64F-unit_tests/k64.txt --signal=MK64F-unit_tests/uart_signal.txt --cc=MK64F-unit_tests/uart_cc.txt --debug
./launch-SEmu.sh debug
mv s2e-out-0/ Statistics/unit-tests/save-k64-uart/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-SPI.elf MK64F-unit_tests/K64F_SPI.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-spi/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-I2C.elf MK64F-unit_tests/K64F_i2c.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-i2c/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-GPIO_INT.elf MK64F-unit_tests/K64F_gpioint.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-gint/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-GPIO.elf MK64F-unit_tests/K64F_gpio.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-gpio/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-ADC.elf MK64F-unit_tests/K64F_adc.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-adc/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-PWM.elf MK64F-unit_tests/K64F_pwm.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-pwm/

python3 SEmu-helper.py MK64F-unit_tests/K64F-RIOT-TIMER.elf  MK64F-unit_tests/K64F_timer.cfg --nlp=MK64F-unit_tests/k64.txt
./launch-SEmu.sh debug 
mv s2e-out-0/ Statistics/unit-tests/save-k64-timer/
