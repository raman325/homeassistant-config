LOCK_TIMEOUT = 2


@service
def lock_down():
    """yaml
    name: Lock house down
    description: Lock the house down
    """
    homeassistant.turn_off(entity_id=["switch.foyer", "light.kitchen", "light.living_room"])

    if lock.front_door == "locked":
        return

    num = 0

    while num <= 3 and lock.front_door != "locked":
        lock.front_door.lock()
        num += 1
        task.sleep(LOCK_TIMEOUT)

    if lock.front_door != "locked":
        log.error("Unable to lock front door")
