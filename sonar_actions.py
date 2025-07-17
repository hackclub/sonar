from typing import Dict, Any
from slack_sdk import WebClient
from commands.fetch_data import get_search_modal_view
# from commands.find_alts import get_find_alts_modal_view


async def handle_sonar_action(client: WebClient, ack, body: Dict[str, Any]):
    await ack()
    print("🔄 Handling sonar action...")

    action_id = body["actions"][0]["action_id"]
    triggering_channel = body["view"]["private_metadata"]
    
    if action_id == "search_action":
        search_modal = get_search_modal_view()
        search_modal["private_metadata"] = triggering_channel
        await client.views_update(
            view_id=body["container"]["view_id"],
            view=search_modal
        )
    elif action_id == "find_alts_action":
        # TODO: When find_alts_modal is implemented, add channel ID there too
        await client.views_update(
            view_id=body["container"]["view_id"],
            view=get_find_alts_modal_view()
        )
    elif action_id == "join_leave_history_action":
        # Real modal for join/leave history
        join_leave_modal = {
            "type": "modal",
            "callback_id": "join_leave_history_modal",
            "title": {"type": "plain_text", "text": "📅 Join/Leave History"},
            "submit": {"type": "plain_text", "text": "Search"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "user_select",
                    "element": {
                        "type": "multi_users_select",
                        "action_id": "user_select_input",
                        "placeholder": {"type": "plain_text", "text": "Select user(s) (optional)"},
                        "max_selected_items": 1
                    },
                    "label": {"type": "plain_text", "text": "User (optional)"},
                    "optional": True
                },
                {
                    "type": "input",
                    "block_id": "channel_select",
                    "element": {
                        "type": "conversations_select",
                        "action_id": "channel_select_input",
                        "placeholder": {"type": "plain_text", "text": "Select a channel (optional)"},
                        "filter": {"include": ["public", "private"]}
                    },
                    "label": {"type": "plain_text", "text": "Channel (optional)"},
                    "optional": True
                },
                {
                    "type": "input",
                    "block_id": "date_range_start",
                    "element": {
                        "type": "datepicker",
                        "action_id": "start_date",
                        "placeholder": {"type": "plain_text", "text": "Select start date (optional)"}
                    },
                    "label": {"type": "plain_text", "text": "Start Date (optional)"},
                    "optional": True
                },
                {
                    "type": "input",
                    "block_id": "date_range_end",
                    "element": {
                        "type": "datepicker",
                        "action_id": "end_date",
                        "placeholder": {"type": "plain_text", "text": "Select end date (optional)"}
                    },
                    "label": {"type": "plain_text", "text": "End Date (optional)"},
                    "optional": True
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "*Tip:* You can search by user, channel, date range, or any combination."}
                    ]
                }
            ]
        }
        await client.views_update(
            view_id=body["container"]["view_id"],
            view=join_leave_modal
        ) 