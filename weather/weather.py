# -*- coding: utf-8 -*-

'''
使用说明：
    仅需要更改查询目标地名称
'''

import json
import urllib.request

class Weather:
    def __init__(self):
        # 初始化
        # self.url = "http://api.map.baidu.com/telematics/v3/weather?output=json&"
        self.url = "https://api.map.baidu.com/weather/v1/?output=json&&data_type=all"
        self.ak = "A5CGqctY5c0RwTfZFuktytfw"

    def get_data_from_pandas(self, city_name):
        csv_file = 'weather_district_id.csv'
        return self.get_target_use_pandas(csv_file, city_name)

    def get_target_use_pandas(self, data_file, city_name):
        import pandas as pd
        df = pd.read_csv(data_file)
        district_code = df[df['district'] == city_name]['districtcode']
        for x in district_code.values.tolist():
            district_code = x
        return district_code

    def getWeather(self, city):
        id = self.get_data_from_pandas(city)
        # url = self.url + 'location=' + str() + '&ak=' + self.ak
        url = self.url + '&district_id=' + str(id) + '&ak=' + self.ak
        response = urllib.request.urlopen(url).read()
        result = response.decode('utf-8')
        result = json.loads(result)
        content = result.get('result')
        location = content.get('location')
        print(location)
        now = content.get('now')
        # -------------
        print(now)
        # -------------
        # date
        date = now.get('uptime')[0:-2]
        print("日 期："+date)
        # city
        province_name = location.get('province')
        city = location.get('city')
        city_name = location.get('name')
        print("城 市： "+city_name)

        forecasts = content.get('forecasts')
        for weather_index in range(len(forecasts)):
            print(forecasts[weather_index])


        #
        # # pm25
        # pm25 = result.get('pm25')
        # print("PM2.5： "+pm25)
        #
        # # advice
        # tips = []
        # advice = result.get('index')
        # for i in range(0, len(advice)-1):
        #     # 意见
        #     suggestion = advice[i].get('des')
        #     tips.append(suggestion)
        #
        # # weather detail
        # detail = []
        # weather = result.get('weather_data')
        # for i in range(0, len(weather)-1):
        #     detail.append(weather[i].get('date') + " | " + weather[i].get('weather') +
        #                   " | " + weather[i].get('wind') + " | " + weather[i].get('temperature'))
        #
        # print("详 情： "+str(detail))
        # print("贴 士： "+str(tips))


if __name__ == '__main__':
    # 根据需要更改
    city = "苏州"
    w = Weather()
    w.getWeather(city=city)