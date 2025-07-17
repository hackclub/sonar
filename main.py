import asyncio
import multiprocessing
from config import app, PORT
from commands.sonar import handle_sonar
from actions.load_more import load_more
from actions.prev_page import prev_page
# from actions.alt_pagination import handle_alt_page
from actions.sonar_actions import handle_sonar_action
from logs.data_fetcher import fetch_historical_data, fetch_incremental_data
from utils.elastic_search import create_index
from utils.slack_utils import fetch_join_leave_history
# from utils.slack_utils import check_bot_channel
from view.search_modal import handle_search
from slack_sdk import WebClient

app.command("/sonar")(handle_sonar)

app.action("search_action")(handle_sonar_action)
# app.action("find_alts_action")(handle_sonar_action)
app.action("load_more")(load_more)
app.action("prev_page")(prev_page)
# app.action("next_alt_page")(handle_alt_page)
# app.action("prev_alt_page")(handle_alt_page)
app.view("search_modal")(handle_search)

async def handle_join_leave_history(ack, body, client: WebClient, view, logger):
    await ack()
    user_id = None
    channel_id = None
    start_date = None
    end_date = None
    try:
        user_select = view["state"]["values"].get("user_select", {})
        if user_select:
            users = user_select["user_select_input"].get("selected_users", [])
            if users:
                user_id = users[0]
        channel_select = view["state"]["values"].get("channel_select", {})
        if channel_select:
            channel_id = channel_select["channel_select_input"].get("selected_conversation", None)
        start_date = view["state"]["values"].get("date_range_start", {}).get("start_date", {}).get("selected_date", None)
        end_date = view["state"]["values"].get("date_range_end", {}).get("end_date", {}).get("selected_date", None)
    except Exception as e:
        logger.error(f"Error extracting join/leave modal values: {e}")
    if not channel_id:
        await client.chat_postMessage(
            channel=body["user"]["id"],
            text="Please select a channel to search join/leave history."
        )
        return
    events = await fetch_join_leave_history(channel_id, user_id, start_date, end_date)
    if not events:
        await client.chat_postMessage(
            channel=body["user"]["id"],
            text="No join/leave events found for the selected criteria."
        )
        return

    from datetime import datetime
    def fmt_event(e):
        ts = datetime.utcfromtimestamp(float(e["ts"])).strftime('%Y-%m-%d %H:%M UTC')
        action = "joined" if e["type"] == "member_joined_channel" else "left"
        user = f'<@{e["user"]}>' if e["user"] else "(unknown)"
        inviter = f' (invited by <@{e["inviter"]}>)' if e.get("inviter") else ""
        return f'{user} {action} <#{e["channel"]}> at {ts}{inviter}'
    msg = "*Join/Leave History:*
" + "\n".join(fmt_event(e) for e in events[:30])
    if len(events) > 30:
        msg += f"\n...and {len(events)-30} more."
    await client.chat_postMessage(
        channel=body["user"]["id"],
        text=msg
    )

app.view("join_leave_history_modal")(handle_join_leave_history)


async def data_fetcher():
    await create_index()
    historical_fetch_task = asyncio.create_task(fetch_historical_data())
    incremental_fetch_task = asyncio.create_task(fetch_incremental_data())
    await asyncio.gather(incremental_fetch_task)


def run_data_fetcher():
    asyncio.run(data_fetcher())


def run_slack_app():
    app.start(PORT)


if __name__ == "__main__":
    data_process = multiprocessing.Process(target=run_data_fetcher)
    slack_process = multiprocessing.Process(target=run_slack_app)

    data_process.start()
    slack_process.start()

    data_process.join()
    slack_process.join()
