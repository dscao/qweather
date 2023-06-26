# https://www.home-assistant.io/integrations/weather/
# https://dev.qweather.com/docs/resource/icons/


CLEAR_NIGHT = "clear-night"  # 晴夜
CLOUDY = "cloudy"  # 阴 ha中对应多去
FOG = "fog"  # 雾
HAIL = "hail"  # 冰雹
LIGHTNING = "lightning"  # 闪电
LIGHTNING_RAINY = "lightning-rainy"  # 闪电雨
PARTYCLOUDY = "partlycloudy"  # 多云 ha中对应阴
POURING = "pouring"  # 倾盆大雨
RAINY = "rainy"  # 下雨
SNOWY = "snowy"  # 下雪
SNOWY_RAINY = "snowy-rainy"  # 雪雨
SUNNY = "sunny"  # 晴天
WINDY = "windy"  # 有风
WINDY_VARIANT = "windy-variant"  # 风变
EXCEPTIONAL = "exceptional"  # 例外
CLOUDY_NIGHT = "cloudy"  # 夜间阴 ha中对应多云
POURING_RAINY = "pouring"  # 倾盆大雨
SNOWY_HEAVY = "snowy"  # 大雪
PARTY_CLOUDY_NIGHT = "partlycloudy"  # 夜间多云

# 'CLEAR_DAY': 'sunny',
# 'CLEAR_NIGHT': 'clear-night',
# 'PARTLY_CLOUDY_DAY': 'partlycloudy',
# 'PARTLY_CLOUDY_NIGHT':'partlycloudy',
# 'CLOUDY': 'cloudy',
# 'LIGHT_HAZE': 'fog',
# 'MODERATE_HAZE': 'fog',
# 'HEAVY_HAZE': 'fog',
# 'LIGHT_RAIN': 'rainy',
# 'MODERATE_RAIN': 'rainy',
# 'HEAVY_RAIN': 'pouring',
# 'STORM_RAIN': 'pouring',
# 'FOG': 'fog',
# 'LIGHT_SNOW': 'snowy',
# 'MODERATE_SNOW': 'snowy',
# 'HEAVY_SNOW': 'snowy',
# 'STORM_SNOW': 'snowy',
# 'DUST': 'fog',
# 'SAND': 'fog',
# 'THUNDER_SHOWER': 'lightning-rainy',
# 'HAIL': 'hail',
# 'SLEET': 'snowy-rainy',
# 'WIND': 'windy',
# 'HAZE': 'fog',
# 'RAIN': 'rainy',
# 'SNOW': 'snowy',


CONDITION_MAP = {
    "100": SUNNY,  # 晴
    "100": SUNNY,  # 晴
    "101": PARTYCLOUDY,  # 多云
    "102": CLOUDY,  # 少云
    "103": PARTYCLOUDY,  # 晴间多云
    "104": CLOUDY,  # 阴
    # 夜间
    "150": CLEAR_NIGHT,  # 晴
    "151": CLOUDY_NIGHT,  # 多云
    "152": CLOUDY_NIGHT,  # 少云
    "153": PARTY_CLOUDY_NIGHT,  # 夜间多云
    "154": CLOUDY,  # 阴
    "300": RAINY,  # 阵雨
    "301": RAINY,  # 强阵雨
    "302": LIGHTNING_RAINY,  # 雷阵雨
    "303": LIGHTNING_RAINY,  # 强雷阵雨
    "304": HAIL,  # 雷阵雨伴有冰雹
    "305": RAINY,  # 小雨
    "306": RAINY,  # 中雨
    "307": POURING_RAINY,  # 大雨
    "308": POURING_RAINY,  # 极端降雨
    "309": RAINY,  # 毛毛雨/细雨
    "310": POURING_RAINY,  # 暴雨
    "311": POURING_RAINY,  # 大暴雨
    "312": POURING_RAINY,  # 特大暴雨
    "313": RAINY,  # 冻雨
    "314": RAINY,  # 小到中雨
    "315": RAINY,  # 中到大雨
    "316": POURING_RAINY,  # 大到暴雨
    "317": POURING_RAINY,  # 暴雨到大暴雨
    "318": POURING_RAINY,  # 大暴雨到特大暴雨
    "350": RAINY,  # 阵雨
    "351": POURING_RAINY,  # 强阵雨
    "399": RAINY,  # 雨
    "400": SNOWY,  # 小雪
    "401": SNOWY,  # 中雪
    "402": SNOWY_HEAVY,  # 大雪
    "403": SNOWY_HEAVY,  # 暴雪
    "404": SNOWY_RAINY,  # 雨夹雪
    "405": SNOWY_RAINY,  # 雨雪天气
    "406": SNOWY_RAINY,  # 阵雨夹雪
    "407": RAINY,  # 阵雪
    "408": RAINY,  # 小到中雪
    "409": RAINY,  # 中到大雪
    "410": SNOWY_HEAVY,  # 大到暴雪
    "456": SNOWY_RAINY,  # 阵雨夹雪
    "457": RAINY,  # 阵雪
    "499": RAINY,  # 雪
    "500": FOG,  # 薄雾
    "501": FOG,  # 雾
    "502": FOG,  # 霾
    "503": EXCEPTIONAL,  # 扬沙
    "504": EXCEPTIONAL,  # 浮尘
    "507": EXCEPTIONAL,  # 沙尘暴
    "508": EXCEPTIONAL,  # 强沙尘暴
    "509": FOG,  # 浓雾
    "510": FOG,  # 强浓雾
    "511": FOG,  # 中度霾
    "512": FOG,  # 重度霾
    "513": FOG,  # 严重霾
    "514": FOG,  # 大雾
    "515": FOG,  # 特强浓雾
    "900": EXCEPTIONAL,  # 热
    "901": EXCEPTIONAL,  # 冷
    "999": EXCEPTIONAL,  # 未知
}
