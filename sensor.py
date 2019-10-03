import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD)
import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.entity import Entity

from landroidcc import Landroid

import voluptuous as vol

DOMAIN = "worxlandroidcloud"

DEPENDENCIES = ['landroidcc']

_LOGGER = logging.getLogger(__name__)


_LOGGER.warning("loaded sensor.py")

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.warning("About to initialize Landroid")
    mower = Landroid()
    mower.connect(config.get(CONF_USERNAME),
                  config.get(CONF_PASSWORD))
    _LOGGER.warning("Connected")
    component = LandroidCloudSensor(mower)
    hass.services.register(DOMAIN, 'start', component.start_mowing)
    hass.services.register(DOMAIN, 'stop', component.stop_mowing)
    hass.services.register(DOMAIN, 'home', component.go_home)
    add_devices([component])


class LandroidCloudSensor(Entity):
    """Representation of a Sensor."""

    _mower = None

    def __init__(self, mower: Landroid):
        """Initialize the sensor."""
        self._mower = mower
        self._mower_state = mower.get_status()

        def status_callback(state):
            self._setState(state)

        self._mower.set_statuscallback(status_callback)
        _LOGGER.warning(self._mower_state)

    def _setState(self, state):
        logging.warning("incoming state update")
        self._mower_state = state
        self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        mower_name = self._mower._api_product_items[0]["name"]
        return mower_name

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self._mower_state:
            return "N/A"

        return self._mower_state._state

    @property
    def state_attributes(self):
        if not self._mower_state:
            return {}

        return {"State": self._mower_state._state,
                "Error": self._mower_state._error,
                "Battery (%)": self._mower_state._battery.percent,
                "Battery (V)": self._mower_state._battery.volts,
                "Distance (km)": self._mower_state._statistics.distance / 1000,
                "Operation time (hours)": int(self._mower_state._statistics.running / 60),
                "Mowing time (hours)": int(self._mower_state._statistics.mowing / 60),
                "Last Update": self._mower_state._updated
                }

    def start_mowing(self, call):
        self._mower.start()

    def stop_mowing(self, call):
        self._mower.pause()

    def go_home(self, call):
        self._mower.go_home()
