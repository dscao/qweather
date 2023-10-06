VERSION = '2023.10.6'
ROOT_PATH = '/qweather-local'
DEFAULT_NAME = "和风天气"
DOMAIN = "qweather"
PLATFORMS = ["weather"]

ATTRIBUTION = "Data provided by Qweather"
MANUFACTURER = "Qweather, Inc."

CONF_API_KEY = "api_key"
CONF_API_VERSION = "api_version"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALERT = "alert"
CONF_LIFEINDEX = "life"
CONF_CUSTOM_UI = "custom_ui"
CONF_HOURLYSTEPS = "hourlysteps"
CONF_DAILYSTEPS = "dailysteps"
CONF_STARTTIME = "starttime"
CONF_UPDATE_INTERVAL = "update_interval_minutes"
CONF_GIRD = "grid_weather"


ATTR_CONDITION_CN = "condition_cn"
ATTR_UPDATE_TIME = "update_time"
ATTR_AQI = "aqi"
ATTR_DAILY_FORECAST = "daily_forecast"
ATTR_HOURLY_FORECAST = "hourly_forecast"
ATTR_MINUTELY_FORECAST = "minutely_forecast"
ATTR_SUGGESTION = "suggestion"
ATTR_CUSTOM_UI_MORE_INFO = "custom_ui_more_info"
ATTR_FORECAST_PROBABLE_PRECIPITATION = 'probable_precipitation'

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

