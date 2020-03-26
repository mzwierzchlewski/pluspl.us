from ..models import Thing
import json


def generate_leaderboard(team=None, losers=False, global_leaderboard=False, snapshot=False):
    if losers:
        ordering = Thing.points.asc()
        header = "Here's the current loserboard:"
    else:
        ordering = Thing.points.desc()
        header = "Here's the current leaderboard:"
    
    if snapshot:
        ordering = Thing.points.desc()
        header = "Last month standings:"

    # filter args
    user_args = {"user": True}
    thing_args = {"user": False}
    if snapshot:
        users = Thing.query.filter_by(**user_args).order_by(Thing.points.desc())
        things =  Thing.query.filter_by(**thing_args).order_by(Thing.points.desc())
    else:
        if not global_leaderboard:
            user_args['team'] = team
            thing_args['team'] = team
            users = Thing.query.filter_by(**user_args).order_by(ordering).limit(10)

        things = Thing.query.filter_by(**thing_args).order_by(ordering).limit(10)

    formatted_things = [f"{thing.item} ({thing.points})" for thing in things] if not snapshot else [f"{thing.item} ({thing.points - thing.last_week_points})" for thing in filter(lambda t: t.points - t.last_week_points != 0, things) ]
    numbered_things = generate_numbered_list(formatted_things)
    leaderboard_header = {"type": "section",
                          "text":
                              {"type": "mrkdwn",
                               "text": header
                               }
                          }
    body = {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Things*\n" + numbered_things
                    }
                ]
        }

    sorted_users = sorted(users, key=lambda u: 0 - (u.points - u.last_week_points))

    if not global_leaderboard:
        formatted_users = [f"<@{user.item.upper()}> ({user.points}) {':turbokotlarz:' if user.turbo else ''} {':rak2:' if user.chujo else ''}" for user in users] if not snapshot else [f"<@{user.item.upper()}> ({user.points - user.last_week_points})" for user in sorted_users]
        numbered_users = generate_numbered_list(formatted_users)
        body['fields'].append({
                                  "type": "mrkdwn",
                                  "text": "*Users*\n" + numbered_users
                              })
        if (snapshot and len(sorted_users) > 0):
            turbo_users = list(filter(lambda u: u.points - u.last_week_points > 0, sorted_users))
            divider = {
			    "type": "divider"
		    }
            turbo = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":turbokotlarz: :turbokotlarz: :turbokotlarz: *Turbokotlarz* :turbokotlarz: :turbokotlarz: :turbokotlarz:\n" + ":sadparrot:"
                    }
                }
            if len(turbo_users) > 0:
                turbo = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":turbokotlarz: :turbokotlarz: :turbokotlarz: *Turbokotlarz* :turbokotlarz: :turbokotlarz: :turbokotlarz:\n" + f"<@{turbo_users[0].item.upper()}>"
                    }
                }
            chujo_users = list(filter(lambda u: u.points - u.last_week_points <= 0, sorted_users))
            chujo = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":tn: :rak2: :zjebparrot: *Chujokotlarz* :zjebparrot: :rak2: :tn:\n" + ":alezapierdalaparrot:"
                }
            }
            if len(chujo_users) > 0:
                chujo_list = ""
                for user in chujo_users:
                    chujo_list += f"<@{user.item.upper()}>\n"
                chujo = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":tn: :rak2: :zjebparrot: *Chujokotlarz* :zjebparrot: :rak2: :tn:\n" + chujo_list
                    }
                }
            
            leaderboard = [leaderboard_header, body, divider, turbo, divider, chujo]
            return json.dumps(leaderboard)

    leaderboard = [leaderboard_header, body]
    return json.dumps(leaderboard)


def generate_numbered_list(items):
    out = ""
    for i, item in enumerate(items, 1):
        out += f"{i}. {item}\n"
    if len(out) == 0:
        out = "Welp, nothing's here yet."
    return out
