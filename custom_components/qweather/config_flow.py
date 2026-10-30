"""Adds config flow for Qweather."""
import logging
import requests
import json
import time
import jwt
import re
import voluptuous as vol
from collections import OrderedDict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_API_KEY, CONF_NAME

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
    CONF_DEV_ID,
)

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class QweatherlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return QweatherOptionsFlow(config_entry)

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.data_schema_step1 = {}
        self._generated_private_key = None
        self._generated_public_key = None 

    def _generate_key_pair(self):
        try:
            private_key = ed25519.Ed25519PrivateKey.generate()
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_key = private_key.public_key()
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return private_bytes.decode('utf-8'), public_bytes.decode('utf-8')
        except Exception as e:
            _LOGGER.error("密钥生成失败: %s", e)
            return None, None

    def generate_jwt(self, pid, kid, private_key_pem, iss=None):
        try:
            # Docs require iss (developer ID), sub (project ID), iat, exp.
            # https://dev.qweather.com/docs/configuration/authentication/
            if not iss:
                _LOGGER.error("JWT 缺少开发者 ID (iss)")
                return None
            payload = {
                'iat': int(time.time()) - 30,
                'exp': int(time.time()) + 900,
                'sub': pid,
                'iss': iss,
            }
            headers = {'kid': kid}
            return jwt.encode(
                payload,
                private_key_pem,
                algorithm='EdDSA',
                headers=headers
            )
        except Exception as e:
            _LOGGER.error("JWT 生成失败: %s", e)
            return None
            
    def get_data(self, url, headers):
        try:
            response = requests.get(url, headers=headers, timeout=(3, 5))
            if response.status_code in [401, 403]:
                return {"code": str(response.status_code)}
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectTimeout:
            return {"code": "timeout"}
        except requests.exceptions.ReadTimeout:
            return {"code": "timeout"}
        except requests.exceptions.RequestException as e:
            _LOGGER.error("API请求失败: %s", e)
            return None

    async def async_step_user(self, user_input=None):
        self._errors = {}
        
        if user_input is not None:
            self.data_schema_step1 = user_input
            
            if user_input.get(CONF_USE_TOKEN):
                return await self.async_step_jwt_setup()
            else:
                return await self._verify_and_create_entry(
                    user_input.get(CONF_API_KEY, ""), 
                    is_jwt=False
                )

        return self._show_step_user_form(user_input)

    def _show_step_user_form(self, user_input=None):
        default_location = f"{round(self.hass.config.longitude, 2)},{round(self.hass.config.latitude, 2)}"
        if user_input is None:
            user_input = {}

        schema = OrderedDict()
        schema[vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "api.qweather.com"))] = str
        schema[vol.Required(CONF_USE_TOKEN, default=user_input.get(CONF_USE_TOKEN, False))] = bool
        schema[vol.Optional(CONF_LOCATION, default=user_input.get(CONF_LOCATION, default_location))] = str
        schema[vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "和风天气"))] = str
        schema[vol.Optional(CONF_API_KEY, default=user_input.get(CONF_API_KEY, ""))] = str

        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema(schema), 
            errors=self._errors
        )

    async def async_step_jwt_setup(self, user_input=None):
        self._errors = {}

        if self._generated_private_key is None:
            private_key, public_key = await self.hass.async_add_executor_job(self._generate_key_pair)
            if not private_key:
                return self.async_abort(reason="key_generation_failed")
            self._generated_private_key = private_key
            self._generated_public_key = public_key

        if user_input is not None:
            final_data = {**self.data_schema_step1, **user_input}
            provided_key = (user_input.get(CONF_PRIVATE_KEY) or "").strip()
            if provided_key:
                final_data[CONF_PRIVATE_KEY] = provided_key
            else:
                final_data[CONF_PRIVATE_KEY] = self._generated_private_key
            
            token = self.generate_jwt(
                user_input[CONF_PROJECT_ID],
                user_input[CONF_KEY_ID],
                final_data[CONF_PRIVATE_KEY],
                user_input.get(CONF_DEV_ID),
            )
            
            if token:
                return await self._verify_and_create_entry(token, is_jwt=True, config_data=final_data)
            else:
                self._errors["base"] = "jwt_generation_failed"

        return self._show_step_jwt_form(user_input)

    def _show_step_jwt_form(self, user_input=None):
        if user_input is None:
            user_input = {}
            
        public_key_display = f"```\n{self._generated_public_key}\n```"
        
        schema = OrderedDict()
        schema[vol.Required(CONF_PROJECT_ID, default=user_input.get(CONF_PROJECT_ID, ""))] = str
        schema[vol.Required(CONF_KEY_ID, default=user_input.get(CONF_KEY_ID, ""))] = str
        schema[vol.Required(CONF_DEV_ID, default=user_input.get(CONF_DEV_ID, ""))] = str
        schema[vol.Optional(CONF_PRIVATE_KEY, default=user_input.get(CONF_PRIVATE_KEY, ""))] = str

        return self.async_show_form(
            step_id="jwt_setup",
            data_schema=vol.Schema(schema),
            errors=self._errors,
            description_placeholders={
                "public_key": public_key_display
            }
        )

    async def _verify_and_create_entry(self, credential, is_jwt=False, config_data=None):

        if config_data is None:
            data = self.data_schema_step1
        else:
            data = config_data

        location = data.get(CONF_LOCATION, "")
        
        if is_jwt:
            headers = {"Authorization": f"Bearer {credential}"}
        else:
            if not credential:
                self._errors["base"] = "api_key_missing"
                return self._show_step_user_form(data)
            data[CONF_API_KEY] = credential
            headers = {"X-QW-Api-Key": credential}

        if not re.match(r"^-?\d+\.?\d*,-?\d+\.?\d*$", location.replace(" ", "")):
            # Geo must use the project API Host; legacy geoapi.qweather.com returns 404 for JWT.
            geo_url = f"https://{data[CONF_HOST]}/geo/v2/city/lookup?location={location}&lang=zh"
            geo_data = await self.hass.async_add_executor_job(self.get_data, geo_url, headers)
            
            if geo_data and geo_data.get('code') == "200" and geo_data.get('location'):
                loc_info = geo_data['location'][0]
                new_location = f"{loc_info['lon']},{loc_info['lat']}"
                data[CONF_LOCATION] = new_location
                _LOGGER.info("位置已自动转换: %s -> %s", location, new_location)
            else:
                error_code = geo_data.get('code') if geo_data else 'unknown'
                if error_code in ["401", "403"]:
                    self._errors["base"] = "auth_failed"
                elif error_code == "timeout":
                    self._errors["base"] = "connect_timeout"
                else:
                    self._errors["base"] = "location_not_found"

                return self._show_step_jwt_form(data) if is_jwt else self._show_step_user_form(data)

        test_url = f"https://{data[CONF_HOST]}/v7/weather/now?location={data[CONF_LOCATION]}&lang=zh"
        redata = await self.hass.async_add_executor_job(self.get_data, test_url, headers)

        if not redata or redata.get('code') != "200":
            code = redata.get('code', 'connect_fail') if redata else 'connect_fail'
            
            if code in ["401", "403"]:
                self._errors["base"] = "auth_failed"
            elif code == "timeout":
                self._errors["base"] = "connect_timeout"
            elif code == "400": 
                self._errors["base"] = "invalid_params" 
            else:
                self._errors["base"] = f"api_error_{code}"
            
            return self._show_step_jwt_form(data) if is_jwt else self._show_step_user_form(data)
        
        await self.async_set_unique_id(f"qw_{data[CONF_LOCATION].replace(',', '_')}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=data[CONF_NAME], data=data)

    async def async_step_import(self, user_input):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="configuration.yaml", data={})


class QweatherOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
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
                    ): vol.All(vol.Coerce(int), vol.Range(min=24, max=168)),
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
