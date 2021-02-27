from datetime import timedelta

from homeassistant.util import dt

SHERENE_BLANKET_PLUG = "sherene_electric_blanket_plug"


@service
def preheat_bed(entity_name: str = SHERENE_BLANKET_PLUG, minutes: float = 30):
    """yaml
    description: Preheats Sherene's side of the bed by turning on the electric blanket temporarily
    fields:
        entity_name:
            description: Optional entity name of switch and input_datetime that controls the heat for the bed and the time when it shuts off. Defaults to example.
            example: sherene_electric_blanket_plug
            selector:
                text:
        minutes:
            description: Number of minutes to run the electric blanket.
            example: 30
            selector:
                number:
                    min: 15
                    max: 120
    """

    switch_entity = f"switch.{entity_name}"
    input_dt_entity = f"input_datetime.{entity_name}"

    if state.get(switch_entity) is None or state.get(input_dt_entity) is None:
        raise TypeError("Entity name must exist as a switch and as an input_datetime.")

    switch_off_time = dt.now() + timedelta(minutes=minutes)
    switch.turn_on(entity_id=switch_entity)
    input_datetime.set_datetime(entity_id=input_dt_entity, datetime=switch_off_time.strftime("%Y-%m-%d %H:%M:%S"))
