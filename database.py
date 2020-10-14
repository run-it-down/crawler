import dataclasses
import json
import model
import os
import psycopg2
import typing


def get_connection(
        database=os.getenv('DB'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWD'),
        host=os.getenv('DBHOST'),
        port=int(os.getenv('DBPORT')),
):
    return psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def kill_connection(conn):
    try:
        conn.close()
    except psycopg2.Error:
        pass


def _execute(
    conn,
    statement: str,
    values: tuple,
    print_exception: bool = True,
):
    cur = conn.cursor()
    try:
        cur.execute(statement, values)
    except psycopg2.Error as e:
        if print_exception:
            print(e)
        cur.execute("rollback")
        conn.commit()
    return cur


def insert_summoner(conn,
                    summoner: model.Summoner,
                    ):
    statement = "INSERT INTO summoners " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, now())"
    values = dataclasses.astuple(summoner)

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=False,
    )

    conn.commit()


def insert_summoner_match(conn,
                          game_id: int,
                          account_id: str,
                          ):
    statement = "INSERT INTO summoner_matches " \
                "VALUES (%s, %s)"
    values = (game_id, account_id)

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=False,
    )

    conn.commit()


def insert_team(conn,
                team: model.Team
                ):
    statement = "INSERT INTO teams " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = dataclasses.astuple(team)

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=True,
    )

    conn.commit()


def insert_timeline(conn,
                    timeline: model.Timeline
                    ):
    statement = "INSERT INTO timelines " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (
        timeline.timeline_id,
        json.dumps(timeline.creepsPerMinDeltas),
        json.dumps(timeline.xpPerMinDeltas),
        json.dumps(timeline.goldPerMinDeltas),
        json.dumps(timeline.csDiffPerMinDeltas),
        json.dumps(timeline.xpDiffPerMinDeltas),
        json.dumps(timeline.damageTakenPerMinDeltas),
        json.dumps(timeline.damageTakenDiffPerMinDeltas),
    )

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=True,
    )

    conn.commit()


def insert_stat(conn,
                stat: model.Stat
                ):
    statement = "INSERT INTO stats " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = dataclasses.astuple(stat)

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=True,
    )

    conn.commit()


def insert_participant(conn,
                       participant: model.Participant
                       ):
    statement = "INSERT INTO participants " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (
        participant.participant_id,
        participant.team_id,
        participant.account_id,
        participant.champion_id,
        participant.spell1_id,
        participant.spell2_id,
        participant.stat.stat_id,
        participant.timeline.timeline_id,
    )

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=True,
    )

    conn.commit()


def insert_match(conn,
                 match: model.Match
                 ):
    statement = "INSERT INTO matches " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    teams: typing.List[str] = []
    for team in match.teams:
        teams.append(team.team_id)

    participants: typing.List[str] = []
    for participant in match.participants:
        participants.append(participant.participant_id)

    values = (match.game_id,
              match.platform_id,
              match.game_creation,
              match.game_duration,
              match.queue_id,
              match.map_id,
              match.season_id,
              match.game_version,
              match.game_mode,
              match.game_type,
              teams,
              participants
              )

    _execute(
        conn=conn,
        statement=statement,
        values=values,
        print_exception=True,
    )

    conn.commit()


def select_count_summoner_match(conn,
                                account_id: str,
                                ):
    statement = "SELECT COUNT(*) FROM summoner_matches " \
                "WHERE accountid = %s"
    values = (account_id,)

    cur = _execute(
        conn=conn,
        statement=statement,
        values=values,
    )

    conn.commit()
    return cur.fetchone()[0]
