import requests
import math


class WeatherApi:
    def __init__(self, token, city):
        self.token = token
        self.city = city
        self.temp = None
        self.description = None
        self.pressure = None
        self.humidity = None
        self.wind = None
        self.feels = None

    def get(self):
        params = {
            'q': self.city,
            'appid': self.token,
            'lang': 'ru',
            'units': 'metric'
        }
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params)
        if response.status_code == 200:
            self.temp = math.floor(response.json()['main']['temp'])
            self.feels = math.floor(response.json()['main']['feels_like'])
            self.description = response.json()['weather'][0]['description']
            self.pressure = math.floor(response.json()['main']['pressure']/1.333)
            self.humidity = response.json()['main']['humidity']
            if response.json()['wind']['deg'] == 0 or response.json()['wind']['deg'] == 360:
                wind_deg = '⬇️'
            elif response.json()['wind']['deg'] == 90:
                wind_deg = '⬅️'
            elif response.json()['wind']['deg'] == 180:
                wind_deg = '⬆️'
            elif response.json()['wind']['deg'] == 270:
                wind_deg = '➡️'
            elif 0 < response.json()['wind']['deg'] < 90:
                wind_deg = '↙️'
            elif 90 < response.json()['wind']['deg'] < 180:
                wind_deg = '↖️'
            elif 180 < response.json()['wind']['deg'] < 270:
                wind_deg = '↗️'
            elif 270 < response.json()['wind']['deg'] < 360:
                wind_deg = '↘️'
            self.wind = [math.ceil(response.json()['wind']['speed']), wind_deg]
            return response.status_code
        else:
            return response.status_code



