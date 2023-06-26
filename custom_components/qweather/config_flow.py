"""Config flow for Hello World integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries

DOMAIN = 'qweather'

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("name", default = "天气"): str,
    vol.Required("city", default = "117.47,30.21"): str,
    vol.Required("appkey", default = ""): str
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):        
        errors = {}

        # 如果输入内容不为空，则进行验证
        if user_input is not None:
            return self.async_create_entry(title=user_input['name'], data=user_input)
        
        # 显示表单
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )