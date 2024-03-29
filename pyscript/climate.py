from homeassistant.components.climate import (
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
)

MODES = [HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF]

CLIMATE_TIMEOUT = 10
HVAC_MODE_TIMEOUT = CLIMATE_TIMEOUT
SET_TEMP_TIMEOUT = CLIMATE_TIMEOUT


@service
def set_hvac_mode(hvac_mode: str):
    """yaml
    name: Set house HVAC mode
    description: Set the house HVAC mode
    fields:
        hvac_mode:
            description: Target HVAC mode to set thermostat to [heat, cool, heat_cool, off].
            example: heat
            required: true
            selector:
                select:
                    options:
                        - heat
                        - cool
                        - heat_cool
                        - off
    """
    task.unique("set_hvac_mode", kill_me=False)
    if hvac_mode not in MODES:
        raise TypeError(
            f"Invalid HVAC mode '{hvac_mode}' specified. Mode must be one of {MODES}"
        )

    if climate.thermostat == hvac_mode:
        return

    num = 0

    while num <= 3 and climate.thermostat != hvac_mode:
        climate.thermostat.set_hvac_mode(hvac_mode=hvac_mode)
        num += 1
        task.sleep(HVAC_MODE_TIMEOUT)

    if climate.thermostat != hvac_mode:
        log.error("Unable to switch HVAC mode to %s", hvac_mode)


def _set_temp(temp: float):
    """Set temperature when HVAC is in heat orcool mode."""
    while float(climate.thermostat.temperature) != float(temp):
        climate.thermostat.set_temperature(temperature=float(temp))
        task.sleep(SET_TEMP_TIMEOUT)


def _set_temp_heat_cool(low: float, high: float):
    """Set low and high targets when HVAC is in heat_cool mode."""
    while float(climate.thermostat.target_temp_low) != float(low) or float(
        climate.thermostat.target_temp_high
    ) != float(high):
        climate.thermostat.set_temperature(
            target_temp_low=float(low),
            target_temp_high=float(high),
        )
        task.sleep(SET_TEMP_TIMEOUT)


def _set_temp_heat_cool_only_one(target: str, temp: float):
    """Set only one target temp when HVAC is in heat_cool mode."""
    while float(state.get(f"climate.thermostat.target_temp_{target}")) != float(temp):
        climate.thermostat.set_temperature(**{f"target_temp_{target}": float(temp)})
        task.sleep(SET_TEMP_TIMEOUT)


@service
def set_temperature(mode: str = None, low: float = None, high: float = None):
    """yaml
    name: Set house temperature
    description: Set the house target low and high temperatures
    fields:
        mode:
            description: Used to determine which `input_number` target temperatures to use [home, away, night]. Takes precedence over `low` and `high`.
            example: away
            selector:
                select:
                    options:
                        - home
                        - away
                        - night
        low:
            description: Target low temperature. Either this or `high` (or both) are required when `mode` isn't provided.
            example: 70
            selector:
                number:
                    min: 60
                    max: 80
        high:
            description: Target high temperature. Either this or `low` (or both) are required when `mode` isn't provided.
            example: 75
            selector:
                number:
                    min: 60
                    max: 80
    """
    task.unique("set_temperature", kill_me=False)
    old_hvac_mode = climate.thermostat

    # Hack to fix thermostat if it isn't reporting properly
    try:
        if old_hvac_mode == HVAC_MODE_HEAT_COOL:
            _ = climate.thermostat.target_temp_high
            _ = climate.thermostat.target_temp_low
        elif old_hvac_mode in (HVAC_MODE_COOL, HVAC_MODE_HEAT):
            _ = climate.thermostat.temperature
    except AttributeError:
        set_hvac_mode(HVAC_MODE_OFF)
        set_hvac_mode(old_hvac_mode)

    if mode:
        if climate.thermostat == HVAC_MODE_HEAT_COOL:
            _set_temp_heat_cool(
                state.get(f"input_number.{mode}_low"),
                state.get(f"input_number.{mode}_high"),
            )
        else:
            if climate.thermostat == HVAC_MODE_OFF:
                set_hvac_mode(HVAC_MODE_HEAT)
                for _ in range(0, 2):
                    if climate.thermostat == HVAC_MODE_HEAT:
                        _set_temp(state.get(f"input_number.{mode}_low"))
                        set_hvac_mode(HVAC_MODE_COOL)
                    else:
                        _set_temp(state.get(f"input_number.{mode}_high"))
                set_hvac_mode(HVAC_MODE_OFF)
            else:
                current_mode, current_target, other_mode, other_target = (
                    (HVAC_MODE_HEAT, "low", HVAC_MODE_COOL, "high")
                    if climate.thermostat == HVAC_MODE_HEAT
                    else (HVAC_MODE_COOL, "high", HVAC_MODE_HEAT, "low")
                )
                _set_temp(state.get(f"input_number.{mode}_{current_target}"))
                set_hvac_mode(other_mode)
                _set_temp(state.get(f"input_number.{mode}_{other_target}"))
                set_hvac_mode(current_mode)
                # if other_mode == HVAC_MODE_COOL and float(
                #     climate.thermostat.current_temperature
                # ) <= float(state.get(f"input_number.{mode}_low")):
                #     set_hvac_mode(HVAC_MODE_HEAT)
                # elif other_mode == HVAC_MODE_HEAT and float(
                #     climate.thermostat.current_temperature
                # ) >= float(state.get(f"input_number.{mode}_high")):
                #     set_hvac_mode(HVAC_MODE_COOL)
                # else:
                #     log.info("Switched HVAC modes because we are way off target.")

    elif low and high:
        if climate.thermostat == HVAC_MODE_HEAT_COOL:
            _set_temp_heat_cool(low, high)
        else:
            if climate.thermostat == HVAC_MODE_OFF:
                set_hvac_mode(HVAC_MODE_HEAT)
                for _ in range(0, 2):
                    if climate.thermostat == HVAC_MODE_HEAT:
                        _set_temp(low)
                        set_hvac_mode(HVAC_MODE_COOL)
                    else:
                        _set_temp(high)
                set_hvac_mode(HVAC_MODE_OFF)
            else:
                old_hvac_mode = climate.thermostat
                current_mode, current_target, other_mode, other_target = (
                    (HVAC_MODE_HEAT, low, HVAC_MODE_COOL, high)
                    if climate.thermostat == HVAC_MODE_HEAT
                    else (HVAC_MODE_COOL, high, HVAC_MODE_HEAT, low)
                )
                _set_temp(current_target)
                set_hvac_mode(other_mode)
                _set_temp(other_target)
                set_hvac_mode(current_mode)
                # if other_mode == HVAC_MODE_COOL and float(
                #     climate.thermostat.current_temperature
                # ) <= float(low):
                #     set_hvac_mode(HVAC_MODE_HEAT)
                # elif other_mode == HVAC_MODE_HEAT and float(
                #     climate.thermostat.current_temperature
                # ) >= float(high):
                #     set_hvac_mode(HVAC_MODE_COOL)
                # else:
                #     log.info("Switched HVAC modes because we are way off target.")

    elif low:
        if climate.thermostat == HVAC_MODE_COOL:
            set_hvac_mode(HVAC_MODE_HEAT)
            _set_temp(low)
            set_hvac_mode(HVAC_MODE_COOL)
            # # Only switch back to cool if temperature is above the low point
            # if float(climate.thermostat.current_temperature) > float(low):
            #     set_hvac_mode(HVAC_MODE_COOL)
            # else:
            #     log.info("Switched HVAC modes because we are way off target.")
        elif climate.thermostat == HVAC_MODE_HEAT:
            _set_temp(low)
        elif climate.thermostat == HVAC_MODE_OFF:
            set_hvac_mode(HVAC_MODE_HEAT)
            _set_temp(low)
            set_hvac_mode(HVAC_MODE_OFF)
        else:
            _set_temp_heat_cool_only_one("low", low)

    elif high:
        if climate.thermostat == HVAC_MODE_COOL:
            _set_temp(high)
        elif climate.thermostat == HVAC_MODE_HEAT:
            set_hvac_mode(HVAC_MODE_COOL)
            _set_temp(high)
            set_hvac_mode(HVAC_MODE_HEAT)
            # # Only switch back to heat if temperature is below the high point
            # if float(climate.thermostat.current_temperature) < float(high):
            #     set_hvac_mode(HVAC_MODE_HEAT)
            # else:
            #     log.info("Switched HVAC modes because we are way off target.")
        elif climate.thermostat == HVAC_MODE_OFF:
            set_hvac_mode(HVAC_MODE_COOL)
            _set_temp(high)
            set_hvac_mode(HVAC_MODE_OFF)
        else:
            _set_temp_heat_cool_only_one("high", high)
