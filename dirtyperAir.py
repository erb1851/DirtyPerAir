import smbus2
from smbus2 import SMBus , i2c_msg
import time
import datadog_api_client
from datetime import datetime
from datadog_api_client.v1 import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.model.metrics_payload import MetricsPayload
from datadog_api_client.v1.model.point import Point
from datadog_api_client.v1.model.series import Series

HM3301_DEFAULT_I2C_ADDR = 0x40
SELECT_I2C_ADDR = 0x88
DATA_CNT = 29

class Seeed_HM3301(object):
    def __init__(self,bus_nr = 1):

        self.PM_1_0_conctrt_std = 0         # PM1.0 Standard particulate matter concentration Unit:ug/m3
        self.PM_2_5_conctrt_std = 0         # PM2.5 Standard particulate matter concentration Unit:ug/m3
        self.PM_10_conctrt_std = 0          # PM10  Standard particulate matter concentration Unit:ug/m3

        with SMBus(bus_nr) as bus:
            write = i2c_msg.write(HM3301_DEFAULT_I2C_ADDR,[SELECT_I2C_ADDR])
            bus.i2c_rdwr(write)

    def read_data(self):
        with SMBus(1) as bus:
            read = i2c_msg.read(HM3301_DEFAULT_I2C_ADDR,DATA_CNT)
            bus.i2c_rdwr(read)
            return list(read)

    def check_crc(self,data):
        sum = 0
        for i in range(DATA_CNT-1):
            sum += data[i]
        sum = sum & 0xff
        #print(sum)
        #print(data[28])
        return (sum==data[28])

    def parse_data(self,data):
        self.PM_1_0_conctrt_std = data[4]<<8 | data[5]
        self.PM_2_5_conctrt_std = data[6]<<8 | data[7]
        self.PM_10_conctrt_std = data[8]<<8 | data[9]
        averagePM_conctrt = ( self.PM_1_0_conctrt_std +self.PM_2_5_conctrt_std + self.PM_10_conctrt_std)/3
        sendDataDog(averagePM_conctrt, "AverageDirtyPerAir", "env:diritesPerAir")
        sendDataDog(self.PM_10_conctrt_std, "PM10DirtyPerAir", "env:diritesPerAir")
        sendDataDog(self.PM_1_0_conctrt_std, "PM1DirtyPerAir", "env:diritesPerAir")
        sendDataDog(self.PM_2_5_conctrt_std, "PM25DirtyPerAir", "env:diritesPerAir")

        
def sendDataDog(data, name, tag):
    body = MetricsPayload(
    series=[
        Series(
            metric=name,
            type="gauge",
            points=[Point([datetime.now().timestamp(), data])],
            tags=[tag],
        )
    ]
)
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = MetricsApi(api_client)
        response = api_instance.submit_metrics(body=body)
        #print(response)


def main():
   # print("################### NOTICE!!!! ############################")
   ## print("####### sudo vim /boot/config.txt                      ####")
   # print("####### add content : dtparam=i2c_arm_baudrate=20000   ####")
   # print("####### sudo reboot                                    ####")
   # print("################### NOTICE!!!! ############################")
    hm3301 = Seeed_HM3301()
    time.sleep(.1)
  #  while 1:
    data = hm3301.read_data()
    if(hm3301.check_crc(data) != True):
        print("CRC error!")
    hm3301.parse_data(data)
        #time.sleep(30)


if __name__ == '__main__':
    main()