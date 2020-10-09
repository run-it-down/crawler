import dataclasses
import requests
import typing
from uuid import uuid4


import model
import util


# init logger
logger = util.Logger(__name__)


class ClientRoutes:

    def __init__(self,
                 endpoint: str,
                 ):
        self.endpoint = endpoint

    def get_summoner_by_summonername(self,
                                     summoner_name: str,
                                     ):
        return util.urljoin(self.endpoint,
                            f'/lol/summoner/v4/summoners/by-name/{summoner_name}',
                            )

    def get_summoner_by_account_id(self,
                                   account_id: str,
                                   ):
        return util.urljoin(self.endpoint,
                            f'/lol/summoner/v4/summoners/by-account/{account_id}',
                            )

    def get_matchlist_by_accountid(self,
                                   account_id: str):
        return util.urljoin(self.endpoint,
                            f'/lol/match/v4/matchlists/by-account/{account_id}',
                            )

    def get_match_by_matchid(self,
                             match_id: str):
        return util.urljoin(self.endpoint,
                            f'/lol/match/v4/matches/{match_id}',
                            )


@dataclasses.dataclass()
class ClientConfig:
    token: str


class RiotAPINotOkayException(Exception):
    def __init__(self,
                 res: requests.Response,
                 msg: str,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)
        self.res = res
        self.msg = msg


class Client:

    def __init__(self,
                 config: ClientConfig,
                 routes: ClientRoutes,
                 ):
        self.config = config
        self.routes = routes

    def _request(self, method: str,
                 print_error: bool = True,
                 *args,
                 **kwargs):
        res = requests.request(method=method,
                               verify=False,
                               *args, **kwargs)
        if not res.ok:
            msg = f'{method} request to url {res.url} failed with {res.status_code=} {res.reason=}'
            if print_error:
                print(msg)
                print(res.text)
            raise RiotAPINotOkayException(res=res,
                                          msg=msg,
                                          )
        return res

    def get_summoner_by_summonername(self,
                                     summoner_name: str,
                                     ):
        logger.info(f'getting summoner {summoner_name}')
        res = self._request(method='GET',
                            url=self.routes.get_summoner_by_summonername(summoner_name=summoner_name),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()
        return model.Summoner(
            account_id=res['accountId'],
            id=res['id'],
            puuid=res['puuid'],
            name=res['name'],
            profile_icon_id=res['profileIconId'],
            revision_date=res['revisionDate'],
            summoner_level=res['summonerLevel'],
        )

    def get_summoner_by_account_id(self,
                                   account_id: str,
                                   ):
        logger.info(f'getting summoner {account_id}')
        res = self._request(method='GET',
                            url=self.routes.get_summoner_by_account_id(account_id=account_id),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()
        return model.Summoner(
            account_id=res['accountId'],
            id=res['id'],
            puuid=res['puuid'],
            name=res['name'],
            profile_icon_id=res['profileIconId'],
            revision_date=res['revisionDate'],
            summoner_level=res['summonerLevel'],
        )

    def get_match_details_by_matchid(self,
                                     match_id: int,
                                     ):
        logger.info(f'getting match {match_id}')
        res = self._request(method='GET',
                            url=self.routes.get_match_by_matchid(match_id=match_id),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()

        teams: typing.List[model.Team] = []
        for team in res['teams']:
            bans: typing.List[model.Champion.id] = []
            for ban in team['bans']:
                bans.append(ban['championId'])

            teams.append(model.Team(
                team_id=str(uuid4()),
                win=team['win'],
                first_blood=team['firstBlood'],
                first_tower=team['firstTower'],
                first_inhibitor=team['firstInhibitor'],
                first_baron=team['firstBaron'],
                first_dragon=team['firstDragon'],
                first_rift_herald=team['firstRiftHerald'],
                tower_kills=team['towerKills'],
                inhibitor_kills=team['inhibitorKills'],
                baron_kills=team['baronKills'],
                dragon_kills=team['dragonKills'],
                vilemaw_kills=team['vilemawKills'],
                rift_herald_kills=team['riftHeraldKills'],
                dominion_victory_score=team['dominionVictoryScore'],
                bans=bans,
            ))

        participants: typing.List[model.Participant] = []
        for participant in res['participants']:
            account_id: str = ''
            for participant_idendity in res['participantIdentities']:
                if participant_idendity['participantId'] == participant['participantId']:
                    account_id = participant_idendity['player']['accountId']

            timeline = model.Timeline(
                timeline_id=str(uuid4()),
                creepsPerMinDeltas=participant['timeline']['creepsPerMinDeltas'],
                xpPerMinDeltas=participant['timeline']['xpPerMinDeltas'],
                goldPerMinDeltas=participant['timeline']['goldPerMinDeltas'],
                csDiffPerMinDeltas=participant['timeline']['csDiffPerMinDeltas'],
                xpDiffPerMinDeltas=participant['timeline']['xpDiffPerMinDeltas'],
                damageTakenPerMinDeltas=participant['timeline']['damageTakenPerMinDeltas'],
                damageTakenDiffPerMinDeltas=participant['timeline']['damageTakenDiffPerMinDeltas'],
            )

            stat = model.Stat(
                stat_id=str(uuid4()),
                win=participant['stats']['win'],
                items=[
                    participant['stats']['item0'],
                    participant['stats']['item1'],
                    participant['stats']['item2'],
                    participant['stats']['item3'],
                    participant['stats']['item4'],
                    participant['stats']['item5'],
                    participant['stats']['item6'],
                ],
                kills=participant['stats']['kills'],
                deaths=participant['stats']['deaths'],
                assists=participant['stats']['assists'],
                largestKillingSpree=participant['stats']['largestKillingSpree'],
                largestMultiKill=participant['stats']['largestMultiKill'],
                killingSprees=participant['stats']['killingSprees'],
                longestTimeSpentLiving=participant['stats']['longestTimeSpentLiving'],
                doubleKills=participant['stats']['doubleKills'],
                tripleKills=participant['stats']['tripleKills'],
                quadraKills=participant['stats']['quadraKills'],
                pentaKills=participant['stats']['pentaKills'],
                unrealKills=participant['stats']['unrealKills'],
                totalDamageDealt=participant['stats']['totalDamageDealt'],
                magicDamageDealt=participant['stats']['magicDamageDealt'],
                physicalDamageDealt=participant['stats']['physicalDamageDealt'],
                trueDamageDealt=participant['stats']['trueDamageDealt'],
                largestCriticalStrike=participant['stats']['largestCriticalStrike'],
                totalDamageDealtToChampions=participant['stats']['totalDamageDealtToChampions'],
                magicDamageDealtToChampions=participant['stats']['magicDamageDealtToChampions'],
                physicalDamageDealtToChampions=participant['stats']['physicalDamageDealtToChampions'],
                trueDamageDealtToChampions=participant['stats']['trueDamageDealtToChampions'],
                totalHeal=participant['stats']['totalHeal'],
                totalUnitsHealed=participant['stats']['totalUnitsHealed'],
                damageSelfMitigated=participant['stats']['damageSelfMitigated'],
                damageDealtToObjectives=participant['stats']['damageDealtToObjectives'],
                damageDealtToTurrets=participant['stats']['damageDealtToTurrets'],
                visionScore=participant['stats']['visionScore'],
                timeCCingOthers=participant['stats']['timeCCingOthers'],
                totalDamageTaken=participant['stats']['totalDamageTaken'],
                magicalDamageTaken=participant['stats']['magicalDamageTaken'],
                physicalDamageTaken=participant['stats']['physicalDamageTaken'],
                trueDamageTaken=participant['stats']['trueDamageTaken'],
                goldEarned=participant['stats']['goldEarned'],
                goldSpent=participant['stats']['goldSpent'],
                turretKills=participant['stats']['turretKills'],
                inhibitorKills=participant['stats']['inhibitorKills'],
                totalMinionsKilled=participant['stats']['totalMinionsKilled'],
                neutralMinionsKilledTeamJungle=participant['stats']['neutralMinionsKilledTeamJungle'],
                neutralMinionsKilledEnemyJungle=participant['stats']['neutralMinionsKilledEnemyJungle'],
                totalTimeCrowdControlDealt=participant['stats']['totalTimeCrowdControlDealt'],
                champLevel=participant['stats']['champLevel'],
                visionWardsBoughtInGame=participant['stats']['visionWardsBoughtInGame'],
                sightWardsBoughtInGame=participant['stats']['sightWardsBoughtInGame'],
                wardsPlaced=participant['stats']['wardsPlaced'],
                wardsKilled=participant['stats']['wardsKilled'],
                firstBloodKill=participant['stats']['firstBloodKill'],
                firstBloodAssist=participant['stats']['firstBloodAssist'],
                firstTowerKill=participant['stats']['firstTowerKill'],
                firstTowerAssist=participant['stats']['firstTowerAssist'],
                firstInhibitorKill=participant['stats']['firstInhibitorKill'],
                firstInhibitorAssist=participant['stats']['firstInhibitorAssist'],
                combatPlayerScore=participant['stats']['combatPlayerScore'],
                objectivePlayerScore=participant['stats']['objectivePlayerScore'],
                totalPlayerScore=participant['stats']['totalPlayerScore'],
                totalScoreRank=participant['stats']['totalScoreRank'],
                playerScore0=participant['stats']['playerScore0'],
                playerScore1=participant['stats']['playerScore1'],
                playerScore2=participant['stats']['playerScore2'],
                playerScore3=participant['stats']['playerScore3'],
                playerScore4=participant['stats']['playerScore4'],
                playerScore5=participant['stats']['playerScore5'],
                playerScore6=participant['stats']['playerScore6'],
                playerScore7=participant['stats']['playerScore7'],
                playerScore8=participant['stats']['playerScore8'],
                playerScore9=participant['stats']['playerScore9'],
                perk0=participant['stats']['perk0'],
                perk0Var1=participant['stats']['perk0Var1'],
                perk0Var2=participant['stats']['perk0Var2'],
                perk0Var3=participant['stats']['perk0Var3'],
                perk1=participant['stats']['perk1'],
                perk1Var1=participant['stats']['perk1Var1'],
                perk1Var2=participant['stats']['perk1Var2'],
                perk1Var3=participant['stats']['perk1Var3'],
                perk2=participant['stats']['perk2'],
                perk2Var1=participant['stats']['perk2Var1'],
                perk2Var2=participant['stats']['perk2Var2'],
                perk2Var3=participant['stats']['perk2Var3'],
                perk3=participant['stats']['perk3'],
                perk3Var1=participant['stats']['perk3Var1'],
                perk3Var2=participant['stats']['perk3Var2'],
                perk3Var3=participant['stats']['perk3Var3'],
                perk4=participant['stats']['perk4'],
                perk4Var1=participant['stats']['perk4Var1'],
                perk4Var2=participant['stats']['perk4Var2'],
                perk4Var3=participant['stats']['perk4Var3'],
                perk5=participant['stats']['perk5'],
                perk5Var1=participant['stats']['perk5Var1'],
                perk5Var2=participant['stats']['perk5Var2'],
                perk5Var3=participant['stats']['perk5Var3'],
                perkPrimaryStyle=participant['stats']['perk5Var3'],
                perkSubStyle=participant['stats']['perkSubStyle'],
                statPerk0=participant['stats']['statPerk0'],
                statPerk1=participant['stats']['statPerk1'],
                statPerk2=participant['stats']['statPerk2'],
            )

            participants.append(model.Participant(
                participant_id=str(uuid4()),
                team_id=teams[0].team_id if participant['participantId'] < 5 else teams[1].team_id,
                account_id=account_id,
                champion_id=participant['championId'],
                spell1_id=participant['spell1Id'],
                spell2_id=participant['spell2Id'],
                stat=stat,
                timeline=timeline,
            ))

        return model.Match(
            game_id=res['gameId'],
            platform_id=res['platformId'],
            game_creation=res['gameCreation'],
            game_duration=res['gameDuration'],
            queue_id=res['queueId'],
            map_id=res['mapId'],
            season_id=res['seasonId'],
            game_version=res['gameVersion'],
            game_mode=res['gameMode'],
            game_type=res['gameType'],
            teams=teams,
            participants=participants,
        )

    def get_matchlist_by_accountid(self,
                                   account_id: str,
                                   begin_index=None,
                                   end_index=None,
                                   ):
        res = self._request(method='GET',
                            url=self.routes.get_matchlist_by_accountid(account_id=account_id),
                            headers={'X-Riot-Token': self.config.token},
                            params={'beginIndex': begin_index,
                                    'endIndex': end_index,
                                    },
                            ).json()

        matches: typing.List[model.MatchReference] = []
        for entry in res['matches']:
            match = model.MatchReference(
                game_id=entry['gameId'],
                platform_id=entry['platformId'],
                lane=entry['lane'],
                role=entry['role'],
                season=entry['season'],
                champion=entry['champion'],
                queue=entry['queue'],
                timestamp=entry['timestamp'],
            )
            matches.append(match)

        return model.Matchlist(
            start_index=res['startIndex'],
            end_index=res['endIndex'],
            match_references=matches,
        )
