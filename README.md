# smartmeter_checker
smartmeter electricity usage checker with EchonetLite

## Usage

```
ROUTEB_ID="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ROUTEB_PW="YYYYYYYYYYYY"
SERIALPORT=/dev/ttyUSB0
BAUDRATE=115200

python3 test.py ${ROUTEB_ID} ${ROUTEB_PW} --serialport ${SERIALPORT} --baudrate ${BAUDRATE}
```
