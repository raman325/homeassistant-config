from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, STATE_ON

SHERENE_BLANKET_PLUG = "switch.sherene_electric_blanket_plug"


@service
def preheat_bed(entity_id: str = SHERENE_BLANKET_PLUG, minutes: float = 30):
    """yaml
    description: Preheats Sherene's side of the bed by turning on the electric blanket temporarily
    fields:
        entity_id:
            description: Switch that controls the heat for the bed
            example: switch.sherene_electric_blanket_plug
        minutes:
            description: Number of minutes to run the electric blanket.
            example: 30
    """

    if entity_id.split(".")[0] != "switch":
        raise TypeError("Entity must be a switch.")

    switch.turn_on(entity_id=entity_id)
    task.sleep(minutes * 60)
    switch.turn_off(entity_id=entity_id)


@event_trigger(EVENT_HOMEASSISTANT_STARTED)
def turnoff_preheat_bed_on_restart():
    """Turns blanket off if HA was restarted."""
    entity_id = SHERENE_BLANKET_PLUG
    if state.get(entity_id) == STATE_ON:
        switch.turn_off(entity_id=entity_id)
