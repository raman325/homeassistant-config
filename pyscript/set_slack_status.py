from slack import WebClient


@service
async def set_slack_status(token: str, status_text: str, status_emoji: str) -> None:
    """yaml
    description: Updates a user's Slack status.
    fields:
        token:
            description: OAuth Access Token obtained from your custom Slack app
            example: xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        status_text:
            description: The text that appears on hover. Set to empty string to clear the status.
            example: On a Call
        status_emoji:
            description: The code for the emoji that will appear next to your name. Set to empty string to clear the status.
            example: ":x:"
    """
    client = WebClient(token=token, run_async=True)
    await client.users_profile_set(
        profile={"status_text": status_text, "status_emoji": status_emoji}
    )
