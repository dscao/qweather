"""

"""
import logging, os
from datetime import datetime, timedelta
import homeassistant.util.dt as dt_util
import asyncio
import async_timeout
import aiohttp
import re
from bs4 import BeautifulSoup
from requests import request
import voluptuous as vol
from aiohttp.client_exceptions import ClientConnectorError

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
    WeatherEntityFeature,
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
    CONF_API_KEY, 
    CONF_LATITUDE, 
    CONF_LONGITUDE, 
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

from .const import (
    VERSION, 
    ROOT_PATH, 
    ATTRIBUTION,
    MANUFACTURER,
    DEFAULT_NAME,
    DOMAIN,
    CONF_HOURLYSTEPS,
    CONF_DAILYSTEPS,
    CONF_ALERT,
    CONF_LIFEINDEX,
    CONF_CUSTOM_UI,
    CONF_STARTTIME,
    CONF_UPDATE_INTERVAL,
    CONF_GIRD,    
    ATTR_CONDITION_CN,
    ATTR_UPDATE_TIME,
    ATTR_AQI,
    ATTR_DAILY_FORECAST,
    ATTR_HOURLY_FORECAST,
    ATTR_MINUTELY_FORECAST,
    ATTR_SUGGESTION,
    ATTR_CUSTOM_UI_MORE_INFO,
    ATTR_FORECAST_PROBABLE_PRECIPITATION,
    CONDITION_CLASSES,
    TRANSLATE_SUGGESTION,
    SUGGESTIONTPYE2NAME,
    )
    
from .condition import CONDITION_MAP, EXCEPTIONAL

_LOGGER = logging.getLogger(__name__)

USER_AGENT_WX = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a29) NetType/WIFI Language/zh_CN'    
wxheaders = {'User-Agent': USER_AGENT_WX,
          'Host': 'api.qweather.com',
          'content-type': 'application/json',
          'Accept-Encoding': 'gzip,compress,br,deflate',
		  'Referer': 'https://servicewechat.com/wxb98fab0540fbd84b/9/page-frame.html'
          }

DEFAULT_TIME = dt_util.now()

# 集成安装
async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.debug(f"register_static_path: {ROOT_PATH + ':custom_components/qweather/local'}")
    hass.http.register_static_path(ROOT_PATH, hass.config.path('custom_components/qweather/local'), False)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-card.js?ver=' + VERSION)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-more-info.js?ver=' + VERSION)

    _LOGGER.info("setup platform weather.Heweather...")

    name = config_entry.data.get(CONF_NAME)    
    api_key = config_entry.data[CONF_API_KEY]
    unique_id = config_entry.unique_id
    longitude = round(config_entry.data[CONF_LONGITUDE],2)
    latitude = round(config_entry.data[CONF_LATITUDE],2)
    update_interval_minutes = config_entry.options.get(CONF_UPDATE_INTERVAL, 10)
    dailysteps = config_entry.options.get(CONF_DAILYSTEPS, 7)
    # if dailysteps != 7 and dailysteps !=3:
        # dailysteps = 7
    hourlysteps = config_entry.options.get(CONF_HOURLYSTEPS, 24)
    # if hourlysteps != 24:
        # hourlysteps = 24
    alert = config_entry.options.get(CONF_ALERT, True)
    life = config_entry.options.get(CONF_LIFEINDEX, True)
    custom_ui = config_entry.options.get(CONF_CUSTOM_UI, False)
    starttime = config_entry.options.get(CONF_STARTTIME, 0)
    gird_weather = config_entry.options.get(CONF_GIRD, False)
  
    data = WeatherData(hass, name, unique_id, api_key, longitude, latitude, dailysteps ,hourlysteps, alert, life, starttime, gird_weather)

    await data.async_update(dt_util.now())
    async_track_time_interval(hass, data.async_update, timedelta(minutes = update_interval_minutes))
    _LOGGER.debug('[%s]刷新间隔时间: %s 分钟', name, update_interval_minutes)
    async_add_entities([HeFengWeather(data, custom_ui, unique_id, name)], True)

class HeFengWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, data, custom_ui, unique_id, name):
        """Initialize the  weather."""
        self._name = name
        self._custom_ui = custom_ui
        self._unique_id = unique_id
        self._condition = None
        self._condition_cn = None
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
        self._winddir = None
        self._windscale = None
        self._suggestion = None
        self._daily_forecast = None
        self._hourly_forecast = None
        self._daily_twice_forecast = None
        self._minutely_forecast = None
        self._minutely_summary = None
        self._hourly_summary = None
        self._weather_warning = []
        self._attr_native_precipitation_unit = LENGTH_MILLIMETERS
        self._attr_native_pressure_unit = PRESSURE_HPA
        self._attr_native_temperature_unit = TEMP_CELSIUS
        self._attr_native_visibility_unit = LENGTH_KILOMETERS
        self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR
        
        forecast_daily = list[list] | None
        forecast_hourly = list[list] | None
        forecast_twice_daily = list[list] | None
        
        self._forecast_daily = forecast_daily
        self._forecast_hourly = forecast_hourly
        self._forecast_twice_daily = forecast_twice_daily
        self._attr_supported_features = 0
        if self._forecast_daily:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_DAILY
        if self._forecast_hourly:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_HOURLY
        if self._forecast_twice_daily:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_TWICE_DAILY

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
        
    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        #_LOGGER.debug("weather_unique_id: %s", self._unique_id)
        return self._unique_id
        
    @property
    def device_info(self):
        """Return the device info."""
        info = {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": self.name,
            "manufacturer": MANUFACTURER,
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
        return ATTRIBUTION
        
        
    async def async_forecast_daily(self) -> list[Forecast]:
        """Return the daily forecast."""
        reftime = dt_util.now().replace(hour=16, minute=00)
        if self._daily_forecast is None:
            return None
        reftime = datetime.now()
        forecast_data = self._daily_forecast
        #_LOGGER.debug('forecast_data: %s', forecast_data)
        return forecast_data


    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        reftime = dt_util.now().replace(hour=16, minute=00)
        return self._hourly_forecast

    async def async_forecast_twice_daily(self) -> list[Forecast]:
        """Return the twice daily forecast."""
        reftime = dt_util.now().replace(hour=11, minute=00)
        _LOGGER.debug('forecast_data: %s', self._daily_twice_forecast)
        return self._daily_twice_forecast
        

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
                ATTR_DAILY_FORECAST: self._daily_forecast,
                ATTR_HOURLY_FORECAST: self._hourly_forecast,
                ATTR_MINUTELY_FORECAST: self._minutely_forecast,
                ATTR_SUGGESTION: self._suggestion,
                "forecast_minutely": self._minutely_summary,
                "forecast_hourly": self._hourly_summary,
                "warning": self._weather_warning,
                "winddir": self._winddir,
                "windscale": self._windscale,
                "sunrise": self._sun_data.get("sunrise"),
                "sunset": self._sun_data.get("sunset"),
            })
            if self._custom_ui == True:
                attributes.update({                   
                    ATTR_CUSTOM_UI_MORE_INFO: "qweather-more-info",
                })
        return attributes

        
    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        """Set up a timer updating the forecasts."""

        async def update_forecasts(_: datetime) -> None:
            if self._forecast_daily:
                self._forecast_daily = (
                    self._forecast_daily[1:] + self._forecast_daily[:1]
                )
            if self._forecast_hourly:
                self._forecast_hourly = (
                    self._forecast_hourly[1:] + self._forecast_hourly[:1]
                )
            if self._forecast_twice_daily:
                self._forecast_twice_daily = (
                    self._forecast_twice_daily[1:] + self._forecast_twice_daily[:1]
                )
            await self.async_update_listeners(None)

        # self.async_on_remove(
            # async_track_time_interval(
                # self.hass, update_forecasts, WEATHER_UPDATE_INTERVAL
            # )
        # )        


    async def async_update(self):
        """update函数变成了async_update."""
        self._condition = self._data._condition
        self._condition_cn = self._data._condition_cn
        self._native_temperature = self._data._native_temperature
        self._humidity = self._data._humidity
        self._native_pressure = self._data._native_pressure
        self._native_wind_speed = self._data._native_wind_speed
        self._wind_bearing = self._data._wind_bearing
        self._daily_forecast = self._data._daily_forecast
        self._hourly_forecast = self._data._hourly_forecast
        self._daily_twice_forecast = self._data._daily_twice_forecast
        self._minutely_forecast = self._data._minutely_forecast
        self._aqi = self._data._aqi
        self._winddir = self._data._winddir
        self._windscale = self._data._windscale
        self._suggestion = self._data._suggestion
        self._minutely_summary = self._data.minutely_summary
        self._hourly_summary = self._data.hourly_summary
        self._weather_warning = self._data._weather_warning
        self._sun_data = self._data._sun_data
        self._city = self._data._city
        self._icon = self._data._icon
        self._updatetime = self._data._refreshtime



class WeatherData(object):
    """天气相关的数据，存储在这个类中."""

    def __init__(self, hass, name, unique_id, api_key, longitude, latitude, dailysteps ,hourlysteps, alert, life, starttime, gird_weather):
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
        self._winddir = None
        self._windscale = None
        self._suggestion = None
        self._weather_warning = None
        self._city = None
             
        self._unique_id = unique_id
        self._api_key = api_key
        self._longitude = longitude
        self._latitude = latitude
        self.default = dailysteps
        self._hourlysteps = hourlysteps
        self._alert = alert
        self._life = life
        self._starttime = starttime
        self._gird_weather = gird_weather

        self._current: dict = {}
        self._daily_data: list[dict] = []
        self._indices_data: list[dict] = []
        self._hourly_data: list[dict] = []
        self._minutely_data: list[dict] = []
        self._warning_data: list[dict] = []
        self._air_data = []
        self._sun_data = {}
        
        self._fxlink = ""
        
        self._sundate = None
        today = datetime.now()        
        self._todaydate = today.strftime("%Y%m%d")
        
        self.geo_url = f"https://geoapi.qweather.com/v2/city/lookup?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.now_url = f"https://devapi.qweather.com/v7/weather/now?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.daily_url = f"https://devapi.qweather.com/v7/weather/{self.default}d?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.indices_url = f"https://devapi.qweather.com/v7/indices/1d?type=0&location={self._longitude},{self._latitude}&key={self._api_key}"
        self.air_url = f"https://devapi.qweather.com/v7/air/now?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.hourly_url = f"https://devapi.qweather.com/v7/weather/{self._hourlysteps}h?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.minutely_url = f"https://devapi.qweather.com/v7/minutely/5m?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.warning_url = f"https://devapi.qweather.com/v7/warning/now?location={self._longitude},{self._latitude}&key={self._api_key}"
        self.sun_url = f"https://devapi.qweather.com/v7/astronomy/sun?location={self._longitude},{self._latitude}&date={self._todaydate}&key={self._api_key}"
        if str(self._api_key)[0:8] == "aa5bc22d":
            self.now_url = f"https://api.qweather.com/v7/weather/now?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.daily_url = f"https://api.qweather.com/v7/weather/{self.default}d?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.indices_url = f"https://api.qweather.com/v7/indices/1d?type=0&location={self._longitude},{self._latitude}&key={self._api_key}"
            self.air_url = f"https://api.qweather.com/v7/air/now?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.hourly_url = f"https://api.qweather.com/v7/weather/{self._hourlysteps}h?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.minutely_url = f"https://api.qweather.com/v7/minutely/5m?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.warning_url = f"https://api.qweather.com/v7/warning/now?location={self._longitude},{self._latitude}&key={self._api_key}"
            self.sun_url = f"https://api.qweather.com/v7/astronomy/sun?location={self._longitude},{self._latitude}&date={self._todaydate}&key={self._api_key}"
        
        
        
        if self._gird_weather == True and str(self._api_key)[0:8] != "aa5bc22d":
            self.now_url = self.now_url.replace("/weather/","/grid-weather/")
            self.daily_url = self.daily_url.replace("/weather/","/grid-weather/")
            self.hourly_url = self.hourly_url.replace("/weather/","/grid-weather/")
            
        self._update_time = None
        self.minutely_summary = None
        self.hourly_summary = None
        self._refreshtime = None
        
        
        _LOGGER.debug('self.daily_url: %s ', self.daily_url)
        #  官方数据   更新间隔，合计最快每小时16次，一天384次，每启动ha或重载集成增加请求1次。间隔默认为10分钟，当20分钟时一天312次，30分钟一天240次，60分钟一天168次。其它情况计算次数有点复杂。
        self._pubtime = None # 数据发布时间，是观测站或数据源发布的时间，代表当前数据是在什么时刻发布的。
        self._updatetime_now = 0       #实况类数据  	10-40分钟，最快以20分钟处理，3/小时
        self._updatetime_daily = 0     #逐天预报   	1-8小时，最快以1小时处理，1次/小时
        self._updatetime_indices = 0   #生活指数	    1小时 ，最快以1小时处理， 1次/小时
        self._updatetime_air = 0       #空气指数     未找到说明，当1小时处理，1次/小时
        self._updatetime_hourly = 0    #逐小时预报	1小时，最快以1小时处理，1次/小时
        self._updatetime_minutely = 0   #分钟级降雨	10-20分钟，最快以20分钟处理，3次/小时
        self._updatetime_warning = 0   #灾害预警	    5分钟，最快以10分钟处理，6次/小时
        self._updatetime_sun = 0  #日出日落，每天更新1次。
        self._responsecode = None #返回码为 402 超过访问次数或余额不足以支持继续访问服务，你可以充值、升级访问量或等待访问量重置。     429  超过限定的QPM（每分钟访问次数）

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def condition(self):
        """Return the current condition."""
#         return self._current["text"]
        return CONDITION_MAP.get(self._current.get("icon"), EXCEPTIONAL)
        
        
    def get_forecast_minutely(self, url):
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        response = request('GET', url, headers=header)
        response.encoding = 'utf-8'        
        soup = BeautifulSoup(response.text, "html.parser")
        responsetext = soup.select(".current-abstract")[0].contents[0].strip()
        _LOGGER.debug(responsetext)
        return responsetext

    async def async_update(self, now):
        """获取天气数据"""
        _LOGGER.info("Update from Qweather's OpenAPI...")
        timeout = aiohttp.ClientTimeout(total=30)  # 将超时时间设置为300秒
        connector = aiohttp.TCPConnector(limit=80, force_close=True)  # 将并发数量降低
        min_updatetime_warning = 600
        min_updatetime_now = 1200
        min_updatetime_daily = 3600        
        min_updatetime_indices = 3600
        min_updatetime_air = 3600
        min_updatetime_hourly = 3600
        min_updatetime_minutely = 1200
        
        _LOGGER.info("response code: %s", self._responsecode)
        if self._responsecode == '402':  # 超过访问次数时所有api请求2小时后再请求，因为好像返回402时本身还占用额度。
            min_updatetime_warning = 7200
            min_updatetime_now = 7200
            min_updatetime_daily = 7200        
            min_updatetime_indices = 7200
            min_updatetime_air = 7200
            min_updatetime_hourly = 7200
            min_updatetime_minutely = 7200
        
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=wxheaders) as session:                    
            if int(datetime.now().timestamp()) - int(self._updatetime_now) >= min_updatetime_now:
                async with session.get(self.now_url) as response:                
                    json_data = await response.json()
                    self._responsecode = json_data.get("code") or None
                    self._current = json_data.get("now") or self._current
                    self._update_time = json_data.get("updateTime") or self._update_time
                    self._updatetime_now = int(datetime.now().timestamp())
                
            if int(datetime.now().timestamp()) - int(self._updatetime_daily) >= min_updatetime_daily:
                async with session.get(self.daily_url) as response:
                    self._daily_data = (await response.json() or {}).get("daily") or self._daily_data
                    self._updatetime_daily = int(datetime.now().timestamp())

            if int(datetime.now().timestamp()) - int(self._updatetime_air) >= min_updatetime_air:
                async with session.get(self.air_url) as response:
                    self._air_data = (await response.json() or {}).get("now") or self._air_data
                    self._updatetime_air = int(datetime.now().timestamp())

            if int(datetime.now().timestamp()) - int(self._updatetime_hourly) >= min_updatetime_hourly:
                async with session.get(self.hourly_url) as response:
                    self._hourly_data = (await response.json() or {}).get("hourly") or self._hourly_data
                    self._updatetime_hourly = int(datetime.now().timestamp())

            if int(datetime.now().timestamp()) - int(self._updatetime_minutely) >= min_updatetime_minutely:
                async with session.get(self.minutely_url) as response:
                    self.minutely_summary = (await response.json() or None).get("summary") or self.minutely_summary
                    self._minutely_data = (await response.json() or {}).get("minutely") or self._minutely_data
                    self._updatetime_minutely = int(datetime.now().timestamp())
                    
            if self._life == True and int(datetime.now().timestamp()) - int(self._updatetime_indices) >= min_updatetime_indices:
                async with session.get(self.indices_url) as response:
                    self._indices_data = (await response.json() or {}).get("daily") or self._indices_data
                    self._updatetime_indices = int(datetime.now().timestamp())
                    
            if self._alert == True and int(datetime.now().timestamp()) - int(self._updatetime_warning) >= min_updatetime_warning:
                async with session.get(self.warning_url) as response:
                    json_data = await response.json()
                    self._warning_data = json_data.get("warning") or self._warning_data
                    self._updatetime_warning = int(datetime.now().timestamp())
            
            if self._sundate != self._todaydate:
                async with session.get(self.sun_url) as response:
                    self._sun_data = await response.json() or self._sun_data
                    self._sundate = self._todaydate
                    self._fxlink = self._sun_data.get("fxLink")
                
            if self._city == None:
                async with session.get(self.geo_url) as response:
                    try:
                        self._city = (await response.json() or {}).get("location")[0]["name"]
                        _LOGGER.info("[%s]天气所在城市：%s", self._name, self._city)
                    except:
                        self._city = "未知"
                        
        _LOGGER.debug("get forecast_minutely")        
        try:            
            hourly_summary = await self._hass.async_add_executor_job(self.get_forecast_minutely, self._fxlink)
        except (
            ClientConnectorError
        ) as error:
            hourly_summary = self.hourly_summary or ""
            raise UpdateFailed(error)
        
        _LOGGER.debug(hourly_summary)
            
        self.hourly_summary = hourly_summary

        # 根据http返回的结果，更新数据
        _LOGGER.debug(self._name + ":实时天气数据" + str(datetime.fromtimestamp(self._updatetime_now)))
        _LOGGER.debug(self._current)
        _LOGGER.debug(self._name + ":逐天预报数据" + str(datetime.fromtimestamp(self._updatetime_daily)))
        _LOGGER.debug(self._daily_data)
        _LOGGER.debug(self._name + ":小时预报数据"+ str(datetime.fromtimestamp(self._updatetime_daily)))
        _LOGGER.debug(self._hourly_data)
        _LOGGER.debug(self._name + ":分钟预报数据"+ str(datetime.fromtimestamp(self._updatetime_minutely)))
        _LOGGER.debug(self._minutely_data)
        _LOGGER.debug(self._name + ":简要信息"+ str(datetime.fromtimestamp(self._updatetime_minutely)))
        _LOGGER.debug(self.minutely_summary)
        _LOGGER.debug(self._name + ":预警信息"+ str(datetime.fromtimestamp(self._updatetime_warning)))
        _LOGGER.debug(self._warning_data)
        _LOGGER.debug(self._name + ":生活指数"+ str(datetime.fromtimestamp(self._updatetime_indices)))
        _LOGGER.debug(self._indices_data)
        _LOGGER.debug(self._name + ":空气数据"+ str(datetime.fromtimestamp(self._updatetime_air)))
        _LOGGER.debug(self._air_data)
        _LOGGER.debug(self._name + ":日出日落数据"+ str(self._sundate))
        _LOGGER.debug(self._sun_data)       
        
        self._icon = self._current.get("icon")
        self._native_temperature = float(self._current.get("temp") or 0)
        self._humidity = int(self._current.get("humidity") or 0)
        self._condition = CONDITION_MAP.get(self._current.get("icon"), EXCEPTIONAL)
        self._condition_cn = self._current.get("text")
        self._native_pressure = int(self._current.get("pressure") or 0)
        self._native_wind_speed = float(self._current.get("windSpeed") or 0)
        self._wind_bearing = float(self._current.get("wind360") or 0)
        self._winddir = self._current.get("windDir")
        self._windscale = self._current.get("windScale")
        if self._update_time:
            date_obj = datetime.fromisoformat(self._update_time.replace('Z', '+00:00'))
            formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
            self._updatetime = formatted_date
        else:
            self._updatetime = "未知"
        self._refreshtime = datetime.strftime(dt_util.as_local(now), '%Y-%m-%d %H:%M')
        self._aqi = self._air_data
        if self._indices_data:
            self._suggestion = [{'title': SUGGESTIONTPYE2NAME[v.get('type')], 'title_cn': v.get('name'), 'brf': v.get('category'), 'txt': v.get('text') } for v in self._indices_data]
        
        self._daily_forecast = []
        if self._daily_data:
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
                        "winddirday": daily["windDirDay"],
                        "winddirnight": daily["windDirNight"],
                        "windscaleday": daily["windScaleDay"],
                        "windscalenight": daily["windScaleNight"],
                        "iconnight": daily["iconNight"],
                        ATTR_FORECAST_WIND_BEARING: float(daily["wind360Day"]),
                        ATTR_FORECAST_NATIVE_WIND_SPEED: float(daily["windSpeedDay"]),
                        ATTR_FORECAST_NATIVE_PRECIPITATION: float(daily["precip"]),
                        "humidity": float(daily["humidity"]),
                        ATTR_FORECAST_NATIVE_PRESSURE: float(daily["pressure"]),
                    }
                )
            
            
        self._hourly_forecast = []        
        if self._hourly_data:
            summarystr = ""
            summarymaxprecipstr = ""
            summaryendstr = ""
            summaryday = ""
            summarystart = 0
            summaryend = 0
            summaryprecip = 0
            for hourly in self._hourly_data:
                date_obj = datetime.fromisoformat(hourly["fxTime"].replace('Z', '+00:00'))
                date_obj = dt_util.as_local(date_obj)
                formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
                
                #_LOGGER.info("小时记录：%s", formatted_date)
                if hourly.get("pop"):
                    pop = int(hourly["pop"])
                else:
                    pop = 0
                self._hourly_forecast.append(
                    {
                        "datetime": formatted_date,
                        ATTR_CONDITION_CLOUDY: hourly["cloud"],
                        ATTR_FORECAST_NATIVE_TEMP: float(hourly["temp"]),
                        ATTR_FORECAST_CONDITION: CONDITION_MAP.get(
                            hourly["icon"], EXCEPTIONAL
                        ),
                        "text": hourly["text"],
                        "icon": hourly["icon"],
                        ATTR_FORECAST_WIND_BEARING: float(hourly["wind360"]),
                        ATTR_FORECAST_NATIVE_WIND_SPEED: float(hourly["windSpeed"]),
                        ATTR_FORECAST_NATIVE_PRECIPITATION: float(hourly["precip"]),
                        ATTR_WEATHER_HUMIDITY: float(hourly["humidity"]),
                        "probable_precipitation": pop,  # 降雨概率，城市天气才有，格点天气不存在。
                        ATTR_FORECAST_PRESSURE: float(hourly["pressure"]),
                    }
                )
                
                if float(hourly["precip"])>0.1 and summarystart > 0:
                    if summarystart < 4:
                        summarystr = str(summarystart)+"小时后转"+hourly["text"]+"。"
                    else:
                        if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                            summaryday = "今天"
                        else:
                            summaryday = "明天"
                        summarystr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点后转"+hourly["text"]+"。"
                    summarystart = -1000
                    summaryprecip = float(hourly["precip"])
                if float(hourly["precip"])>0.1 and float(hourly["precip"]) > summaryprecip:
                    if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                        summaryday = "今天"
                    else:
                        summaryday = "明天"
                    probablestr = ""
                    #if hourly.get("pop"):
                    #    probablestr = "，降水概率为 " + hourly.get("pop") + "%"
                    summarymaxprecipstr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点为"+hourly["text"] + probablestr+ "！"
                    summaryprecip = float(hourly["precip"])
                    summaryend = 0
                    summaryendstr = ""
                # _LOGGER.debug("hourly precip：%s", hourly["precip"])
                if float(hourly["precip"]) == 0 and summaryprecip>0 and summaryend ==0:
                    if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                        summaryday = "今天"
                    else:
                        summaryday = "明天"
                    summaryendstr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点后转"+hourly["text"]+"。"
                    summaryend += 1
                summarystart += 1
            if summarystr and self.hourly_summary == "":
                self.hourly_summary = summarystr + summarymaxprecipstr + summaryendstr
            elif self.hourly_summary == "":
                self.hourly_summary = "未来24小时内无降水"
                
                
            self._minutely_forecast = []
            for minutely_data in self._minutely_data:
                self._minutely_forecast.append(
                    {
                        "time": minutely_data['fxTime'][11:16],
                        "type": minutely_data["type"],
                        ATTR_FORECAST_PRECIPITATION: float(minutely_data["precip"]),
                    }
                )
                
        self._daily_twice_forecast = []
        if self._daily_data:
            for daily in self._daily_data:
                self._daily_twice_forecast.append(
                    {
                        ATTR_FORECAST_TIME: daily["fxDate"],
                        ATTR_FORECAST_NATIVE_TEMP: float(daily["tempMax"]),
                        ATTR_FORECAST_NATIVE_TEMP_LOW: "",
                        ATTR_FORECAST_CONDITION: CONDITION_MAP.get(
                            daily["iconDay"], EXCEPTIONAL
                        ),
                        "is_daytime": True,
                        "humidity": float(daily["humidity"]),
                    }
                )
                self._daily_twice_forecast.append(
                    {
                        ATTR_FORECAST_TIME: daily["fxDate"],
                        ATTR_FORECAST_NATIVE_TEMP: "",
                        ATTR_FORECAST_NATIVE_TEMP_LOW: float(daily["tempMin"]),
                        ATTR_FORECAST_CONDITION: CONDITION_MAP.get(
                            daily["iconNight"], EXCEPTIONAL
                        ),
                        "is_daytime": False,
                        "humidity": float(daily["humidity"]),
                    }                    
                )
            
        self._weather_warning = []
        if self._warning_data:
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
                
        if self._responsecode == '402':
            self.minutely_summary = "API请求超过访问次数，暂停2小时再请求"
            self._suggestion = [{'title': '请求API出错', 'title_cn': '请求API出错', 'brf': 'API出错', 'txt': 'API请求超过访问次数，暂停2小时再请求。'}]
            _LOGGER.info("API请求超过访问次数")
        elif self._responsecode == '200':
            _LOGGER.info("success to fetch local informations from API")
        else:
            _LOGGER.info("请求api错误，未取得数据，可能是api不支持相关类型，尝试关闭格点天气试试。")

