console.info("%c  QWEATHER MORE INFO \n%c  Version 2026.02.01.NativeStyle ",
"color: orange; font-weight: bold; background: black", 
"color: white; font-weight: bold; background: dimgray");

import {
  LitElement,
  html,
  css
} from "./vendor/lit-element.js";

class MoreInfoWeather extends LitElement {
  static get properties() {
    return {
      hass: Object,
      stateObj: Object,
      _forecast: Array,       // 每日预报数据
      _forecastHourly: Array, // 小时预报数据
      _subscribing: Boolean,
      _selectedTab: String    // 'daily' or 'hourly'
    };
  }

  constructor() {
    super();
    this._forecast = [];
    this._forecastHourly = [];
    this._subscribing = false;
    this._selectedTab = 'daily'; // 默认显示每日
    this.weatherIcons = {
      "clear-night": "hass:weather-night",
      "cloudy": "hass:weather-cloudy",
      "exceptional": "hass:alert-circle-outline",
      "fog": "hass:weather-fog",
      "hail": "hass:weather-hail",
      "lightning": "hass:weather-lightning",
      "lightning-rainy": "hass:weather-lightning-rainy",
      "partlycloudy": "hass:weather-partly-cloudy",
      "pouring": "hass:weather-pouring",
      "rainy": "hass:weather-rainy",
      "snowy": "hass:weather-snowy",
      "snowy-rainy": "hass:weather-snowy-rainy",
      "sunny": "hass:weather-sunny",
      "windy": "hass:weather-windy",
      "windy-variant": "hass:weather-windy-variant"
    };
  }

  // 样式复刻 HA 原生弹窗
  static get styles() {
    return css`
      :host {
        font-family: var(--paper-font-body1_-_font-family);
        -webkit-font-smoothing: var(--paper-font-body1_-_-webkit-font-smoothing);
        font-size: var(--paper-font-body1_-_font-size);
        font-weight: var(--paper-font-body1_-_font-weight);
        line-height: var(--paper-font-body1_-_line-height);
      }
      
      ha-icon {
        color: var(--paper-item-icon-color);
      }

      /* 头部样式：大图标+状态 */
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
      }
      .header-left {
        display: flex;
        align-items: center;
      }
      .weather-icon {
        width: 64px;
        height: 64px;
        margin-right: 16px;
        border-radius: 50%;
        background-color: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .weather-icon ha-icon {
        width: 42px;
        height: 42px;
        color: var(--paper-item-icon-color);
      }
      .weather-icon img {
        width: 42px;
        height: 42px;
      }
      .condition-state {
        font-size: 28px;
        font-weight: 400;
      }
      .condition-time {
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .header-right {
        text-align: right;
      }
      .current-temp {
        font-size: 42px;
        line-height: 1;
        font-weight: 400;
      }
      .current-temp span {
        font-size: 20px;
        vertical-align: top;
        margin-left: 2px;
      }

      /* 属性列表 */
      .attributes-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 24px;
      }
      .attribute-item {
        display: flex;
        align-items: center;
      }
      .attribute-item ha-icon {
        margin-right: 16px;
        color: var(--secondary-text-color);
      }
      .attribute-name {
        color: var(--secondary-text-color);
        margin-right: 8px;
      }
      .attribute-value {
        color: var(--primary-text-color);
      }

      /* 预警区域 */
      .warning-section {
        background-color: var(--error-color);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-weight: bold;
        display: flex;
        align-items: flex-start;
      }
      .warning-section ha-icon {
        color: white;
        margin-right: 12px;
      }

      /* 生活指数区域 */
      .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        background: var(--secondary-background-color);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 24px;
      }
      .suggestion-item {
        font-size: 12px;
        display: flex;
        justify-content: space-between;
      }
      .suggestion-label {
        color: var(--secondary-text-color);
      }

      /* 预报 Tab 栏 */
      .tabs {
        display: flex;
        border-bottom: 1px solid var(--divider-color);
        margin-bottom: 16px;
      }
      .tab {
        padding: 12px 24px;
        cursor: pointer;
        font-weight: 500;
        color: var(--secondary-text-color);
        border-bottom: 2px solid transparent;
      }
      .tab.active {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
      }

      /* 预报列表 */
      .forecast-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .forecast-item:last-child {
        border-bottom: none;
      }
      .forecast-time {
        width: 100px;
        font-weight: 500;
      }
      .forecast-icon {
        flex: 1;
        text-align: center;
      }
      .forecast-icon img {
        width: 32px;
        height: 32px;
        vertical-align: middle;
      }
      .forecast-temp {
        width: 100px;
        text-align: right;
        font-weight: 500;
      }
      .forecast-low {
        color: var(--secondary-text-color);
        margin-left: 8px;
      }
    `;
  }

  updated(changedProperties) {
    if (changedProperties.has("stateObj") && this.stateObj) {
      this._subscribeForecast();
    }
  }

  async _subscribeForecast() {
    if (!this.hass || !this.stateObj || this._subscribing) return;
    const entity_id = this.stateObj.entity_id;
    this._subscribing = true;

    try {
      // 订阅每日
      this.hass.connection.subscribeMessage(
        (msg) => {
          this._forecast = msg.forecast;
          this.requestUpdate();
        },
        { type: "weather/subscribe_forecast", entity_id: entity_id, forecast_type: "daily" }
      );
      // 订阅每小时
      this.hass.connection.subscribeMessage(
        (msg) => {
          this._forecastHourly = msg.forecast;
          this.requestUpdate();
        },
        { type: "weather/subscribe_forecast", entity_id: entity_id, forecast_type: "hourly" }
      );
    } catch (e) {
      console.error("Sub error", e);
      this._subscribing = false;
    }
  }

  getUnit(measure) {
    return this.hass.config.unit_system[measure] || "";
  }

  gethfIconurl(icon) {
    return `/qweather-local/qweather-card/icons/${icon}.svg`
  }
  
  _setTab(tab) {
    this._selectedTab = tab;
    this.requestUpdate();
  }

  _formatDate(datetime) {
    const d = new Date(datetime);
    const now = new Date();
    if (d.getDate() === now.getDate()) return "今天";
    return d.toLocaleDateString(this.hass.language, { weekday: "long" });
  }

  _formatTime(datetime) {
    const d = new Date(datetime);
    return d.toLocaleTimeString(this.hass.language, { hour: 'numeric', minute: '2-digit', hour12: false });
  }

  render() {
    if (!this.stateObj) return html``;
    const attr = this.stateObj.attributes;
    const tempUnit = attr.temperature_unit;
    const forecast = this._selectedTab === 'daily' ? (this._forecast || []) : (this._forecastHourly || []);

    return html`
      <div class="header">
        <div class="header-left">
          <div class="weather-icon">
            ${attr.qweather_icon 
              ? html`<img src="${this.gethfIconurl(attr.qweather_icon)}" alt="">`
              : html`<ha-icon icon="${this.weatherIcons[this.stateObj.state] || 'mdi:weather-partly-cloudy'}"></ha-icon>`
            }
          </div>
          <div>
            <div class="condition-state">${attr.condition_cn || this.stateObj.state}</div>
            <div class="condition-time">${attr.update_time || ''}</div>
          </div>
        </div>
        <div class="header-right">
          <div class="current-temp">${attr.temperature}<span>${tempUnit}</span></div>
        </div>
      </div>

      <div class="attributes-grid">
        ${this._renderAttribute('hass:water-percent', '湿度', `${attr.humidity} %`)}
        ${this._renderAttribute('hass:gauge', '气压', `${attr.pressure} hPa`)}
        ${this._renderAttribute('hass:weather-windy', '风速', `${attr.wind_speed} ${this.getUnit('length')}/h`)}
        ${this._renderAttribute('hass:eye', '能见度', `${attr.visibility} km`)}
      </div>

      ${attr.warning && attr.warning.length > 0 ? html`
        ${attr.warning.map(w => html`
          <div class="warning-section">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <div>
              <div style="font-size: 14px;">${w.title}</div>
              <div style="font-size: 12px; font-weight: normal; margin-top: 4px;">${w.text}</div>
            </div>
          </div>
        `)}
      ` : ''}

      ${attr.suggestion ? html`
        <div class="suggestion-grid">
          ${attr.suggestion.map(s => html`
            <div class="suggestion-item">
              <span class="suggestion-label">${s.title_cn}</span>
              <span>${s.brf}</span>
            </div>
          `)}
        </div>
      ` : ''}

      <div class="tabs">
        <div class="tab ${this._selectedTab === 'daily' ? 'active' : ''}" @click=${() => this._setTab('daily')}>
          每日预报
        </div>
        <div class="tab ${this._selectedTab === 'hourly' ? 'active' : ''}" @click=${() => this._setTab('hourly')}>
          小时预报
        </div>
      </div>

      <div class="forecast-list">
        ${forecast.length === 0 ? html`<div style="text-align:center; padding:20px; color:var(--secondary-text-color);">加载中...</div>` : ''}
        ${forecast.map(item => html`
          <div class="forecast-item">
            <div class="forecast-time">
              ${this._selectedTab === 'daily' ? this._formatDate(item.datetime) : this._formatTime(item.datetime)}
            </div>
            <div class="forecast-icon">
              <img src="${this.gethfIconurl(item.icon)}" alt="" style="width:24px; height:24px;">
              ${this._selectedTab === 'daily' ? html`<span style="font-size:12px; margin-left:8px; color:var(--secondary-text-color)">${item.text}</span>` : ''}
            </div>
            <div class="forecast-temp">
              ${item.temperature}°
              ${this._selectedTab === 'daily' ? html`<span class="forecast-low">${item.templow}°</span>` : ''}
            </div>
          </div>
        `)}
      </div>
      
      ${attr.attribution ? html`<div style="text-align:center; color:var(--secondary-text-color); font-size:10px; margin-top:16px;">${attr.attribution}</div>` : ''}
    `;
  }

  _renderAttribute(icon, label, value) {
    if (value === undefined || value === null) return '';
    return html`
      <div class="attribute-item">
        <ha-icon icon="${icon}"></ha-icon>
        <div>
          <div class="attribute-name">${label}</div>
          <div class="attribute-value">${value}</div>
        </div>
      </div>
    `;
  }
}

if (!customElements.get('qweather-more-info')) {
  customElements.define('qweather-more-info', MoreInfoWeather);
}