from slack import WebClient


@service
async def set_slack_status(token: str, status_text: str = None, status_emoji: str = None) -> None:
    """yaml
    name: Update Slack status
    description: Updates a user's Slack status.
    fields:
        token:
            description: OAuth Access Token obtained from your custom Slack app
            example: xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            required: true
            selector:
                text:
        status_text:
            description: The text that appears on hover. Set to empty string to clear the status.
            example: On a Call
            selector:
                text:
        status_emoji:
            description: The code for the emoji that will appear next to your name. Set to empty string to clear the status.
            example: ":x:"
            selector:
                text:
    """

    client = WebClient(token=token, run_async=True)
    data = {"status_text": status_text, "status_emoji": status_emoji}
    await client.users_profile_set(
        profile={key: value for key, value in data.items() if value is not None}
    )
