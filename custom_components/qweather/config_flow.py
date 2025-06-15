
"""Adds config flow for Qweather."""
import logging
import requests
import json
import sys
import time
import jwt

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_API_KEY, CONF_NAME

from collections import OrderedDict
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
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
    CONF_PROJECT_ID,
    CONF_KEY_ID,
    CONF_PRIVATE_KEY,
    )
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class QweatherlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return QweatherOptionsFlow(config_entry)

    def __init__(self):
        """Initialize."""
        self._errors = {}
    
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
            
    def get_data(self, url, config):
        headers = {}
        if config[CONF_USE_TOKEN]:
            jwt_token = self.generate_jwt(config)
            if not jwt_token:
                return None
            headers = {"Authorization": f"Bearer {jwt_token}"}
        else:
            headers = {"X-QW-Api-Key": config[CONF_API_KEY]}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error("请求失败: %s", e)
            return None

    async def async_step_user(self, user_input={}):
        self._errors = {}
        if user_input is not None:
            # Check if entered host is already in HomeAssistant
            existing = await self._check_existing(user_input[CONF_NAME])
            if existing:
                return self.async_abort(reason="already_configured")
                
            if user_input[CONF_USE_TOKEN]:
                missing = []
                if not user_input.get(CONF_PROJECT_ID):
                    missing.append("项目ID")
                if not user_input.get(CONF_KEY_ID):
                    missing.append("密钥ID")
                if not user_input.get(CONF_PRIVATE_KEY):
                    missing.append("私钥")
                
                if missing:
                    self._errors["base"] = f"缺少JWT参数: {', '.join(missing)}"
                    return await self._show_config_form(user_input)

            url = f"https://{user_input[CONF_HOST]}/v7/weather/now?location={user_input[CONF_LOCATION]}&lang=zh&unit=m"
            
            # 获取天气数据
            redata = await self.hass.async_add_executor_job(
                self.get_data, url, user_input
            )
            
            if not redata or redata.get('code') != "200":
                self._errors["base"] = "communication"
                _LOGGER.debug("API响应: %s", redata)
            else:
                await self.async_set_unique_id(f"qweather_{user_input['location'].replace(".","_")}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input=None):
        if user_input is None:
            user_input = {}

        base_schema = {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "api.qweather.com")): str,
            vol.Required(CONF_USE_TOKEN, default=user_input.get(CONF_USE_TOKEN, False)): bool,
            vol.Optional(CONF_LOCATION, 
                default=user_input.get(CONF_LOCATION, 
                    f"{round(self.hass.config.longitude,2)},{round(self.hass.config.latitude,2)}")
            ): str,
            vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "天气")): str,
        }
        

        if user_input.get(CONF_USE_TOKEN, False):
            token_schema = {
                vol.Required(CONF_PROJECT_ID, default=user_input.get(CONF_PROJECT_ID, "")): str,
                vol.Required(CONF_KEY_ID, default=user_input.get(CONF_KEY_ID, "")): str,
                vol.Required(CONF_PRIVATE_KEY, default=user_input.get(CONF_PRIVATE_KEY, "")): str,
            }
            data_schema = {**base_schema, **token_schema}
        else:
            api_key_schema = {
                vol.Required(CONF_API_KEY, default=user_input.get(CONF_API_KEY, "请修改，使用JWT模式时可忽略")): str,
            }
            data_schema = {**base_schema, **api_key_schema}

        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema(data_schema), 
            errors=self._errors
        )

    async def async_step_import(self, user_input):
        """Import a config entry.

        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    async def _check_existing(self, host):
        for entry in self._async_current_entries():
            if host == entry.data.get(CONF_NAME):
                return True

class QweatherOptionsFlow(config_entries.OptionsFlow):
    """Config flow options for Qweather."""

    def __init__(self, config_entry):
        """Initialize Qweather options flow."""
        self._config = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._config.update(user_input)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=self._config
            )
            await self.hass.config_entries.async_reload(self._config_entry_id)
            return self.async_create_entry(title="", data=self._config)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, 10),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
                    vol.Optional(
                        CONF_DAILYSTEPS,
                        default=self.config_entry.options.get(CONF_DAILYSTEPS, 7),
                    ): vol.All(vol.Coerce(int), vol.Range(min=3, max=15)),
                    vol.Optional(
                        CONF_HOURLYSTEPS,
                        default=self.config_entry.options.get(CONF_HOURLYSTEPS, 24),
                    ): vol.All(vol.Coerce(int), vol.Range(min=24, max=72)),
                    vol.Optional(
                        CONF_ALERT,
                        default=self.config_entry.options.get(CONF_ALERT, True),
                    ): bool,
                    vol.Optional(
                        CONF_LIFEINDEX,
                        default=self.config_entry.options.get(CONF_LIFEINDEX, True),
                    ): bool,
                    vol.Optional(
                        CONF_GIRD,
                        default=self.config_entry.options.get(CONF_GIRD, False),
                    ): bool,
                    vol.Optional(
                        CONF_CUSTOM_UI,
                        default=self.config_entry.options.get(CONF_CUSTOM_UI, False),
                    ): bool,
                }
            ),
        )

