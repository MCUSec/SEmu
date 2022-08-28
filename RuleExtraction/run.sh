
python extract.py k64 UART 1 &
python extract.py k64 SPI 1 &
python extract.py k64 GPIO 1 &
python extract.py k64 I2C 1 &
python extract.py k64 ADC 1 &
python extract.py k64 RTC 1 &
python extract.py k64 SIM 1 &
python extract.py k64 PORT 1 &
python extract.py k64 WDOG 1 &
python extract.py k64 MCG 1 &
python extract.py k64 SMC 1 &
python extract.py k64 PWM 1 &
python extract.py k64 PIT 1 &
wait
cat Manuals/k64/data/*memory.txt > extractedRules/k64.txt
echo "==" >> extractedRules/k64.txt
cat Manuals/k64/data/*tas.txt >> extractedRules/k64.txt
echo "==" >> extractedRules/k64.txt
cat Manuals/k64/data/*flag.txt >> extractedRules/k64.txt
echo "==" >> extractedRules/k64.txt
