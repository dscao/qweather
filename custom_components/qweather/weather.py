"""

"""
import logging, os
from datetime import datetime, timedelta

import asyncio
import async_timeout
import aiohttp

import voluptuous as vol

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    WeatherEntity,
    ATTR_FORECAST_TIME,    
    ATTR_CONDITION_CLOUDY,
    ATTR_WEATHER_HUMIDITY,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_PRESSURE,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_WIND_SPEED,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_DEFAULT,
    LENGTH_INCHES,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    LENGTH_MILLIMETERS,
    PRESSURE_HPA,
    PRESSURE_INHG,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_ATTRIBUTION, 
)
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

from .const import VERSION, ROOT_PATH
from .condition import CONDITION_MAP, EXCEPTIONAL

_LOGGER = logging.getLogger(__name__)

TIME_BETWEEN_UPDATES = timedelta(seconds=900)

DEFAULT_TIME = dt_util.now()

CONF_CITY = "city"
CONF_APPKEY = "appkey"

ATTR_CONDITION_CN = "condition_cn"
ATTR_UPDATE_TIME = "update_time"
ATTR_AQI = "aqi"
ATTR_HOURLY_FORECAST = "hourly_forecast"
ATTR_SUGGESTION = "suggestion"
ATTR_CUSTOM_UI_MORE_INFO = "custom_ui_more_info"
CONDITION_CLASSES = {
    'sunny': ["晴"],
    'cloudy': ["多云"],
    'partlycloudy': ["少云", "晴间多云", "阴"],
    'windy': ["有风", "微风", "和风", "清风"],
    'windy-variant': ["强风", "疾风", "大风", "烈风"],
    'hurricane': ["飓风", "龙卷风", "热带风暴", "狂暴风", "风暴"],
    'rainy': ["雨", "毛毛雨", "小雨", "中雨", "大雨", "阵雨", "极端降雨"],
    'pouring': ["暴雨", "大暴雨", "特大暴雨", "强阵雨"],
    'lightning-rainy': ["雷阵雨", "强雷阵雨"],
    'fog': ["雾", "薄雾"],
    'hail': ["雷阵雨伴有冰雹"],
    'snowy': ["雪", "小雪", "中雪", "大雪", "暴雪", "阵雪"],
    'snowy-rainy': ["雨夹雪", "雨雪天气", "阵雨夹雪"],
}
TRANSLATE_SUGGESTION = {
    'air': '空气污染扩散条件指数',
    'drsg': '穿衣指数',
    'uv': '紫外线指数',
    'comf': '舒适度指数',
    'flu': '感冒指数',
    'sport': '运动指数',
    'trav': '旅游指数',
    'cw': '洗车指数',
}
SUGGESTIONTPYE2NAME = {
    '1': 'sport',
    '2': 'cw',
    '3': 'drsg',
    '4': '钓鱼指数',
    '5': 'uv',
    '6': 'trav',
    '7': '过敏指数',
    '8': 'comf',
    '9': 'flu',
    '10': 'air',
    '11': '空调开启指数',
    '12': '太阳镜指数',
    '13': '化妆指数',
    '14': '晾晒指数',
    '15': '交通指数',
    '16': '防晒指数',
}

ATTRIBUTION = "来自和风天气的天气数据"

ATTR_FORECAST_PROBABLE_PRECIPITATION = 'probable_precipitation'

# 集成安装
async def async_setup_entry(hass, config_entry, async_add_entities):
    hass.http.register_static_path(ROOT_PATH, hass.config.path('custom_components/qweather/local'), False)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-card.js?ver=' + VERSION)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-more-info.js?ver=' + VERSION)

    _LOGGER.info("setup platform weather.Heweather...")
    config = config_entry.data
    name = config.get(CONF_NAME)
    location = config.get(CONF_CITY)
    appkey = config.get(CONF_APPKEY)

    data = WeatherData(hass, location, appkey, name)

    await data.async_update() #(dt_util.now())
    async_track_time_interval(hass, data.async_update, TIME_BETWEEN_UPDATES)

    async_add_entities([HeFengWeather(data, name)], True)

class HeFengWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, data, object_id):
        """Initialize the  weather."""
        self._name = None
        self._object_id = object_id
        self._city = None
        self._condition = None
        self._icon = None
        self._native_temperature = None
        self._humidity = None
        self._native_pressure = None
        self._native_wind_speed = None
        self._wind_bearing = None
        self._forecast = None
        self._data = data
        self._updatetime = None
        self._aqi = None
        self._attr_native_precipitation_unit = LENGTH_MILLIMETERS
        self._attr_native_pressure_unit = PRESSURE_HPA
        self._attr_native_temperature_unit = TEMP_CELSIUS
        self._attr_native_visibility_unit = LENGTH_KILOMETERS
        self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._object_id
        
    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        #_LOGGER.debug("weather_unique_id: %s", self._object_id)
        return f'qweather_${self._object_id}'
        
    @property
    def device_info(self):
        """Return the device info."""
        info = {
            "identifiers": {("qweather", self._object_id)},
            "name": self._name,
            "manufacturer": "和风天气",
        }        
        from homeassistant.helpers.device_registry import DeviceEntryType
        info["entry_type"] = DeviceEntryType.SERVICE        
        return info

    @property
    def registry_name(self):
        """返回实体的friendly_name属性."""
        return '{} {}'.format('和风天气', self._name)

    @property
    def should_poll(self):
        """attention No polling needed for a demo weather condition."""
        return True

    @property
    def native_temperature(self):
        """Return the temperature."""
        return self._native_temperature


    @property
    def humidity(self):
        """Return the humidity."""
        return self._humidity

    @property
    def wind_bearing(self):
        """Return the wind speed."""
        return self._wind_bearing

    @property
    def native_wind_speed(self):
        """Return the wind speed."""
        return self._native_wind_speed

    @property
    def native_pressure(self):
        """Return the pressure."""
        return self._native_pressure

    @property
    def condition(self):
        """Return the weather condition."""
        return self._condition

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by Qweather & Home Assistant'

    @property
    def state_attributes(self):
        attributes = super().state_attributes
        """设置其它一些属性值."""
        if self._condition is not None:
            attributes.update({
                "city": self._city,
                "qweather_icon": self._icon,
                ATTR_UPDATE_TIME: self._updatetime,
                ATTR_CONDITION_CN: self._condition_cn,
                ATTR_AQI: self._aqi,
                ATTR_HOURLY_FORECAST: self.hourly_forecast,
                ATTR_SUGGESTION: self._suggestion,
                ATTR_CUSTOM_UI_MORE_INFO: "qweather-more-info"
            })
        return attributes

    @property
    def forecast(self):
        """Return the forecast."""
        if self._daily_forecast is None:
            return None
        reftime = datetime.now()
        forecast_data = self._daily_forecast
        _LOGGER.debug('forecast_data: %s', forecast_data)
        return forecast_data

    @property
    def hourly_forecast(self):
        """Return the forecast."""
        return self._hourly_forecast

    async def async_update(self):
        """update函数变成了async_update."""
        self._updatetime = self._data._updatetime
        self._condition = self._data._condition
        self._condition_cn = self._data._condition_cn
        self._native_temperature = self._data._native_temperature
        self._humidity = self._data._humidity
        self._native_pressure = self._data._native_pressure
        self._native_wind_speed = self._data._native_wind_speed
        self._wind_bearing = self._data._wind_bearing
        self._daily_forecast = self._data._daily_forecast
        self._hourly_forecast = self._data._hourly_forecast
        self._aqi = self._data._aqi
        self._suggestion = self._data._suggestion
        self._city = self._data._city
        self._icon = self._data._icon



class WeatherData(object):
    """天气相关的数据，存储在这个类中."""

    def __init__(self, hass, location, appkey, name):
        super().__init__()
        """初始化函数."""
        self._hass = hass
        self._name = name
        self._condition = None
        self._condition_cn = None
        self._icon = None
        self._native_temperature = None
        self._humidity = None
        self._native_pressure = None
        self._native_wind_speed = None
        self._wind_bearing = None
        self._forecast = None
        self._updatetime = None
        self._daily_forecast = None
        self._hourly_forecast = None
        self._minutely_forecast = None
        self._aqi = None
        self._suggestion = None
        self._weather_warning = None
        self._city = None

       
        self.api_key = appkey
        self.location = location
        self.default = 7
        self._current: dict = None
        self._daily_data: list[dict] = None
        self._indices_data: list[dict] = None
        self._hourly_data: list[dict] = None
        self._minutely_data: list[dict] = None
        self._warning_data: list[dict] = None
        self._air_data = None        
        self.geo_url = f"https://geoapi.qweather.com/v2/city/lookup?location={self.location}&key={self.api_key}"
        self.now_url = f"https://devapi.qweather.com/v7/weather/now?location={self.location}&key={self.api_key}"
        self.daily_url = f"https://devapi.qweather.com/v7/weather/{self.default}d?location={self.location}&key={self.api_key}"
        self.indices_url = f"https://devapi.qweather.com/v7/indices/1d?type=0&location={self.location}&key={self.api_key}"
        self.air_url = f"https://devapi.qweather.com/v7/air/now?location={self.location}&key={self.api_key}"
        self.hourly_url = f"https://devapi.qweather.com/v7/weather/24h?location={self.location}&key={self.api_key}"
        self.minutely_url = f"https://devapi.qweather.com/v7/minutely/5m?location={self.location}&key={self.api_key}"
        self.warning_url = f"https://devapi.qweather.com/v7/warning/now?location={self.location}&key={self.api_key}"
        self.update_time = None
        self.minutely_summary = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def condition(self):
        """Return the current condition."""
#         return self._current["text"]
        return CONDITION_MAP.get(self._current.get("icon"), EXCEPTIONAL)

    async def async_update(self):
        """获取天气数据"""
        _LOGGER.info("Update from Qweather's OpenAPI...")
        timeout = aiohttp.ClientTimeout(total=30)  # 将超时时间设置为300秒
        connector = aiohttp.TCPConnector(limit=80, force_close=True)  # 将并发数量降低
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(self.now_url) as response:                
                _LOGGER.debug(response)
                json_data = await response.json()
                _LOGGER.debug(json_data)
                self._current = json_data["now"]
                self.update_time = json_data["updateTime"]
                
            async with session.get(self.daily_url) as response:
                self._daily_data = (await response.json() or {}).get("daily")

            async with session.get(self.indices_url) as response:
                self._indices_data = (await response.json() or {}).get("daily")

            async with session.get(self.air_url) as response:
                self._air_data = (await response.json() or {}).get("now")

            async with session.get(self.hourly_url) as response:
                self._hourly_data = (await response.json() or {}).get("hourly")

            async with session.get(self.minutely_url) as response:
                minutely_data = await response.json()
                self.minutely_summary = (await response.json() or None).get("summary")
                self._minutely_data = (await response.json() or {}).get("minutely")

            async with session.get(self.warning_url) as response:
                self._warning_data = (await response.json() or {}).get("warning")
                
            if self._city == None:
                async with session.get(self.geo_url) as response:
                    self._city = (await response.json() or {}).get("location")[0]["name"]

        # 根据http返回的结果，更新数据
        
        _LOGGER.debug(self._current)
        _LOGGER.debug(self._daily_data)
        _LOGGER.debug(self._hourly_data)
        _LOGGER.debug(self._minutely_data)
        _LOGGER.debug("预警信息")
        _LOGGER.debug(self._warning_data)
        _LOGGER.debug("生活指数")
        _LOGGER.debug(self._indices_data)
        _LOGGER.debug("空气数据")
        _LOGGER.debug(self._air_data)
        
        

        self._icon = self._current.get("icon")
        self._native_temperature = float(self._current.get("temp"))
        self._humidity = int(self._current.get("humidity"))
        self._condition = CONDITION_MAP.get(self._current.get("icon"), EXCEPTIONAL)
        self._condition_cn = self._current.get("text")
        self._native_pressure = int(self._current.get("pressure"))
        self._native_wind_speed = float(self._current.get("windSpeed"))
        self._wind_bearing = float(self._current.get("wind360"))
        date_obj = datetime.fromisoformat(self.update_time.replace('Z', '+00:00'))
        formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
        self._updatetime = formatted_date
        self._aqi = self._air_data
        self._suggestion = [{'title': SUGGESTIONTPYE2NAME[v.get('type')], 'title_cn': v.get('name'), 'brf': v.get('category'), 'txt': v.get('text') } for v in self._indices_data]

        datemsg = self._daily_data
        forec_cond = []
        
        self._daily_forecast = []
        for daily in self._daily_data:
            self._daily_forecast.append(
                {
                    ATTR_FORECAST_TIME: daily["fxDate"],
                    ATTR_FORECAST_NATIVE_TEMP: float(daily["tempMax"]),
                    ATTR_FORECAST_NATIVE_TEMP_LOW: float(daily["tempMin"]),
                    ATTR_FORECAST_CONDITION: CONDITION_MAP.get(
                        daily["iconDay"], EXCEPTIONAL
                    ),
                    "text": daily["textDay"],
                    "icon": daily["iconDay"],
                    "textnight": daily["textNight"],
                    "iconnight": daily["iconNight"],
                    ATTR_FORECAST_WIND_BEARING: float(daily["wind360Day"]),
                    ATTR_FORECAST_NATIVE_WIND_SPEED: float(daily["windSpeedDay"]),
                    ATTR_FORECAST_NATIVE_PRECIPITATION: float(daily["precip"]),
                    "humidity": float(daily["humidity"]),
                    ATTR_FORECAST_NATIVE_PRESSURE: float(daily["pressure"]),
                }
            )
            
        self._hourly_forecast = []
        for hourly in self._hourly_data:
            date_obj = datetime.fromisoformat(hourly["fxTime"].replace('Z', '+00:00'))
            formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
            self._hourly_forecast.append(
                {
                    "datetime": formatted_date,
                    ATTR_CONDITION_CLOUDY: hourly["cloud"],
                    ATTR_FORECAST_TEMP: float(hourly["temp"]),
                    ATTR_FORECAST_CONDITION: CONDITION_MAP.get(
                        hourly["icon"], EXCEPTIONAL
                    ),
                    "text": hourly["text"],
                    "icon": hourly["icon"],
                    ATTR_FORECAST_WIND_BEARING: float(hourly["wind360"]),
                    ATTR_FORECAST_WIND_SPEED: float(hourly["windSpeed"]),
                    ATTR_FORECAST_PRECIPITATION: float(hourly["precip"]),
                    ATTR_WEATHER_HUMIDITY: float(hourly["humidity"]),
                    "probable_precipitation": int(
                        hourly["pop"]
                    ),  # 降雨概率
                    ATTR_FORECAST_PRESSURE: float(hourly["pressure"]),
                }
            )
            
        self._minutely_forecast = []
        for minutely_data in self._minutely_data:
            self._minutely_forecast.append(
                {
                    "time": minutely_data['fxTime'][11:16],
                    "type": minutely_data["type"],
                    ATTR_FORECAST_PRECIPITATION: float(minutely_data["precip"]),
                }
            )
            
        self._weather_warning = []
        if len(self._warning_data):
            for warningItem in self._warning_data:
                self._weather_warning.append(
                    {
                        "pubTime": warningItem["pubTime"],
                        "startTime": warningItem["startTime"],
                        "endTime": warningItem["endTime"],
                        "sender": warningItem["sender"],
                        "title": warningItem["title"],
                        "text": warningItem["text"],
                        "severity": warningItem["severity"],
                        "severityColor": warningItem["severityColor"],
                        "level": warningItem["level"],
                        "typeName": warningItem["typeName"],
                    }
                )

        else:
            self._weather_warning.append(
                {
                   'text': '当前无灾害预警'
                }
            )
        _LOGGER.info("success to fetch local informations from API")

