"""

"""
import logging
from datetime import datetime, timedelta
import homeassistant.util.dt as dt_util
import asyncio
import async_timeout
import aiohttp
import json
import re
import sys
import time
import jwt
import asyncio
import logging
from dataclasses import dataclass, asdict
from pprint import pformat
from aiohttp import ClientConnectorError

from bs4 import BeautifulSoup
from requests import request
import voluptuous as vol
from aiohttp.client_exceptions import ClientConnectorError
from homeassistant.components import frontend
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.http import StaticPathConfig

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
    CONF_HOST,
    CONF_API_KEY, 
    CONF_NAME,
    CONF_DEFAULT,
    CONF_LATITUDE, 
    CONF_LONGITUDE, 
    UnitOfLength,
    UnitOfPressure,    
    UnitOfSpeed,
    UnitOfTemperature,
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
    CONF_USE_TOKEN,
    CONF_LOCATION,
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
    CONF_PROJECT_ID,
    CONF_KEY_ID,
    CONF_PRIVATE_KEY,
    )
    
from .condition import CONDITION_MAP, EXCEPTIONAL

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIME = dt_util.now()

# 集成安装
async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.debug(f"register_static_path: {ROOT_PATH + ':custom_components/qweather/local'}")
    await hass.http.async_register_static_paths([
        StaticPathConfig(ROOT_PATH, hass.config.path('custom_components/qweather/local'), False)
    ])
    frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-card.js?ver=' + VERSION)
    frontend.add_extra_js_url(hass, ROOT_PATH + '/qweather-card/qweather-more-info.js?ver=' + VERSION)

    _LOGGER.info("setup platform weather.Heweather...")

    name = config_entry.data.get(CONF_NAME)
    host = config_entry.data.get(CONF_HOST, "api.qweather.com")
    api_key = config_entry.data.get(CONF_API_KEY)
    usetoken = config_entry.data.get(CONF_USE_TOKEN, False)
    unique_id = config_entry.unique_id
    location = config_entry.data.get(CONF_LOCATION) or f"{round(config_entry.data.get(CONF_LONGITUDE, hass.config.longitude), 2)},{round(config_entry.data.get(CONF_LATITUDE, hass.config.latitude), 2)}"
    update_interval_minutes = config_entry.options.get(CONF_UPDATE_INTERVAL, 10)
    dailysteps = config_entry.options.get(CONF_DAILYSTEPS, 7)
    hourlysteps = config_entry.options.get(CONF_HOURLYSTEPS, 24)
    alert = config_entry.options.get(CONF_ALERT, True)
    life = config_entry.options.get(CONF_LIFEINDEX, True)
    custom_ui = config_entry.options.get(CONF_CUSTOM_UI, False)
    starttime = config_entry.options.get(CONF_STARTTIME, 0)
    gird_weather = config_entry.options.get(CONF_GIRD, False)
    config = {}
    config[CONF_PROJECT_ID] = config_entry.data.get(CONF_PROJECT_ID)
    config[CONF_KEY_ID] = config_entry.data.get(CONF_KEY_ID)
    config[CONF_PRIVATE_KEY] = config_entry.data.get(CONF_PRIVATE_KEY)
    config[CONF_API_KEY] = api_key
  
    data = WeatherData(hass, name, unique_id, host, config, usetoken, location, dailysteps ,hourlysteps, alert, life, starttime, gird_weather)

    weather_entity = HeFengWeather(data, custom_ui, unique_id, name)
    async_add_entities([weather_entity], True)
    _LOGGER.info(f"成功添加天气实体: {name}")
    
    session = async_get_clientsession(hass)
    data.set_session(session)

    async def initial_update():
        try:
            await data.async_update(dt_util.now())
            weather_entity.update_from_data()
            weather_entity.async_write_ha_state()
        except Exception as e:
            _LOGGER.exception("初始更新失败: %s", e) 

    hass.async_create_task(initial_update())

    async def periodic_update(now):
        try:
            await data.async_update(now)
            weather_entity.update_from_data()
            weather_entity.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("定时更新失败: %s", e)

    async_track_time_interval(hass, periodic_update, timedelta(minutes=update_interval_minutes))
    _LOGGER.debug('[%s]刷新间隔时间: %s 分钟', name, update_interval_minutes)

    return True

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
        self._feelslike = None
        self._cloud = None
        self._dew = None
        self._weather_warning = []
        self._attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_visibility_unit = UnitOfLength.KILOMETERS
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
        
        self._forecast_daily = list[list] | None
        self._forecast_hourly = list[list] | None
        self._forecast_twice_daily = list[list] | None
        
        self._available = False

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
    def available(self):
        """Return if entity is available."""
        return getattr(self, '_available', False)

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
        if not self._daily_forecast:
            return None
            
        forecast_data = []
        for forecast in self._daily_forecast:
            forecast_dict = {
                ATTR_FORECAST_TIME: forecast.datetime,
                ATTR_FORECAST_NATIVE_TEMP: forecast.native_temperature,
                ATTR_FORECAST_NATIVE_TEMP_LOW: forecast.native_temp_low,
                ATTR_FORECAST_CONDITION: forecast.condition,
                ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.native_precipitation,
                ATTR_FORECAST_NATIVE_WIND_SPEED: forecast.native_wind_speed,
                ATTR_FORECAST_WIND_BEARING: forecast.wind_bearing,
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: None, 
                # 添加其他需要显示的属性
                "text": forecast.text,
                "icon": forecast.icon,
                "textnight": forecast.textnight,
                "winddirday": forecast.winddirday,
                "winddirnight": forecast.winddirnight,
                "windscaleday": forecast.windscaleday,
                "windscalenight": forecast.windscalenight,
                "iconnight": forecast.iconnight
            }
            forecast_data.append(forecast_dict)
        
        #_LOGGER.debug('转换后的每日预报数据: %s', forecast_data)
        return forecast_data


    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        if not self._hourly_forecast:
            return None
            
        forecast_data = []
        for forecast in self._hourly_forecast:
            forecast_dict = {
                ATTR_FORECAST_TIME: forecast.datetime,
                ATTR_FORECAST_NATIVE_TEMP: forecast.native_temperature,
                ATTR_FORECAST_CONDITION: forecast.condition,
                ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.native_precipitation,
                ATTR_FORECAST_NATIVE_WIND_SPEED: forecast.native_wind_speed,
                ATTR_FORECAST_WIND_BEARING: forecast.wind_bearing,
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: forecast.probable_precipitation,
                # 添加其他属性
                "text": forecast.text,
                "icon": forecast.icon,
                "humidity": forecast.humidity
            }
            forecast_data.append(forecast_dict)
        
        return forecast_data

    async def async_forecast_twice_daily(self) -> list[Forecast]:
        """Return the twice daily forecast."""
        if not self._daily_twice_forecast:
            return None
            
        forecast_data = []
        for forecast in self._daily_twice_forecast:
            forecast_dict = {
                ATTR_FORECAST_TIME: forecast.datetime,
                ATTR_FORECAST_NATIVE_TEMP: forecast.native_temperature if forecast.is_daytime else None,
                ATTR_FORECAST_NATIVE_TEMP_LOW: None if forecast.is_daytime else forecast.native_temp_low,
                ATTR_FORECAST_CONDITION: forecast.condition,
                "is_daytime": forecast.is_daytime
            }
            forecast_data.append(forecast_dict)
        
        return forecast_data

    @property
    def state_attributes(self):
        attributes = super().state_attributes
        if self._condition is not None:
            # 转换数据类实例为字典
            daily_forecast = [asdict(item) for item in self._daily_forecast] if self._daily_forecast else []
            hourly_forecast = [asdict(item) for item in self._hourly_forecast] if self._hourly_forecast else []
            minutely_forecast = [asdict(item) for item in self._minutely_forecast] if self._minutely_forecast else []
            suggestion = [asdict(item) for item in self._suggestion] if self._suggestion else []
            weather_warning = [asdict(item) for item in self._weather_warning] if self._weather_warning else []
            
            attributes.update({
                "city": self._city,
                "qweather_icon": self._icon,
                ATTR_UPDATE_TIME: self._updatetime,
                ATTR_CONDITION_CN: self._condition_cn,
                ATTR_AQI: self._aqi,
                ATTR_DAILY_FORECAST: daily_forecast,
                ATTR_HOURLY_FORECAST: hourly_forecast,
                ATTR_MINUTELY_FORECAST: minutely_forecast,
                ATTR_SUGGESTION: suggestion,
                "forecast_minutely": self._minutely_summary,
                "forecast_hourly": self._hourly_summary,
                "warning": weather_warning,
                "winddir": self._winddir,
                "windscale": self._windscale,
                "sunrise": self._sun_data.get("sunrise", ""),
                "sunset": self._sun_data.get("sunset", ""),
                "feelslike": self._feelslike,
                "cloud": self._cloud,
                "dew": self._dew,
            })
            if self._custom_ui:
                attributes[ATTR_CUSTOM_UI_MORE_INFO] = "qweather-more-info"
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
      
    def update_from_data(self):
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
        self._minutely_summary = self._data._minutely_summary
        self._hourly_summary = self._data._hourly_summary
        self._weather_warning = self._data._weather_warning
        self._sun_data = self._data._sun_data
        self._city = self._data._city
        self._icon = self._data._icon
        self._feelslike = self._data._feelslike
        self._cloud = self._data._cloud
        self._dew = self._data._dew
        self._updatetime = self._data._refreshtime
        self._available = True

@dataclass
class Forecast:
    datetime: str
    native_temperature: float = None
    native_temp_low: float = None
    condition: str = None
    text: str = None
    icon: str = None
    wind_bearing: float = None
    native_wind_speed: float = None
    native_precipitation: float = None
    humidity: float = None
    native_pressure: float = None
    cloud: int = None
    textnight: str = None
    winddirday: str = None
    winddirnight: str = None
    windscaleday: str = None
    windscalenight: str = None
    iconnight: str = None
    is_daytime: bool = False

@dataclass
class HourlyForecast:
    datetime: str
    native_temperature: int = None
    condition: str = None
    text: str = None
    icon: str = None
    wind_bearing: int = None
    native_wind_speed: int = None
    native_precipitation: int = None
    humidity: int = None
    probable_precipitation: int = None
    native_pressure: int = None
    cloud: int = None
    
@dataclass
class MinutelyForecast:
    time: str
    type: str
    precipitation: float

@dataclass
class WarningData:
    pubTime: str
    startTime: str
    endTime: str
    sender: str
    title: str
    text: str
    severity: str
    severityColor: str
    level: str
    typeName: str

@dataclass
class Suggestion:
    title: str
    title_cn: str
    brf: str
    txt: str

class WeatherData(object):
    """天气相关的数据，存储在这个类中."""

    def __init__(self, hass, name, unique_id, host, config, usetoken, location, dailysteps ,hourlysteps, alert, life, starttime, gird_weather):
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
        self._daily_twice_forecast = None
        self._hourly_forecast = None
        self._minutely_forecast = None
        self._aqi = None
        self._winddir = None
        self._windscale = None
        self._suggestion = None
        self._weather_warning = None
        self._city = None
        self._feelslike = None
        self._cloud = None
        self._dew = None
             
        self._unique_id = unique_id
        self._host = host
        self._config = config
        self._use_token = usetoken
        self._location = location
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
        
        self.geo_url = f"https://{self._host}/geo/v2/city/lookup?location={self._location}&lang=zh"
        self.now_url = f"https://{self._host}/v7/weather/now?location={self._location}&lang=zh"
        self.daily_url = f"https://{self._host}/v7/weather/{self.default}d?location={self._location}&lang=zh"
        self.indices_url = f"https://{self._host}/v7/indices/1d?type=0&location={self._location}&lang=zh"
        self.air_url = f"https://{self._host}/v7/air/now?location={self._location}&lang=zh"
        self.hourly_url = f"https://{self._host}/v7/weather/{self._hourlysteps}h?location={self._location}&lang=zh"
        self.minutely_url = f"https://{self._host}/v7/minutely/5m?location={self._location}&lang=zh"
        self.warning_url = f"https://{self._host}/v7/warning/now?location={self._location}&lang=zh"
        self.sun_url = f"https://{self._host}/v7/astronomy/sun?location={self._location}&date={self._todaydate}&lang=zh"

        if self._gird_weather == True and self.validate_location(self._location)==True:
            self.now_url = self.now_url.replace("/weather/","/grid-weather/")
            self.daily_url = self.daily_url.replace("/weather/","/grid-weather/")
            self.hourly_url = self.hourly_url.replace("/weather/","/grid-weather/")
            
        self._update_time = None
        self._refreshtime = None
        self._hourly_summary = None
        self._minutely_summary = None
        
        
        _LOGGER.debug('self.daily_url: %s ', self.daily_url)
        #  官方数据  免费额度每月50000次 更新间隔，合计最快每小时16次，一天384次，每启动ha或重载集成增加请求1次。间隔默认为10分钟，当20分钟时一天312次，30分钟一天240次，60分钟一天168次。其它情况计算次数有点复杂。
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
        
        
    def get_forecast_summary(self, url):
        header = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'cookie': 'h_c=beijing-101010100; i_c=beijing-101010100; JSESSIONID=D72633A8513514A8ED11C1C4D85E5683'
        }
        response = request('GET', url, headers=header)
        response.encoding = 'utf-8'        
        soup = BeautifulSoup(response.text, "html.parser")
        _LOGGER.debug(response.text)
        responsetext = soup.select(".current-abstract")[0].contents[0].strip()
        _LOGGER.debug(responsetext)
        return responsetext
        
    def validate_location(self, location):
        if not isinstance(location, str):
            return False
        pattern = r"^-?\d+\.\d{1,2},^-?\d+\.\d{1,2}$"  # 允许负数坐标，小数点后1-2位
        match = re.match(pattern, location)
        if match:
            try:
                longitude, latitude = map(float, location.split(','))
                return True
            except ValueError:
                return False
        else:
            return False
            
    def generate_jwt(self, config):
        try:
            payload = {
                'iat': int(time.time()) - 30,
                'exp': int(time.time()) + 900,
                'sub': config[CONF_PROJECT_ID]
            }
            headers = {'kid': config[CONF_KEY_ID]}
            return jwt.encode(
                payload,
                config[CONF_PRIVATE_KEY],
                algorithm='EdDSA',
                headers=headers
            )
        except Exception as e:
            _LOGGER.error("生成JWT失败: %s", e)
            return None
            
    def set_session(self, session):
        self._session = session
        
    async def async_update(self, now):
        """获取天气数据"""
        _LOGGER.info("Update from QWeather's API...")
        
        if not self._session:
            _LOGGER.error("Session not initialized")
            return
    
        
        # 统一管理更新间隔
        min_intervals = {
            'warning': 600,
            'now': 1200,
            'daily': 3600,
            'indices': 3600,
            'air': 3600,
            'hourly': 3600,
            'minutely': 1200
        }
        
        if self._responsecode == '402':
            min_intervals = {k: 7200 for k in min_intervals}
        
        # 设置请求头
        if self._use_token:
            jwt_token = self.generate_jwt(self._config)
            if jwt_token:
                self.headers = {"Authorization": f"Bearer {jwt_token}"}
        else:
            self.headers = {"X-QW-Api-Key": self._config.get(CONF_API_KEY)}
        
        _LOGGER.debug("headers: %s", self.headers)
        
        # 创建异步任务列表
        current_time = int(datetime.now().timestamp())
        
        async def fetch_data(url, update_attr, data_attr, min_interval, json_key=None):

            last_update = getattr(self, update_attr, 0) or 0
            
            # 检查是否需要更新
            if current_time - last_update < min_interval:
                return False
        
            try:
                async with self._session.get(url, headers=self.headers, timeout=10) as response:
                    _LOGGER.debug("请求 %s 返回状态码: %d", url, response.status)
                    
                    if response.status >= 400:
                        try:
                            error_body = await response.text()
                            _LOGGER.error("API错误响应 (%s): %d - %s", url, response.status, error_body[:200])
                        except Exception:
                            _LOGGER.error("API错误响应 (%s): %d - 无法读取响应体", url, response.status)
                        return False
                    
                    try:
                        json_data = await response.json()
                        _LOGGER.debug("response json_data： %s", json_data)
                        
                        if url == self.now_url and 'code' in json_data:
                            self._responsecode = json_data.get("code")
                            # 处理API响应状态
                            if self._responsecode == '402':
                                self._minutely_summary = "API请求超过访问次数，暂停2小时再请求"
                                self._suggestion = [Suggestion(
                                    title='请求API出错', 
                                    title_cn='请求API出错', 
                                    brf='API出错', 
                                    txt='API请求超过访问次数，暂停2小时再请求。'
                                )]
                                _LOGGER.warning("API请求超过访问次数")
                                return False
                            elif self._responsecode == '200':
                                _LOGGER.info("成功从API获取本地信息")
                            else:
                                _LOGGER.warning("请求API错误，未取得数据，可能是API不支持相关类型，尝试关闭格点天气试试。")
                                return False
                        
                        if json_key:
                            data = json_data.get(json_key)
                            if data is None:
                                if json_key == 'now' and 'now' in json_data:
                                    data = json_data['now']
                                elif json_key == 'daily' and 'daily' in json_data:
                                    data = json_data['daily']
                                else:
                                    data = json_data
                        else:
                            data = json_data
                        
                        if data is not None:
                            setattr(self, data_attr, data)
                            setattr(self, update_attr, current_time)
                            return True

                    except (json.JSONDecodeError, ValueError) as error:
                        raw_text = await response.text()
                        _LOGGER.error("JSON解析失败 (%s): %s\n原始响应: %s", url, str(error), raw_text[:500])
                        return False

            except asyncio.TimeoutError:
                _LOGGER.warning("API请求超时 (%s): 超过10秒", url)
                return False

            except Exception as error:
                # 捕获所有其他可能的异常
                _LOGGER.exception("处理API请求时发生意外错误 (%s): %s", url, str(error))
                return False

        tasks = []
        tasks.append(fetch_data(self.now_url, '_updatetime_now', '_current', min_intervals['now'], 'now'))
        tasks.append(fetch_data(self.daily_url, '_updatetime_daily', '_daily_data', min_intervals['daily'], 'daily'))
        tasks.append(fetch_data(self.air_url, '_updatetime_air', '_air_data', min_intervals['air'], 'now'))
        tasks.append(fetch_data(self.hourly_url, '_updatetime_hourly', '_hourly_data', min_intervals['hourly'], 'hourly'))
        
        async def fetch_minutely():
            """单独处理分钟级预报数据，获取minutely_data和summary"""
            if current_time - (self._updatetime_minutely or 0) >= min_intervals['minutely']:
                try:
                    async with self._session.get(self.minutely_url, headers=self.headers, timeout=10) as response:
                        json_data = await response.json()
                        self._minutely_data = json_data.get("minutely") or self._minutely_data
                        self._minutely_summary = json_data.get("summary") or self._minutely_summary
                        self._updatetime_minutely = current_time
                        return True
                except Exception as error:
                    _LOGGER.exception("处理API分钟级预报请求时发生意外错误 (%s): %s", url, str(error))

            return False
        
        tasks.append(fetch_minutely())
        
        tasks.append(fetch_data(self.warning_url, '_updatetime_warning', '_warning_data', min_intervals['warning'], 'warning'))
        
        if self._life:
            tasks.append(fetch_data(self.indices_url, '_updatetime_indices', '_indices_data', min_intervals['indices'], 'daily'))
        
        # 执行所有任务
        results = await asyncio.gather(*tasks)
        _LOGGER.debug("API更新结果: %s", results)
        
        # 单独处理日出日落数据
        if self._sundate != self._todaydate:
            try:
                async with self._session.get(self.sun_url, headers=self.headers, timeout=10) as response:
                    sun_data = await response.json()
                    if 'daily' in sun_data and sun_data['daily']:
                        first_day = sun_data['daily'][0]
                        self._sun_data = {
                            'sunrise': first_day.get('sunrise', ''),
                            'sunset': first_day.get('sunset', '')
                        }
                        self._fxlink = sun_data.get("fxLink", "")
                    else:
                        self._sun_data = sun_data
                        self._fxlink = sun_data.get("fxLink", "")
                    self._sundate = self._todaydate
            except Exception as error:
                _LOGGER.warning("处理API日出日落请求时发生意外错误 (%s): %s", self.sun_url, str(error))
                    
        
        # 单独处理城市信息
        if not self._city:
            try:
                async with self._session.get(self.geo_url, headers=self.headers, timeout=10) as response:
                    geo_data = await response.json()
                    if 'location' in geo_data and geo_data['location']:
                        self._city = geo_data['location'][0].get("name", "未知")
                        _LOGGER.info("[%s]天气所在城市：%s", self._name, self._city)
                    else:
                        self._city = "未知"
            except Exception as error:
                _LOGGER.warning("城市信息API请求失败%s: %s", self.geo_url, str(error))
                self._city = "未知"
                    
        # 生成预报摘要
        if self._fxlink:
            try:            
                hourly_summary = await self._hass.async_add_executor_job(
                    self.get_forecast_summary, self._fxlink
                )
                self._hourly_summary = hourly_summary
            except Exception as error:
                _LOGGER.warning("获取预报摘要失败: %s", str(error))
                self._hourly_summary = ""
       
        
        # 记录调试信息
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("%s:实时天气数据 %s", self._name, datetime.fromtimestamp(self._updatetime_now))
            _LOGGER.debug(pformat(self._current))
            _LOGGER.debug("%s:逐天预报数据 %s", self._name, datetime.fromtimestamp(self._updatetime_daily))
            _LOGGER.debug(pformat(self._daily_data))
            _LOGGER.debug("%s:小时预报数据 %s", self._name, datetime.fromtimestamp(self._updatetime_hourly))
            _LOGGER.debug(pformat(self._hourly_data))
            _LOGGER.debug("%s:分钟预报数据 %s", self._name, datetime.fromtimestamp(self._updatetime_minutely))
            _LOGGER.debug(pformat(self._minutely_data))
            _LOGGER.debug("%s:预警信息 %s", self._name, datetime.fromtimestamp(self._updatetime_warning))
            _LOGGER.debug(pformat(self._warning_data))
            _LOGGER.debug("%s:生活指数 %s", self._name, datetime.fromtimestamp(self._updatetime_indices))
            _LOGGER.debug(pformat(self._indices_data))
            _LOGGER.debug("%s:空气数据 %s", self._name, datetime.fromtimestamp(self._updatetime_air))
            _LOGGER.debug(pformat(self._air_data))
            _LOGGER.debug("%s:日出日落数据 %s", self._name, self._sundate)
            _LOGGER.debug(pformat(self._sun_data))
        
        if isinstance(self._current, dict):
            # 标准处理
            self._icon = self._current.get("icon", "")
            self._native_temperature = float(self._current.get("temp", 0))
            self._humidity = int(self._current.get("humidity", 0))
            self._condition = CONDITION_MAP.get(self._current.get("icon", ""), EXCEPTIONAL)
            self._condition_cn = self._current.get("text", "")
            self._native_pressure = int(self._current.get("pressure", 0))
            self._native_wind_speed = float(self._current.get("windSpeed", 0))
            self._wind_bearing = float(self._current.get("wind360", 0))
            self._winddir = self._current.get("windDir", "")
            self._windscale = self._current.get("windScale", "")
            self._textnight = self._current.get("textNight", "")
            self._winddirday = self._current.get("windDirday", "")
            self._winddirnight = self._current.get("windDirNight", "")
            self._windscaleday = self._current.get("windScaleDay", "")
            self._windscalenight = self._current.get("windScaleNight", "")
            self._iconnight = self._current.get("iconNight", "")
            self._feelslike = float(self._current.get("feelsLike", 0))
            self._cloud = self._current.get("cloud", "")
            self._dew = self._current.get("dew","")
            

        else:
            _LOGGER.error("实时天气数据格式不正确")
        
        # 处理更新时间
        if self._update_time:
            try:
                date_obj = datetime.fromisoformat(self._update_time.replace('Z', '+00:00'))
                self._updatetime = date_obj.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                self._updatetime = "格式错误"
        else:
            self._updatetime = "未知"
        
        self._refreshtime = dt_util.as_local(now).strftime('%Y-%m-%d %H:%M')
        
        # 修复：正确处理空气质量数据结构
        if isinstance(self._air_data, dict):
            self._aqi = self._air_data
        elif isinstance(self._air_data, list) and self._air_data:
            self._aqi = self._air_data[0]
        else:
            self._aqi = {}
            _LOGGER.warning("空气质量数据结构异常")
        
        # 处理生活指数
        self._suggestion = []
        if self._indices_data:
            if isinstance(self._indices_data, dict) and 'daily' in self._indices_data:
                indices_list = self._indices_data['daily']
            elif isinstance(self._indices_data, list):
                indices_list = self._indices_data
            else:
                indices_list = []
                _LOGGER.warning("生活指数数据结构异常")
            
            for v in indices_list:
                self._suggestion.append(Suggestion(
                    title=SUGGESTIONTPYE2NAME.get(v.get('type'), "未知"),
                    title_cn=v.get('name', "未知"),
                    brf=v.get('category', "未知"),
                    txt=v.get('text', "")
                ))
        
        # 处理每日预报
        self._daily_forecast = []
        if self._daily_data:
            if isinstance(self._daily_data, dict) and 'daily' in self._daily_data:
                daily_list = self._daily_data['daily']
            elif isinstance(self._daily_data, list):
                daily_list = self._daily_data
            else:
                daily_list = []
                _LOGGER.warning("每日预报数据结构异常")
            
            for daily in daily_list:
                self._daily_forecast.append(Forecast(
                    datetime=daily.get("fxDate", ""),
                    native_temperature=float(daily.get("tempMax", 0)),
                    native_temp_low=float(daily.get("tempMin", 0)),
                    condition=CONDITION_MAP.get(daily.get("iconDay", ""), EXCEPTIONAL),
                    text=daily.get("textDay", ""),
                    icon=daily.get("iconDay", ""),
                    wind_bearing=float(daily.get("wind360Day", 0)),
                    native_wind_speed=float(daily.get("windSpeedDay", 0)),
                    native_precipitation=float(daily.get("precip", 0)),
                    humidity=float(daily.get("humidity", 0)),
                    native_pressure=float(daily.get("pressure", 0)),
                    textnight=daily.get("textNight", ""),
                    winddirday=daily.get("windDirDay", ""),
                    winddirnight=daily.get("windDirNight", ""),
                    windscaleday=daily.get("windScaleDay", ""),
                    windscalenight=daily.get("windScaleNight", ""),
                    iconnight=daily.get("iconNight", ""),
                    cloud=daily.get("cloud", ""),
                ))
        
        # 处理小时预报
        self._hourly_forecast = []        
        if self._hourly_data:
            # 修复：确保_hourly_data是列表
            hourly_list = self._hourly_data
            if isinstance(self._hourly_data, dict) and 'hourly' in self._hourly_data:
                hourly_list = self._hourly_data['hourly']
            
            for hourly in hourly_list:
                try:
                    date_obj = datetime.fromisoformat(hourly.get("fxTime", "").replace('Z', '+00:00'))
                    date_obj = dt_util.as_local(date_obj)
                    time_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    time_str = "时间格式错误"
                
                self._hourly_forecast.append(HourlyForecast(
                    datetime=time_str,
                    native_temperature=float(hourly.get("temp", 0)),
                    condition=CONDITION_MAP.get(hourly.get("icon", ""), EXCEPTIONAL),
                    text=hourly.get("text", ""),
                    icon=hourly.get("icon", ""),
                    wind_bearing=float(hourly.get("wind360", 0)),
                    native_wind_speed=float(hourly.get("windSpeed", 0)),
                    native_precipitation=float(hourly.get("precip", 0)),
                    humidity=float(hourly.get("humidity", 0)),
                    probable_precipitation=int(hourly.get("pop", 0)),
                    native_pressure=float(hourly.get("pressure", 0)),
                    cloud=hourly.get("cloud"),
                ))

        
        # 处理分钟级预报
        self._minutely_forecast = []
        if self._minutely_data:
            # 修复：确保_minutely_data是列表
            minutely_list = self._minutely_data
            if isinstance(self._minutely_data, dict) and 'minutely' in self._minutely_data:
                minutely_list = self._minutely_data['minutely']
            
            for minutely_data in minutely_list:
                self._minutely_forecast.append(MinutelyForecast(
                    time=minutely_data.get('fxTime', '')[11:16],
                    type=minutely_data.get("type", ""),
                    precipitation=float(minutely_data.get("precip", 0))
                ))

        
        # 处理白天/夜晚预报
        self._daily_twice_forecast = []
        if self._daily_data:
            # 使用上面处理过的daily_list
            for daily in daily_list:
                self._daily_twice_forecast.append(Forecast(
                    datetime=daily.get("fxDate", ""),
                    native_temperature=float(daily.get("tempMax", 0)),
                    condition=CONDITION_MAP.get(daily.get("iconDay", ""), EXCEPTIONAL),
                    is_daytime=True,
                    humidity=float(daily.get("humidity", 0))
                ))
                self._daily_twice_forecast.append(Forecast(
                    datetime=daily.get("fxDate", ""),
                    native_temp_low=float(daily.get("tempMin", 0)),
                    condition=CONDITION_MAP.get(daily.get("iconNight", ""), EXCEPTIONAL),
                    is_daytime=False,
                    humidity=float(daily.get("humidity", 0))
                ))
        
        # 处理天气预警
        self._weather_warning = []
        if self._warning_data:
            if isinstance(self._warning_data, dict) and 'warning' in self._warning_data:
                warning_list = self._warning_data['warning']
            elif isinstance(self._warning_data, list):
                warning_list = self._warning_data
            else:
                warning_list = []
                _LOGGER.warning("预警数据结构异常")
            
            for warningItem in warning_list:
                self._weather_warning.append(WarningData(
                    pubTime=warningItem.get("pubTime", ""),
                    startTime=warningItem.get("startTime", ""),
                    endTime=warningItem.get("endTime", ""),
                    sender=warningItem.get("sender", ""),
                    title=warningItem.get("title", ""),
                    text=warningItem.get("text", ""),
                    severity=warningItem.get("severity", ""),
                    severityColor=warningItem.get("severityColor", ""),
                    level=warningItem.get("level", ""),
                    typeName=warningItem.get("typeName", "")
                ))
        
        
