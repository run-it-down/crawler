import client

import database
import model
import util
import dtos.matchlist
import rid_parser

logger = util.Logger(__name__)


def post_summoner(riot_client: client.Client,
                  summoner_name: str = None,
                  ):
    conn = database.get_connection()

    summoner = riot_client.get_summoner_by_summonername(summoner_name=summoner_name)
    matchlist = _get_matchlist_updates(summoner=summoner,
                                       conn=conn,
                                       riot_client=riot_client,
                                       )

    # TODO remove hardcoded gamerange
    for match_ref in matchlist.matches[:3]:
        match = riot_client.get_match_by_matchid(match_ref.game_id)
        database.insert_match(conn=conn, match=rid_parser.parse_match(match_dto=match))

        for team in match.teams:
            database.insert_team(conn=conn, team=rid_parser.parse_team(team_dto=team,
                                                                       game_id=match.game_id))

        identities = {}  # Key-Value-Store to match participants later on
        for identity in match.participant_identities:
            summoner = riot_client.get_summoner_by_account_id(identity.player.current_account_id)
            database.insert_summoner(conn=conn, summoner=rid_parser.parse_summoner(summoner))

            database.insert_summoner_match(
                conn=conn,
                summoner_match=model.SummonerMatch(game_id=match.game_id,
                                                   account_id=summoner.account_id)
            )
            identities[identity.participant_id] = identity.player.current_account_id

        participants = {}
        for participant_dto in match.participants:
            part_identity = identities.get(participant_dto.participant_id)

            timeline = rid_parser.parse_timeline(timeline_dto=participant_dto.timeline)
            database.insert_timeline(conn=conn, timeline=timeline)

            stat = rid_parser.parse_stats(stat=participant_dto.stats)
            database.insert_stat(conn=conn, stat=stat)

            participant = rid_parser.parse_participant(participant_dto=participant_dto,
                                                       game_id=match.game_id,
                                                       account_id=part_identity,
                                                       stat_id=stat.stat_id,
                                                       team_id=participant_dto.team_id,
                                                       timeline_id=timeline.timeline_id,
                                                       role=participant_dto.timeline.role,
                                                       lane=participant_dto.timeline.lane,
                                                       )
            database.insert_participant(conn=conn, participant=participant)
            participants[participant_dto.participant_id] = participant.participant_id  # map id to uuid

        timeline = riot_client.get_match_timeline_by_matchid(match_id=str(match.game_id))
        for frame_dto in timeline.frames:
            for event_dto in frame_dto.events:
                event = rid_parser.parse_event(event_dto=event_dto,
                                               map=participants)
                database.insert_event(conn=conn, event=event)

            for participant_frame_dto in frame_dto.participant_frames.values():
                participant_frame = rid_parser.parse_participant_frame(
                    participant_frame_dto=participant_frame_dto,
                    participant_id=participants[participant_frame_dto.participant_id],
                    timestamp=frame_dto.timestamp,
                )
                database.insert_participant_frame(conn=conn, participant_frame=participant_frame)


def _get_matchlist_updates(summoner: model.Summoner,
                           riot_client: client.Client,
                           conn,
                           ) -> dtos.matchlist.MatchlistDto:
    # get count of matches pro summoner
    i = database.select_count_summoner_match(conn=conn,
                                             account_id=summoner.account_id)
    if not i:
        i = 0

    matchlist = riot_client.get_matchlist_by_accountid(account_id=summoner.account_id,
                                                       begin_index=i,
                                                       end_index=i + 100,
                                                       )

    while True:
        if len(matchlist.matches) % 100 == 0:
            i += 100
        else:
            break
        matchlist_tmp = riot_client.get_matchlist_by_accountid(account_id=summoner.account_id,
                                                               begin_index=i,
                                                               end_index=i + 100,
                                                               )

        matchlist.matches.extend(matchlist_tmp.matches)
        if len(matchlist.matches) == 0:
            # no new matches found
            break

    return matchlist


def summoner_exists(summoner: str):
    conn = database.get_connection()

    summoner = database.select_summoner(conn=conn, summoner_name=summoner)
    return summoner
