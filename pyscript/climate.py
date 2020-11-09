CLIMATE_TIMEOUT = 2
HVAC_MODE_TIMEOUT = CLIMATE_TIMEOUT
SET_TEMP_TIMEOUT = CLIMATE_TIMEOUT


@service
def set_hvac_mode(hvac_mode: str = None):
    """yaml
    description: Set the house HVAC mode
    fields:
        hvac_mode:
            description: Target HVAC mode to set thermostat to [heat, cool, heat_cool].
            example: heat
    """
    task.unique("set_hvac_mode", kill_me=False)
    if hvac_mode not in ["heat", "cool", "heat_cool"]:
        raise TypeError(
            f"Invalid HVAC mode '{hvac_mode}' specified. Mode must be one of [heat, cool, heat_cool]"
        )

    if climate.thermostat == hvac_mode:
        return

    num = 0

    while num <= 3 and climate.thermostat != hvac_mode:
        climate.set_hvac_mode(entity_id="climate.thermostat", hvac_mode=hvac_mode)
        num += 1
        task.sleep(HVAC_MODE_TIMEOUT)

    if climate.thermostat != hvac_mode:
        log.error("Unable to switch HVAC mode to %s", hvac_mode)


def _set_temp(temp: float):
    """Set temperature when HVAC is in heat orcool mode."""
    while float(climate.thermostat.temperature) != float(temp):
        climate.set_temperature(entity_id="climate.thermostat", temperature=float(temp))
        task.sleep(SET_TEMP_TIMEOUT)


def _set_temp_heat_cool(low: float, high: float):
    """Set low and high targets when HVAC is in heat_cool mode."""
    while float(climate.thermostat.target_temp_low) != float(low) or float(
        climate.thermostat.target_temp_high
    ) != float(high):
        climate.set_temperature(
            entity_id="climate.thermostat",
            target_temp_low=float(low),
            target_temp_high=float(high),
        )
        task.sleep(SET_TEMP_TIMEOUT)


def _set_temp_heat_cool_only_one(target: str, temp: float):
    """Set only one target temp when HVAC is in heat_cool mode."""
    while float(state.get(f"climate.thermostat.target_temp_{target}")) != float(temp):
        climate.set_temperature(
            **{"entity_id": "climate.thermostat", f"target_temp_{target}": float(temp)}
        )
        task.sleep(SET_TEMP_TIMEOUT)


@service
def set_temperature(mode: str = None, low: float = None, high: float = None):
    """yaml
    description: Set the house target low and high temperatures
    fields:
        mode:
            description: Used to determine which `input_number` target temperatures to use [home, away, night]. Takes precedence over `low` and `high`.
            example: away
        low:
            description: Target low temperature. Either this or `high` (or both) are required when `mode` isn't provided.
            example: 70
        high:
            description: Target high temperature. Either this or `low` (or both) are required when `mode` isn't provided.
            example: 75
    """
    task.unique("set_temperature", kill_me=False)
    old_hvac_mode = climate.thermostat

    if mode:
        if climate.thermostat == "heat_cool":
            _set_temp_heat_cool(
                state.get(f"input_number.{mode}_low"),
                state.get(f"input_number.{mode}_high"),
            )
        else:
            set_hvac_mode("heat_cool")
            if climate.thermostat == "heat_cool":
                _set_temp_heat_cool(
                    state.get(f"input_number.{mode}_low"),
                    state.get(f"input_number.{mode}_high"),
                )
                set_hvac_mode(old_hvac_mode)
            elif climate.thermostat == "off":
                set_hvac_mode("heat")
                for _ in range(0, 2):
                    if climate.thermostat == "heat":
                        _set_temp(state.get(f"input_number.{mode}_low"))
                        set_hvac_mode("cool")
                    else:
                        _set_temp(state.get(f"input_number.{mode}_high"))
                set_hvac_mode("off")
            else:
                for _ in range(0, 2):
                    if climate.thermostat == "heat":
                        _set_temp(state.get(f"input_number.{mode}_low"))
                        set_hvac_mode("cool")
                    else:
                        _set_temp(state.get(f"input_number.{mode}_high"))
                        set_hvac_mode("heat")

    elif low and high:
        if climate.thermostat == "heat_cool":
            _set_temp_heat_cool(low, high)
        else:
            set_hvac_mode("heat_cool")
            if climate.thermostat == "heat_cool":
                _set_temp_heat_cool(low, high)
                set_hvac_mode(old_hvac_mode)
            elif climate.thermostat == "off":
                set_hvac_mode("heat")
                for _ in range(0, 2):
                    if climate.thermostat == "heat":
                        _set_temp(low)
                        set_hvac_mode("cool")
                    else:
                        _set_temp(high)
                set_hvac_mode("off")
            else:
                for _ in range(0, 2):
                    if climate.thermostat == "heat":
                        _set_temp(low)
                        set_hvac_mode("cool")
                    else:
                        _set_temp(high)
                        set_hvac_mode("heat")

    elif low:
        if climate.thermostat == "cool":
            set_hvac_mode("heat")
            _set_temp(low)
            set_hvac_mode("cool")
        elif climate.thermostat == "heat":
            _set_temp(low)
        elif climate.thermostat == "off":
                set_hvac_mode("heat")
                _set_temp(low)
                set_hvac_mode("off")
        else:
            _set_temp_heat_cool_only_one("low", low)

    elif high:
        if climate.thermostat == "cool":
            _set_temp(high)
        elif climate.thermostat == "heat":
            set_hvac_mode("cool")
            _set_temp(high)
            set_hvac_mode("heat")
        elif climate.thermostat == "off":
                set_hvac_mode("cool")
                _set_temp(high)
                set_hvac_mode("off")
        else:
            _set_temp_heat_cool_only_one("high", high)

    else:
        raise ValueError("At least one parameter must be provided.")
