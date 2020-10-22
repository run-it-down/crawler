import client
import database
import model
import util


logger = util.Logger(__name__)


def post_summoner(riot_client: client.Client,
                  game_range: tuple,
                  summoner_name: str = None,
                  ):
    conn = database.get_connection()

    # summoner
    summoner = riot_client.get_summoner_by_summonername(summoner_name=summoner_name)
    database.insert_summoner(conn=conn,
                             summoner=summoner,
                             )

    # matchlist
    matchlist = _get_matchlist_updates(summoner=summoner,
                                       conn=conn,
                                       riot_client=riot_client,
                                       )
    matchlist.match_references = matchlist.match_references[game_range[0]:game_range[1]]
    for match_ref in matchlist.match_references:
        database.insert_summoner_match(conn=conn,
                                       game_id=match_ref.game_id,
                                       account_id=summoner.account_id,
                                       )

    # matchdetails
    i = 1
    for match_ref in matchlist.match_references:
        logger.info(f'getting match {match_ref.game_id} ({i}/{len(matchlist.match_references)})')
        match = riot_client.get_match_details_by_matchid(match_id=match_ref.game_id)
        if match.game_mode != 'CLASSIC':
            continue

        # insert team
        for team in match.teams:
            database.insert_team(conn=conn,
                                 team=team)

        for participant in match.participants:

            # insert timeline
            database.insert_timeline(conn,
                                     timeline=participant.timeline)

            # insert stat
            database.insert_stat(conn,
                                 stat=participant.stat)

            # insert participating summoners
            s = riot_client.get_summoner_by_account_id(account_id=participant.account_id)
            database.insert_summoner(conn=conn,
                                     summoner=s,
                                     )

            # insert participant
            database.insert_participant(conn=conn,
                                        participant=participant)

        # insert match
        database.insert_match(conn=conn,
                              match=match)

        i += 1

    database.kill_connection(conn)


def _get_matchlist_updates(summoner: model.Summoner,
                           riot_client: client.Client,
                           conn,
                           ) -> model.Matchlist:

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
        if len(matchlist.match_references) % 100 == 0:
            i += 100
        else:
            break
        matchlist_tmp = riot_client.get_matchlist_by_accountid(account_id=summoner.account_id,
                                                               begin_index=i,
                                                               end_index=i + 100,
                                                               )

        matchlist.match_references.extend(matchlist_tmp.match_references)
        if len(matchlist.match_references) == 0:
            # no new matches found
            break

    logger.info(f'{len(matchlist.match_references)} new games')
    return matchlist
