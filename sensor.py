#!/usr/bin/env python 
# -*- coding:utf-8 -*-
"""
A component which allows you to parse BeeSCRM_system get electricity info

For more details about this component, please refer to the documentation at
https://github.com/zrincet/BeeSCRM_system_electricity_query/

"""
import logging
import asyncio
import voluptuous as vol
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME)
from homeassistant.const import (CONF_CODE)
from homeassistant.const import (CONF_BASE)
from requests import request
from requests.exceptions import (
    ConnectionError as ConnectError, HTTPError, Timeout)
from bs4 import BeautifulSoup
import json

__version__ = '0.1.0'
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['requests', 'beautifulsoup4']

COMPONENT_REPO = 'https://github.com/zrincet/BeeSCRM_system_electricity_query/'
SCAN_INTERVAL = timedelta(seconds=900)
CONF_OPTIONS = "options"
ATTR_UPDATE_TIME = "更新时间"
ATTR_ROOM_NAME = "房间名称"

OPTIONS = dict(ele=["BeeSCRM_ele", "剩余电量", "mdi:flash", "kW·h"],
               balance=["BeeSCRM_balance", "剩余余额", "mdi:wallet", "￥"])

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CODE): cv.string,
    vol.Required(CONF_BASE): cv.string,
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [vol.In(OPTIONS)]),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    _LOGGER.info("async_setup_platform sensor BeeSCRM_system electricity info Sensor")
    dev = []
    for option in config[CONF_OPTIONS]:
        dev.append(BeeSCRMElectricitySensor(config[CONF_BASE], config[CONF_CODE], option))

    async_add_devices(dev, True)


class BeeSCRMElectricitySensor(Entity):
    def __init__(self, baseCode, roomID, option):
        self._baseCode = baseCode
        self._roomID = roomID
        self._state = None

        self._ele = None
        self._price = None
        self._updateTime = None
        self._roomName = None

        self._object_id = OPTIONS[option][0]
        self._friendly_name = OPTIONS[option][1]
        self._icon = OPTIONS[option][2]
        self._unit_of_measurement = OPTIONS[option][3]
        self._type = option

    def update(self):
        import time
        _LOGGER.info("BeeSCRMElectricitySensor start updating data.")
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; MI 8 UD Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 XWEB/1179 MMWEBSDK/200201 Mobile Safari/537.36 MMWEBID/9993 MicroMessenger/7.0.12.1620(0x27000C35) Process/tools NetType/WIFI Language/zh_CN ABI/arm64'
        }
        url = 'http://wap.xt.beescrm.com/base/ips/getInfo/ips_id/'+self._baseCode+'/xgh/MjAxNzE1MDU0/openid/MjAxNzE1MDU0'
        data = {'room_id': self._roomID}
        try:
            response = request('POST', url, headers=header, data=data)  # 定义头信息发送请求返回response对象
            response.encoding = 'utf-8'
            re_json = json.loads(response.text)
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            time.sleep(0.01)
            _LOGGER.error("Unable to connect to Beescrm. %s", error)

        try:
            self._ele = re_json['ele']
            self._price = re_json['price']
            self._updateTime = re_json['time']
            self._roomName = re_json['room_name']

            if self._type == "ele":
                self._state = self._ele
            elif self._type == "balance":
                self._state = self._price
        except Exception as e:
            _LOGGER.error("Something wrong in Beescrm. %s", e)

    @property
    def name(self):
        return self._friendly_name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon
    @property
    def unique_id(self):
        return self._object_id

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        return {
            ATTR_UPDATE_TIME: self._updateTime,
            ATTR_ROOM_NAME: self._roomName,
        }
