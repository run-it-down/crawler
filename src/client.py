import dataclasses
import requests
import time
import typing
from uuid import uuid4

from src import util, model

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

    def get_summoner_by_summoner_id(self,
                                    summoner_id: str,
                                    ):
        return util.urljoin(self.endpoint,
                            f'/lol/summoner/v4/summoners/{summoner_id}',
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
                 *args,
                 **kwargs):
        while True:
            res = requests.request(method=method,
                                   verify=False,
                                   *args, **kwargs)
            if res.ok:
                break
            else:
                if res.status_code != 429:
                    msg = f'{method} request to url {res.url} failed with {res.status_code=} {res.reason=}'
                    raise RiotAPINotOkayException(res=res, msg=msg)

                # triggered if quota limit is reached, add some delay to avoid firewall
                time.sleep(5)

        return res

    def get_summoner_by_summonername(self,
                                     summoner_name: str,
                                     print: bool = True,
                                     ):
        if print:
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

    def get_summoner_by_summoner_id(self,
                                    summoner_id: str,
                                    ):
        res = self._request(method='GET',
                            url=self.routes.get_summoner_by_summoner_id(summoner_id=summoner_id),
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

                    # edge case, if region changed there are inconsistencies regarding account
                    # id and sum name
                    if participant_idendity['player']['platformId'] != 'EUW1':
                        s = self.get_summoner_by_summoner_id(summoner_id=participant_idendity['player']['summonerId'],
                                                             )
                        account_id = s.account_id
                    else:
                        account_id = participant_idendity['player']['accountId']

            timeline = model.Timeline(
                timeline_id=str(uuid4()),
                creepsPerMinDeltas=participant['timeline']['creepsPerMinDeltas'] if 'creepsPerMinDeltas' in participant['timeline'].keys() else None,
                xpPerMinDeltas=participant['timeline']['xpPerMinDeltas'] if 'xpPerMinDeltas' in participant['timeline'].keys() else None,
                goldPerMinDeltas=participant['timeline']['goldPerMinDeltas'] if 'goldPerMinDeltas' in participant['timeline'].keys() else None,
                csDiffPerMinDeltas=participant['timeline']['csDiffPerMinDeltas'] if 'csDiffPerMinDeltas' in participant['timeline'].keys() else None,
                xpDiffPerMinDeltas=participant['timeline']['xpDiffPerMinDeltas'] if 'xpDiffPerMinDeltas' in participant['timeline'].keys() else None,
                damageTakenPerMinDeltas=participant['timeline']['damageTakenPerMinDeltas'] if 'damageTakenPerMinDeltas' in participant['timeline'].keys() else None,
                damageTakenDiffPerMinDeltas=participant['timeline']['damageTakenDiffPerMinDeltas'] if 'damageTakenDiffPerMinDeltas' in participant['timeline'].keys() else None,
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
                neutralMinionsKilledTeamJungle=participant['stats']['neutralMinionsKilledTeamJungle'] if 'neutralMinionsKilledTeamJungle' in participant['stats'].keys() else None,
                neutralMinionsKilledEnemyJungle=participant['stats']['neutralMinionsKilledEnemyJungle'] if 'neutralMinionsKilledEnemyJungle' in participant['stats'].keys() else None,
                totalTimeCrowdControlDealt=participant['stats']['totalTimeCrowdControlDealt'],
                champLevel=participant['stats']['champLevel'],
                visionWardsBoughtInGame=participant['stats']['visionWardsBoughtInGame'],
                sightWardsBoughtInGame=participant['stats']['sightWardsBoughtInGame'],
                wardsPlaced=participant['stats']['wardsPlaced'] if 'wardsPlaced' in participant['stats'].keys() else None,
                wardsKilled=participant['stats']['wardsKilled'] if 'wardsKilled' in participant['stats'].keys() else None,
                firstBloodKill=participant['stats']['firstBloodKill'] if 'firstBloodKill' in participant['stats'].keys() else None,
                firstBloodAssist=participant['stats']['firstBloodAssist'] if 'firstBloodAssist' in participant['stats'].keys() else None,
                firstTowerKill=participant['stats']['firstTowerKill'] if 'firstTowerKill' in participant['stats'].keys() else None,
                firstTowerAssist=participant['stats']['firstTowerAssist'] if 'firstTowerAssist' in participant['stats'].keys() else None,
                firstInhibitorKill=participant['stats']['firstInhibitorKill'] if 'firstInhibitorKill' in participant['stats'].keys() else None,
                firstInhibitorAssist=participant['stats']['firstInhibitorAssist'] if 'firstInhibitorAssist' in participant['stats'].keys() else None,
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
