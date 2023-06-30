console.info("%c  WEATHER CARD Extends \n%c  Version 2023.6.26 ",
"color: orange; font-weight: bold; background: black", 
"color: white; font-weight: bold; background: dimgray");

import {
LitElement,
html,
css
} from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";


class MoreInfoWeather extends LitElement {
	static get properties() {
	  return {
		hass: Object,
		stateObj: Object,
	  };
	}

	constructor() {
	  super();
	  this.cardinalDirections = [
		"N",
		"NNE",
		"NE",
		"ENE",
		"E",
		"ESE",
		"SE",
		"SSE",
		"S",
		"SSW",
		"SW",
		"WSW",
		"W",
		"WNW",
		"NW",
		"NNW",
		"N",
	  ];
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
	ll(str) {
	  if (locale[this.lang] === undefined)
		return locale.en[str];
	  return locale[this.lang][str];
	}
	computeDate(data) {
	  const date = new Date(data);
	  return date.toLocaleDateString(this.hass.language, {
		weekday: "long",
		month: "short",
		day: "numeric",
	  });
	}

	computeDateTime(data) {
	  const date = new Date(data);
	  return date.toLocaleDateString(this.hass.language, {
		weekday: "long",
		hour: "numeric",
	  });
	}

	getUnit(measure) {
	  const lengthUnit = this.hass.config.unit_system.length || "";
	  switch (measure) {
		case "air_pressure":
		  return lengthUnit === "km" ? "hPa" : "inHg";
		case "length":
		  return lengthUnit;
		case "precipitation":
		  return lengthUnit === "km" ? "mm" : "in";
		default:
		  return this.hass.config.unit_system[measure] || "";
	  }
	}

	windBearingToText(degree) {
	  const degreenum = parseInt(degree);
	  if (isFinite(degreenum)) {
		return this.cardinalDirections[(((degreenum + 11.25) / 22.5) | 0) % 16];
	  }
	  return degree;
	}

	getWind(speed, bearing, localize) {
	  if (bearing != null) {
		const cardinalDirection = this.windBearingToText(bearing);
		return `${speed} ${this.getUnit("length")}/h (${localize(
		  `ui.card.weather.cardinal_direction.${cardinalDirection.toLowerCase()}`
		) || cardinalDirection})`;
	  }
	  return `${speed} ${this.getUnit("length")}/h`;
	}

	getWeatherIcon(condition) {
	  return this.weatherIcons[condition];
	}

	_showValue(item) {
	  return typeof item !== "undefined" && item !== null;
	}
	
	render() {
		return html`
		<style>
        ha-icon {
          color: var(--paper-item-icon-color);
        }
        .section {
          margin: 16px 0 8px 0;
          font-size: 1.2em;
        }

        .flex {
          display: flex;
          height: 32px;
          align-items: center;
        }
        .suggestion_brf {
          color: #44739e;
          justify-content: space-between;
          display: flex;
          align-items: center;
          margin-top: 5px;
        }
        .suggestion_txt {
          margin-left:10px;
        }
        .main {
          flex: 1;
          margin-left: 24px;
        }

        .temp,
        .templow {
          min-width: 48px;
          text-align: right;
        }

        .templow {
          margin: 0 16px;
          color: var(--secondary-text-color);
        }

        .attribution {
          color: var(--secondary-text-color);
          text-align: center;
        }
      </style>
		  <div class="flex">
			<ha-icon icon="hass:thermometer"></ha-icon>
			<div class="main">
			  温度
			</div>
			<div>
			  ${this.stateObj.attributes.temperature} ${this.stateObj.attributes.temperature_unit}
			</div>
		  </div>
		  ${this._showValue(this.stateObj.attributes.pressure) ? html`
			<div class="flex">
			  <ha-icon icon="hass:gauge"></ha-icon>
			  <div class="main">
				气压
			  </div>
			  <div>
				${this.stateObj.attributes.pressure} ${this.getUnit('air_pressure')}
			  </div>
			</div>
		  ` : ''}
		  ${this._showValue(this.stateObj.attributes.humidity) ? html`
			<div class="flex">
			  <ha-icon icon="hass:water-percent"></ha-icon>
			  <div class="main">
				湿度
			  </div>
			  <div>${this.stateObj.attributes.humidity} %</div>
			</div>
		  ` : ''}
		  ${this._showValue(this.stateObj.attributes.wind_speed) ? html`
			<div class="flex">
			  <ha-icon icon="hass:weather-windy"></ha-icon>
			  <div class="main">
				风速
			  </div>
			  <div>
				${this.stateObj.attributes.wind_speed} ${this.stateObj.attributes.wind_speed_unit}
			  </div>
			</div>
		  ` : ''}
		  ${this._showValue(this.stateObj.attributes.visibility) ? html`
			<div class="flex">
			  <ha-icon icon="hass:eye"></ha-icon>
			  <div class="main">
				能见度
			  </div>
			  <div>${this.stateObj.attributes.visibility} ${this.stateObj.attributes.visibility_unit}</div>
			</div>
		  ` : ''}
		  ${this.stateObj.attributes.warning ? html`
			<div class="section">气象预警:</div>
			${this.stateObj.attributes.warning.map(
				(item) => html`
				  <div class="suggestion_brf">
					<div>-&nbsp;&nbsp;${item.title}</div>
					<div>${item.typeName}</div>
				  </div>
			  <div class="suggestion_txt">${item.text}</div>
				`,
			  )}	
		  ` : ''}
		  ${this.stateObj.attributes.suggestion ? html`
			<div class="section">生活指数:</div>
			${this.stateObj.attributes.suggestion.map(
				(item) => html`
				  <div class="suggestion_brf">
					<div>-&nbsp;&nbsp;${item.title_cn}</div>
					<div>${item.brf}</div>
				  </div>
			  <div class="suggestion_txt">${item.txt}</div>
				`,
			  )}	
		  ` : ''}
		  ${this.stateObj.attributes.forecast ? html`
			<div class="section">天气预报:</div>
			${this.stateObj.attributes.forecast.map(
				(item) => html`
				  <div class="flex">
					${this._showValue(item.condition)
					  ? html`<ha-icon icon="${this.getWeatherIcon(item.condition)}"></ha-icon>`
					  : null}
					${!this._showValue(item.templow)
					  ? html`<div class="main">${this.computeDateTime(item.datetime)}</div>`
					  : html`
						  <div class="main">${this.computeDate(item.datetime)}</div>
						  <div class="templow">${item.templow} ${this.stateObj.attributes.temperature_unit}</div>
						`}
					<div class="temp">${item.temperature} ${this.stateObj.attributes.temperature_unit}</div>
				  </div>
				`,
			  )}
		  ` : ''}
		  ${this.stateObj.attributes.attribution ? html`
			<div class="attribution">${this.stateObj.attributes.attribution}</div>
		  ` : ''}
		`;
	  };
	}

customElements.define("qweather-more-info", MoreInfoWeather);