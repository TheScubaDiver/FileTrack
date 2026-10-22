import glob
import os
import time
import logging
from datetime import timedelta

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify
from .const import DOMAIN, CONF_FOLDER_PATHS, CONF_FILTER, CONF_SORT, CONF_RECURSIVE, CONF_UNIQUE_ID, CONF_MAX_AGE, DEFAULT_FILTER, DEFAULT_SORT, DEFAULT_RECURSIVE, DEFAULT_MAX_AGE, SORT_OPTIONS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("name"): cv.string,
    vol.Required(CONF_FOLDER_PATHS): cv.string,
    vol.Optional(CONF_FILTER, default=DEFAULT_FILTER): cv.string,
    vol.Optional(CONF_SORT, default=DEFAULT_SORT): vol.In(SORT_OPTIONS),
    vol.Optional(CONF_RECURSIVE, default=DEFAULT_RECURSIVE): cv.boolean,
    vol.Optional(CONF_MAX_AGE, default=DEFAULT_MAX_AGE): cv.positive_int,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})


def get_files_list(folder_path, filter_term, sort, recursive):
    # `glob.glob(..., recursive=True)` only walks subdirs when the pattern
    # itself contains `**`. Without it the recursive flag is a no-op —
    # which is the bug behind issue #5. When the user (or YAML) asks for
    # recursive search, expand the pattern to `**/<filter>` so every
    # subdir is walked. The recursive flag still controls glob's
    # interpretation of `**`.
    if recursive:
        query = os.path.join(folder_path, "**", filter_term)
    else:
        query = os.path.join(folder_path, filter_term)
    files = glob.glob(query, recursive=recursive)
    # `*` (and `**`) also matches directory entries. Filter those out so
    # the sensor only reports actual files — otherwise the size sum and
    # file count include directory bytes / inodes too.
    files = [f for f in files if os.path.isfile(f)]
    if sort == "name":
        return sorted(files)
    elif sort == "size":
        return sorted(files, key=os.path.getsize)
    else:  # date
        return sorted(files, key=os.path.getmtime, reverse=True)

def cleanup_old_files(folder_path, filter_term, recursive, max_age_days):
    """Delete files older than max_age_days. 0 disables cleanup."""
    if not max_age_days or max_age_days <= 0:
        return
    cutoff = time.time() - max_age_days * 86400
    files = get_files_list(folder_path, filter_term, "date", recursive)
    for f in files:
        try:
            if os.path.getmtime(f) < cutoff:
                os.remove(f)
                _LOGGER.debug("FileTrack: deleted old file %s", f)
        except OSError as err:
            _LOGGER.warning("FileTrack: could not delete %s: %s", f, err)


async def async_setup_entry(hass, entry, async_add_entities):
    """Laad sensoren vanuit de opgeslagen configuratie."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["add_entities"] = async_add_entities
    stored = hass.data[DOMAIN].get("stored", {})
    yaml_config = hass.data[DOMAIN].get("yaml_sensors", [])
    entities = []
    
    for sc in stored.get("sensors", []):
        unique_id = f"filetrack_{sc['id']}"
        _LOGGER.debug("FileTrack: Preparing UI sensor: %s (unique_id: %s)", sc["name"], unique_id)
        entities.append(FileTrackSensor(
            sc[CONF_FOLDER_PATHS],
            sc["name"],
            sc.get(CONF_FILTER, DEFAULT_FILTER),
            sc.get(CONF_SORT, DEFAULT_SORT),
            sc.get(CONF_RECURSIVE, DEFAULT_RECURSIVE),
            f"filetrack_{sc['id']}",
            config_entry=entry,
            max_age=sc.get(CONF_MAX_AGE, DEFAULT_MAX_AGE),
        ))
    for yc in yaml_config:
        name = yc["name"]
        yaml_unique_id = yc.get(CONF_UNIQUE_ID)
        if yaml_unique_id:
            unique_id = yaml_unique_id
        else:
            unique_id = slugify(name)
        _LOGGER.debug("FileTrack: Preparing YAML sensor: %s (unique_id: %s)", name, unique_id)
        entities.append(FileTrackSensor(
            yc[CONF_FOLDER_PATHS],
            name,
            yc.get(CONF_FILTER, DEFAULT_FILTER),
            yc.get(CONF_SORT, DEFAULT_SORT),
            yc.get(CONF_RECURSIVE, DEFAULT_RECURSIVE),
            unique_id,
            config_entry=entry,
            max_age=yc.get(CONF_MAX_AGE, DEFAULT_MAX_AGE),
        ))
    if entities:
        async_add_entities(entities, True)


class FileTrackSensor(SensorEntity):
    """De sensor definitie."""
    _attr_icon = "mdi:folder"
    _attr_native_unit_of_measurement = "MB"

    def __init__(self, folder_path, name, filter_term, sort, recursive, entry_id, config_entry=None, max_age=0):
        self._attr_name = name
        self._attr_unique_id = entry_id
        self._attr_suggested_object_id = slugify(name)
        self._max_age = max_age

        # Keep existing sensor_id for UI and YAML
        if entry_id.startswith("filetrack_"):
            self._attr_has_entity_name = True
        else:
            self.entity_id = f"sensor.{slugify(name)}"
            self._attr_has_entity_name = False
            
        self._attr_config_entry_id = getattr(config_entry, 'entry_id', None)
        self._config_entry = config_entry    
        self._folder_path = os.path.join(folder_path, "")
        self._filter_term = filter_term
        self._sort = sort
        self._recursive = recursive
        self._state = 0
        self._attributes = {}

    def update(self):
        """Haal de nieuwe data op."""
        cleanup_old_files(self._folder_path, self._filter_term, self._recursive, self._max_age)
        files_list = get_files_list(self._folder_path, self._filter_term, self._sort, self._recursive)
        total_size = sum(os.path.getsize(f) for f in files_list if os.path.isfile(f))

        self._state = round(total_size / 1e6, 2)
        self._attributes = {
            "path": self._folder_path,
            "filter": self._filter_term,
            "number_of_files": len(files_list),
            "fileList": files_list,
            "sort": self._sort,
        }

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes
    
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "filetrack_service_device")},
        }
