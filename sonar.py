from typing import Dict, Any
from utils.slack_utils import is_user_authorized, is_channel_allowed
from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient


async def handle_sonar(client: WebClient, ack: Ack, body: Dict[str, Any], context: BoltContext) -> None:
    await ack()

    if not is_channel_allowed(body["channel_id"]):
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="🚫 This command can only be used in authorized channels.",
        )
        return

    if not await is_user_authorized(body["user_id"]):
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="🚫 You don't have permission to perform this action.",
        )
        return

    modal_view: Dict[str, Any] = {
        "type": "modal",
        "callback_id": "sonar_modal",
        "title": {"type": "plain_text", "text": "🔍 Sonar"},
        "private_metadata": body["channel_id"],
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "👋 *Welcome to Sonar!*\nWhat would you like to do?",
                },
            },
            {"type": "divider"},
            {
                "type": "actions",
                "block_id": "sonar_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔍 Search Data",
                            "emoji": True,
                        },
                        "value": "search",
                        "action_id": "search_action",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👥 Find Alt Accounts",
                            "emoji": True,
                        },
                        "value": "find_alts",
                        "action_id": "find_alts_action",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📅 User Join/Leave History",
                            "emoji": True,
                        },
                        "value": "join_leave_history",
                        "action_id": "join_leave_history_action",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⚠️ *Note:* All search actions are logged for audit purposes."
                    }
                ],
            },
        ],
    }

    await client.views_open(trigger_id=body["trigger_id"], view=modal_view) 