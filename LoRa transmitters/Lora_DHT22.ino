#include <SPI.h>
#include <SimpleDHT.h>
#include <LoRa.h>
#include "board_def.h"
#include <Wire.h>
#include <MQ135.h>

//Edited code from https://github.com/cubapp/LilyGO-TTGO-LoRa32-SenderReceiver/tree/master
//Added the DHT22 part from the DHT22 library examples

// for DHT22, 
//      VCC: 5V or 3V
//      GND: GND
//      DATA: 2

/* return absolute humidity [mg/m^3] with approximation formula
* @param Temperature [°C]
* @param Relative Humidity [%RH]
* 
*/


int pinDHT22 = 12;
int pinMQ135 = 13;
SimpleDHT22 dht22(pinDHT22);
//MQ135 mq135_sensor(pinMQ135);

OLED_CLASS_OBJ display(OLED_ADDRESS, OLED_SDA, OLED_SCL);

//display size for better string placement
int width;
int height;

void setup()
{
  Serial.begin(115200);
  while (!Serial);

  if (OLED_RST > 0) {
    pinMode(OLED_RST, OUTPUT);
    digitalWrite(OLED_RST, HIGH);
    delay(100);
    digitalWrite(OLED_RST, LOW);
    delay(100);
    digitalWrite(OLED_RST, HIGH);
  }

  display.init();
  width = display.getWidth() / 2;
  height = display.getHeight() / 2;
  display.flipScreenVertically();
  display.clear();
  display.setFont(ArialMT_Plain_10);
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.drawString(width - 50, height, LORA_SENDER ? "LoRa+++ Sender" : "LoRa++ Receiver");
  display.display();
  delay(2000);

  SPI.begin(CONFIG_CLK, CONFIG_MISO, CONFIG_MOSI, CONFIG_NSS);
  LoRa.setPins(CONFIG_NSS, CONFIG_RST, CONFIG_DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  
  // Setting LoRa parameters
  LoRa.setTxPower(20);  // Set transmitter power; max 20dB
  LoRa.setSpreadingFactor(10);  // Set SF, 6-12 (use 12 for max range)
  LoRa.setSignalBandwidth(41.7e3); // Supported values are 7.8E3, 10.4E3, 15.6E3, 20.8E3, 31.25E3, 41.7E3, 62.5E3, 125E3=default, and 250E3
  LoRa.setPreambleLength(10); // Preamble length for SDRangel is 4 - 20
  LoRa.setCodingRate4(4); // Set the coding rate (1-4)
  LoRa.enableCrc(); // Adds CRC

  if (!LORA_SENDER) {
    display.clear();
    display.drawString(width - 50, height, String(LORA_SENDER));
    display.display();
  }
  else {
    display.clear();
    display.drawString(width - 50, height, "LoRa Transmitter");
    display.display();

    delay(1000);
  }
}

int count = 0;
void loop()
{

  // read without samples.
  // @remark We use read2 to get a float data, such as 10.1*C
  //    if user doesn't care about the accurate data, use read to get a byte data, such as 10*C.
  float temperature = 0;
  float humidity = 0;
  float ppm = 0;
  int err = SimpleDHTErrSuccess;

  // Initiate reading samples from DHT22, min. sampling rate is 2 seconds.
  // If no data is read, print error

  if ((err = dht22.read2(&temperature, &humidity, NULL)) != SimpleDHTErrSuccess) {
    Serial.print("Read DHT22 failed, err="); Serial.print(SimpleDHTErrCode(err));
    Serial.print(","); Serial.println(SimpleDHTErrDuration(err)); delay(2000);
    return;
  }
/*
  float rzero = mq135_sensor.getRZero();
  float correctedRZero = mq135_sensor.getCorrectedRZero(temperature, humidity);
  float resistance = mq135_sensor.getResistance();
  float ppm = mq135_sensor.getPPM();
  float correctedPPM = mq135_sensor.getCorrectedPPM(temperature, humidity);
 */ 
  // Print out in serial monitor the received temp and RH values
  ppm = analogRead(pinMQ135);
  
  Serial.print("Sample OK: ");
  Serial.print((float)temperature); Serial.print(" *C\t");
  Serial.print((float)humidity); Serial.print(" RH%\t");
  Serial.print((float)ppm); Serial.println(" ppm");
  

#if LORA_SENDER
  count++;
  display.clear();
  display.setTextAlignment(TEXT_ALIGN_LEFT);
  display.drawString(width - 60, height - 20, "Temp: " + String(temperature) + " " + "Hum: " + String(humidity));
  display.drawString(width - 60, height, "AQ: " + String(ppm));
  display.display();

//Each weather data is transmitted 2 times before proceeding to the next
//This is to give us a higher chance of getting the correct value
  Serial.println("Sending via LoRa at 433 MHz...");
/*
  for (int i = 0; i <= 1; i++) {
    LoRa.beginPacket();
    LoRa.print("433 MHz");
    LoRa.endPacket();
  }

  Serial.println("Temperature");

  for (int i = 0; i <= 1; i++) {
    // serial display
    
    Serial.print(String(i+1)+"...");

    //send LoRa packet
    LoRa.beginPacket();
    LoRa.print("Temp=" );
    LoRa.print(temperature);
    LoRa.endPacket();

    Serial.println("OK");

    // display on OLED screen
    display.clear();
    display.setTextAlignment(TEXT_ALIGN_LEFT);
    display.drawString(width - 60, height - 20, "Sending temp packet...");
    display.drawString(width - 60, height + 20, "Temp=" + String(temperature));
    display.display();

    delay(1500);
  }

  Serial.println("All temperature packets have been sent out!");
  Serial.println("Humidity");

  for (int i = 0; i <= 1; i++) {
    Serial.print(String(i+1)+"...");

    //send LoRa packet
    LoRa.beginPacket();
    LoRa.print("RH=");
    LoRa.print(humidity);
    LoRa.endPacket();

    Serial.println("OK");

    // display on OLED screen
    display.clear();
    display.setTextAlignment(TEXT_ALIGN_LEFT);
    display.drawString(width - 60, height - 20, "Sending RH packet...");
    display.drawString(width - 60, height + 20, "RH=" + String(humidity));
    display.display();

    delay(1500);
  }

  Serial.println("All RH packets have been sent out!");
  Serial.println("Air Quality");

  for (int i = 0; i <= 1; i++) {
    Serial.print(String(i+1)+"...");

    //send LoRa packet
    LoRa.beginPacket();
    LoRa.print("AQ=");
    LoRa.print(ppm);
    LoRa.endPacket();

    Serial.println("OK");

    // display on OLED screen
    display.clear();
    display.setTextAlignment(TEXT_ALIGN_LEFT);
    display.drawString(width - 60, height - 20, "Sending Gas packet...");
    display.drawString(width - 60, height + 20, "Gas=" + String(ppm));
    display.display();

    delay(1500);
  }

  Serial.println("All Gas packets have been sent out!");

  Serial.println("Temperature");

  for (int i = 0; i <= 1; i++) {
    Serial.print(String(i+1)+"...");
    
    LoRa.beginPacket();
    LoRa.print("ID=");
    LoRa.print(433);
    LoRa.print(" Temp=");
    LoRa.print(temperature);

    LoRa.endPacket();

    Serial.println("OK");

    delay(1500);
  }

  Serial.println("Humidity");

  for (int i = 0; i <= 1; i++) {
    Serial.print(String(i+1)+"...");

    LoRa.beginPacket();

    LoRa.print("ID=");
    LoRa.print(433);
    LoRa.print(" RH=");
    LoRa.print(humidity);

    LoRa.endPacket();

    Serial.println("OK");

    delay(1500);
  }

  Serial.println("Air Quality");

  for (int i = 0; i <= 1; i++) {
    Serial.print(String(i+1)+"...");
    
    LoRa.beginPacket();

    LoRa.print("ID=");
    LoRa.print(433);
    LoRa.print(" AQ=");
    LoRa.print(ppm);

    LoRa.endPacket();

    Serial.println("OK");

    delay(1500);
  }
*/
  Serial.println("All Packets");
  
  LoRa.beginPacket();

  LoRa.print("ID=");
  LoRa.print(433);
  LoRa.print(" Temp=");
  LoRa.print(temperature);
  LoRa.print(" RH=");
  LoRa.print(humidity);
  LoRa.print(" AQ=");
  LoRa.print(ppm);

  LoRa.endPacket();

  Serial.println("OK");  

  delay(5000);

#else

#endif
}
