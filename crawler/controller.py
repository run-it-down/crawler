import falcon

import client

try:
    import dtos.matchlist
    import rid_parser
    import database
    import parser
    import model
    import util
except ModuleNotFoundError:
    print('common package not in python path')


logger = util.Logger(__name__)


def crawl_summoner(
    rclient: client.Client,
    summoner_name: str,
) -> falcon.http_status:
    conn = database.get_connection()

    # get summoner, fail if not exist
    summoner = rclient.get_summoner_by_summonername(
        summoner_name=summoner_name,
    )

    # get matchlist
    match_ref_list = []
    i = 0
    while True:
        ml_snippet = rclient.get_matchlist_by_accountid(
            account_id=summoner.account_id,
            begin_index=i,
            end_index=i+100,
        )
        match_ref_list.extend(ml_snippet.matches)
        i += 100
        if not ml_snippet.matches.__len__() == 100:
            break

    # for m in matchlist: check if match in db -> insert
    g = 0
    for ref in match_ref_list:
        if database.select_match_by_gameid(
            conn=conn,
            game_id=ref.game_id
        ):
            logger.info(f'"{summoner_name}" - game {g}/{match_ref_list.__len__()}: skip')
            g += 1
            continue

        logger.info(f'"{summoner_name}" - game {g}/{match_ref_list.__len__()}')
        match = rclient.get_match_by_matchid(
            ref.game_id,
        )
        database.insert_match(
            conn=conn,
            match=rid_parser.parse_match(match_dto=match)
        )
        for team in match.teams:
            database.insert_team(
                conn=conn,
                team=rid_parser.parse_team(
                    team_dto=team,
                    game_id=match.game_id
                )
            )
        identities = {}  # Key-Value-Store to match participants later on
        for identity in match.participant_identities:
            summoner = rclient.get_summoner_by_account_id(
                identity.player.account_id,
            )
            database.insert_summoner(
                conn=conn,
                summoner=rid_parser.parse_summoner(summoner),
            )

            database.insert_summoner_match(
                conn=conn,
                summoner_match=model.SummonerMatch(
                    game_id=match.game_id,
                    account_id=summoner.account_id,
                )
            )
            identities[identity.participant_id] = identity.player.account_id

        participants = {}
        for participant_dto in match.participants:

            part_identity = identities.get(participant_dto.participant_id)

            timeline = rid_parser.parse_timeline(timeline_dto=participant_dto.timeline)
            database.insert_timeline(
                conn=conn,
                timeline=timeline,
            )

            stat = rid_parser.parse_stats(
                stat=participant_dto.stats,
            )
            database.insert_stat(
                conn=conn,
                stat=stat,
            )

            participant = rid_parser.parse_participant(
                participant_dto=participant_dto,
                game_id=match.game_id,
                account_id=part_identity,
                stat_id=stat.stat_id,
                team_id=participant_dto.team_id,
                timeline_id=timeline.timeline_id,
                role=participant_dto.timeline.role,
                lane=participant_dto.timeline.lane,
            )
            database.insert_participant(
                conn=conn,
                participant=participant,
            )
            participants[participant_dto.participant_id] = participant.participant_id  # map id to uuid

        timeline = rclient.get_match_timeline_by_matchid(
            match_id=str(match.game_id),
        )
        for frame_dto in timeline.frames:
            for event_dto in frame_dto.events:
                event = rid_parser.parse_event(
                    event_dto=event_dto,
                    map=participants,
                )
                database.insert_event(
                    conn=conn,
                    event=event,
                )

            for participant_frame_dto in frame_dto.participant_frames.values():
                participant_frame = rid_parser.parse_participant_frame(
                    participant_frame_dto=participant_frame_dto,
                    participant_id=participants[participant_frame_dto.participant_id],
                    timestamp=frame_dto.timestamp,
                )
                database.insert_participant_frame(
                    conn=conn,
                    participant_frame=participant_frame,
                )
        g += 1


def summoner_exists(
    summoner_name: str,
):
    conn = database.get_connection()

    summoner = database.select_summoner(
        conn=conn,
        summoner_name=summoner_name,
    )
    return summoner
