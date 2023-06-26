# qweather
使用和风官方v7版api的和风天气最简单的配置版本

[![hacs_badge](https://img.shields.io/badge/Home-Assistant-%23049cdb)](https://www.home-assistant.io/)
![visit](https://visitor-badge.laobi.icu/badge?page_id=dscao.qweather&left_text=visit)

## 使用方式

安装完成重启HA，刷新一下页面，在集成里搜索`和风天气`即可

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=hf_weather)

注意：
name 实体名字
api_key 和风申请的api key，申请地址：https://dev.qweather.com/，申请后，请认证为个人开发者，新建一个使用web api项目，获取key。
location 经纬度，请参考和风官方的地址列表，搜索你所在的地区。
默认，查询7天的数据。需要认证开发者，有一些格点天气之类的必须需要开发者。
刷新频率默认设置为30分钟，每次请求7个接口，安装或启动后第一次多请求一次geo接口，以显示city名称。正常情况每天请求次数不会超1000次的免费额度，以后可再根据接口更新频率再优化。

> Lovelace配置

```yaml
type: 'custom:qweather-card'
entity: weather.tian_qi

# 不设置则同时显示
mode: hourly按小时天气预报、daily按天天气预报

# 不设置则使用entity的friendly_name
title: 卡片标题
```

> TTS语音提醒模板
```yaml
data:
  message: >-
    {% set state = state_attr('weather.tian_qi', 'forecast')%}
    今天的天气是{{state[0].condition_cn}}，最高温度：{{state[0].temperature}}度，最低温度：{{state[0].templow}}度，
    明天的天气是{{state[1].condition_cn}}，最高温度：{{state[1].temperature}}度，最低温度：{{state[1].templow}}度，
    后天的天气是{{state[2].condition_cn}}，最高温度：{{state[2].temperature}}度，最低温度：{{state[2].templow}}度
service: ha_cloud_music.tts
```

```yaml
data:
  message: >-
    {% set state = state_attr('weather.tian_qi', 'hourly_forecast')%}
    {{state[0].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[0].condition_cn}}，温度是{{state[0].temperature}}度，
    {{state[1].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[1].condition_cn}}，温度是{{state[1].temperature}}度，
    {{state[2].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[2].condition_cn}}，温度是{{state[2].temperature}}度
service: ha_cloud_music.tts
```

![1](https://github.com/dscao/qweather/assets/16587914/0c8432ae-d6b1-4a44-a111-753c961ccabd)

![2](https://github.com/dscao/qweather/assets/16587914/97a6fb78-4210-4564-9397-718526abc6d9)

![3](https://github.com/dscao/qweather/assets/16587914/57b7bff6-a8dd-4e30-9f03-4bcd6b2b1868)
