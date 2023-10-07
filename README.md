# 和风天气-官方API版
v2.0 2023.10.6

使用和风官方v7版api的和风天气完整配置版本（支持homeassistant 2023.9 以后版本）


[![hacs_badge](https://img.shields.io/badge/Home-Assistant-%23049cdb)](https://www.home-assistant.io/)
![visit](https://visitor-badge.laobi.icu/badge?page_id=dscao.qweather&left_text=visit)

## 官方接口说明

[官方开发文档](https://dev.qweather.com/docs/)

[和风天气数据更新时间](https://dev.qweather.com/docs/resource/glossary/#update-time)


## 使用方式

安装完成重启HA，刷新一下页面，在集成里搜索`和风天气`即可

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=hf_weather)

注意：
name 实体名字

api_key 和风申请的api key，申请地址：https://dev.qweather.com/  ，申请后，请认证为个人开发者，新建一个使用web api项目，获取key。早期申请的api_key可能没有分钟级预报及格点天气等请求权限。

location 经纬度，中国大陆地区应使用GCJ-02坐标系，在其他地区应使用WGS-84坐标系。
查询格式：经度,纬度（经度在前纬度在后，英文逗号分隔，十进制格式，北纬东经为正，南纬西经为负）。例如：location=116.41,39.92。

默认，查询7天的数据。需要认证开发者，免费订阅api请求额度 1000次/天。

刷新频率默认设置为10分钟，每次请求7个接口，安装或启动后第一次多请求一次geo接口，以显示city名称。

更新间隔，合计最快每小时16次，一天384次，每启动ha或重载集成增加请求1次。间隔默认为10分钟，当20分钟时一天312次，30分钟一天240次，60分钟一天168次。其它情况计算次数有点复杂。

实况类数据  	10-40分钟，最快以20分钟处理，3/小时

逐天预报   	1-8小时，最快以1小时处理，1次/小时

生活指数	    1小时 ，最快以1小时处理， 1次/小时

空气指数     未找到说明，当1小时处理，1次/小时

逐小时预报	1小时，最快以1小时处理，1次/小时

分钟级降雨	10-20分钟，最快以20分钟处理，3次/小时

灾害预警	    5分钟，最快以10分钟处理，6次/小时
 
> Lovelace配置

```yaml
type: 'custom:qweather-card'
entity: weather.tian_qi  #天气实体名称
title:                  #卡片标题
name:                   #名称，不填写则显示城市或县名称
show_attributes: true   #是否显示属性
show_hourly_forecast: true  #是否显示小时级预报
show_daily_forecast: true   #是否显示天级预报
show_daily_chart: true      #是否曲线图表
show_daily_date: true       #是否天级预报的日期
show_condition_text: true   #是否显示天级预报的天气名称
show_keypoint: true         #是否显示关键总结的一句话信息
show_warning: true          #是否显示气象预警信息
show_warningtext: false      #是否显示气象预警信息的详细内容
show_night: false            #是否显示天级预报的夜间内容
show_wind: false            #是否显示天级预报的风速风向
show_daily_temperature: false #是否显示天级预报的气温文字
show_thick_border: false      #是否以 #9e9e9e的线条显示，默认以系统divider线条显示
```
以上为默认选项，如需更改，则true改成false，false改成true。


> TTS语音提醒模板
```yaml
data:
  message: >-
    {% set state = state_attr('weather.tian_qi', 'daily_forecast')%}
    今天的天气是{{state[0].condition_cn}}，最高温度：{{state[0].native_temperature}}度，最低温度：{{state[0].native_templow}}度，
    明天的天气是{{state[1].condition_cn}}，最高温度：{{state[1].native_temperature}}度，最低温度：{{state[1].native_templow}}度，
    后天的天气是{{state[2].condition_cn}}，最高温度：{{state[2].native_temperature}}度，最低温度：{{state[2].native_templow}}度
service: ha_cloud_music.tts
```

```yaml
data:
  message: >-
    {% set state = state_attr('weather.tian_qi', 'hourly_forecast')%}
    {{state[0].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[0].condition_cn}}，温度是{{state[0].native_temperature}}度，
    {{state[1].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[1].condition_cn}}，温度是{{state[1].native_temperature}}度，
    {{state[2].datetime | regex_replace(now().strftime('%Y-%m-%d'), '')}}
    的天气是{{state[2].condition_cn}}，温度是{{state[2].native_temperature}}度
service: ha_cloud_music.tts
```


![1](https://github.com/dscao/qweather/assets/16587914/fb564690-e73b-4e60-b2ed-7ff211e84ee5)


![2](https://github.com/dscao/qweather/assets/16587914/ce7f01cd-738a-4d94-8db0-743215709782)


![3](https://github.com/dscao/qweather/assets/16587914/b1931902-a97f-4b27-a04e-9f27f29bd1d2)


![4](https://github.com/dscao/qweather/assets/16587914/75c54ab0-b631-4c90-8291-77dbf4e9f0d0)


![3](https://github.com/dscao/qweather/assets/16587914/57b7bff6-a8dd-4e30-9f03-4bcd6b2b1868)


感谢：https://github.com/shaonianzhentan/hf_weather 和 https://github.com/cheny95/qweather ，这个项目最初版本是结合了这两个项目的代码。
