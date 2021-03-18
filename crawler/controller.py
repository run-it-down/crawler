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
        logger.info(msg=f"Crawling match {match_ref.game_id}...")
        match = riot_client.get_match_by_matchid(match_ref.game_id)
        database.insert_match(conn=conn, match=rid_parser.parse_match(match_dto=match))

        for team in match.teams:
            database.insert_team(conn=conn, team=rid_parser.parse_team(team_dto=team,
                                                                       game_id=match.game_id))

        identities = {}  # Key-Value-Store to match participants later on
        for identity in match.participant_identities:
            logger.info(msg=f"Crawling summoner {identity.player.summoner_name}, {identity.player.current_account_id}")
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

            logger.info(msg=f"Insert timeline for {part_identity}...")
            timeline = rid_parser.parse_timeline(timeline_dto=participant_dto.timeline)
            database.insert_timeline(conn=conn, timeline=timeline)

            logger.info(msg=f"Insert stats for {part_identity}...")
            stat = rid_parser.parse_stats(stat=participant_dto.stats)
            database.insert_stat(conn=conn, stat=stat)

            logger.info(msg=f"Insert participant {part_identity}...")
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

        logger.info(msg=f"Crawling match timeline for {match.game_id}...")
        timeline = riot_client.get_match_timeline_by_matchid(match_id=str(match.game_id))
        for frame_dto in timeline.frames:
            for event_dto in frame_dto.events:
                logger.info(f"Insert event frame {event_dto.type} at {event_dto.timestamp}...")
                event = rid_parser.parse_event(event_dto=event_dto,
                                               map=participants)
                database.insert_event(conn=conn, event=event)

            for participant_frame_dto in frame_dto.participant_frames.values():
                logger.info(
                    f"Insert participant frame for {participant_frame_dto.participant_id} at {frame_dto.timestamp}")
                participant_frame = rid_parser.parse_participant_frame(
                    participant_frame_dto=participant_frame_dto,
                    participant_id=participants[participant_frame_dto.participant_id],
                    timestamp=frame_dto.timestamp,
                )
                database.insert_participant_frame(conn=conn, participant_frame=participant_frame)

        logger.info(f"Successfully crawled game {match_ref.game_id}")
    logger.info(f"Successfully crawled games for {summoner_name}")


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

    logger.info(f'{len(matchlist.matches)} new games')
    return matchlist
