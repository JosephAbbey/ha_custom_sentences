"""The custom_sentences component."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType


async def async_setup(_hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up the custom_sentences component."""
    return True
