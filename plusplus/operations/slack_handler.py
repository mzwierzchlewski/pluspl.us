from plusplus.operations.points import update_points, generate_string
from plusplus.operations.leaderboard import generate_leaderboard, generate_numbered_list
from plusplus.operations.help import help_text
from plusplus.operations.reset import generate_reset_block
from plusplus.models import db, SlackTeam, Thing
from plusplus import config
import re

user_exp = re.compile(r"[^<]*<@([A-Za-z0-9]+)> *(\+\+|\-\-|==)")
user_chuj_exp = re.compile(r"^<@([A-Za-z0-9]+)> chuj$")
thing_exp = re.compile(r"#([A-Za-z0-9\.\-_@$!\*\(\)\,\?\/%\\\^&\[\]\{\"':; ]+)(\+\+|\-\-|==)")

def process_incoming_message(event_data, req):
    # ignore retries
    if req.headers.get('X-Slack-Retry-Reason'):
        return "Status: OK"

    event = event_data['event']
    subtype = event.get('subtype', '')
    # ignore bot messages
    text = event.get('text')
    if text is None:
        return "Status: OK"
    message = text.lower()

    if (message != "sn4psh0t" and message != "sn44psh0t" and message != "sn4pr3s3t") and subtype == 'bot_message':
        return "Status: OK"

    # ignore edited messages
    if subtype == 'message_changed':
        return "Status: OK"

    user = event.get('user').lower()
    channel = event.get('channel')
    channel_type = event.get('channel_type')

    # load/update team
    team = SlackTeam.query.filter_by(id=event_data['team_id']).first()
    team.update_last_access()
    db.session.add(team)
    db.session.commit()
    
    user_match = user_exp.match(message)
    user_chuj_match = user_chuj_exp.match(message)
    thing_match = thing_exp.match(message)
    if user_match:
        # handle user point operations
        found_user = user_match.groups()[0].strip()
        operation = user_match.groups()[1].strip()
        thing = Thing.query.filter_by(item=found_user.lower(), team=team).first()
        if not thing:
            thing = Thing(item=found_user.lower(), points=0, user=True, team_id=team.id)
        message = update_points(thing, operation, is_self=user==found_user)
        team.slack_client().api_call(
            "chat.postMessage",
            channel='#karmawhores',
            text=message
        )
        print("Processed " + thing.item)
    elif user_chuj_match:
        found_user = user_chuj_match.groups()[0].strip()
        operation = "--"
        thing = Thing.query.filter_by(item=found_user.lower(), team=team).first()
        if not thing:
            thing = Thing(item=found_user.lower(), points=0, user=True, team_id=team.id)
        message = update_points(thing, operation, is_self=user==found_user)
        team.slack_client().api_call(
            "chat.postMessage",
            channel='#karmawhores',
            text=message
        )
        print("Processed " + thing.item)
    elif thing_match:
        # handle thing point operations
        found_thing = thing_match.groups()[0].strip()
        operation = thing_match.groups()[1].strip()
        thing = Thing.query.filter_by(item=found_thing.lower(), team=team).first()
        if not thing:
            thing = Thing(item=found_thing.lower(), points=0, user=False, team_id=team.id)
        message = update_points(thing, operation)
        team.slack_client().api_call(
            "chat.postMessage",
            channel='#karmawhores',
            text=message
        )
        print("Processed " + thing.item)
    elif "leaderboard" in message and team.bot_user_id.lower() in message:
        global_board = "global" in message
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            blocks=generate_leaderboard(team=team, global_leaderboard=global_board)
        )
        print("Processed leaderboard for team " + team.id)
    elif "loserboard" in message and team.bot_user_id.lower() in message:
        global_board = "global" in message
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            blocks=generate_leaderboard(team=team, losers=True, global_leaderboard=global_board)
        )
        print("Processed loserboard for team " + team.id)
    elif "help" in message and (team.bot_user_id.lower() in message or channel_type=="im"):
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            blocks=help_text(team)
        )
        print("Processed help for team " + team.id)
    elif "feedback" in message and (team.bot_user_id.lower() in message or channel_type=="im"):
        print(message)
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            text="Thanks! For a more urgent response, please email " + config.SUPPORT_EMAIL
        )
    elif "reset" in message and team.bot_user_id.lower() in message:
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            blocks=generate_reset_block()
        )
    elif "sn4psh0t" in message and team.bot_user_id.lower() in message:
        team.slack_client().api_call(
            "chat.postMessage",
            channel='#karmawhores',
            blocks=generate_leaderboard(team=team, snapshot=True)
        )
        print("Processed shapshot for team " + team.id)
    elif "sn44psh0t" in message and team.bot_user_id.lower() in message:
        team.slack_client().api_call(
            "chat.postMessage",
            channel=channel,
            blocks=generate_leaderboard(team=team, snapshot=True)
        )
        print("Processed shapshot for team " + team.id)
    elif "sn4pr3s3t" in message and team.bot_user_id.lower() in message:
        user_args = {"user": True}
        users = Thing.query.filter_by(**user_args)
        for user in users:
            user.reset_status()
            db.session.add(user)
        db.session.commit()
        
        filtered_users = sorted(list(filter(lambda u: u.points - u.last_week_points != 0, users)), key=lambda u: u.points - u.last_week_points)
        if len(filtered_users) > 0:
            filtered_users[0].turbo = True
            db.session.add(filtered_users[0])
            filtered_users[-1].chujo = True
            db.session.add(filtered_users[-1])
            db.session.commit()

        things = Thing.query.all()
        for thing in things:
            thing.reset_last_week()
            db.session.add(thing)
        db.session.commit()
        print("Processed shapreset for team " + team.id)

    return "OK", 200