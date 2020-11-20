import dataclasses
import requests
import time

try:
    import dtos.summoner
    import dtos.match
    import dtos.matchlist
    import dtos.match_timeline
    import model
    import util
except ModuleNotFoundError:
    print('common package not in python path')


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
                             match_id: int):
        return util.urljoin(self.endpoint,
                            f'/lol/match/v4/matches/{match_id}',
                            )

    def get_match_timeline_by_matchid(self,
                                      match_id: str):
        return util.urljoin(self.endpoint,
                            f'/lol/match/v4/timelines/by-match/{match_id}',
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
                                     ):
        res = self._request(method='GET',
                            url=self.routes.get_summoner_by_summonername(summoner_name=summoner_name),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()
        return dtos.summoner.SummonerDto(
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
        return dtos.summoner.SummonerDto(
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
        return dtos.summoner.SummonerDto(
            account_id=res['accountId'],
            id=res['id'],
            puuid=res['puuid'],
            name=res['name'],
            profile_icon_id=res['profileIconId'],
            revision_date=res['revisionDate'],
            summoner_level=res['summonerLevel'],
        )

    def get_match_by_matchid(self,
                             match_id: int,
                             ) -> dtos.match.MatchDto:

        res = self._request(method='GET',
                            url=self.routes.get_match_by_matchid(match_id=match_id),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()

        participant_identities = []
        for participant_identity_raw in res['participantIdentities']:
            player = dtos.match.PlayerDto(
                profile_icon=participant_identity_raw['player']['profileIcon'],
                account_id=participant_identity_raw['player']['accountId'],
                match_history_uri=participant_identity_raw['player']['matchHistoryUri'],
                current_account_id=participant_identity_raw['player']['currentAccountId'],
                current_platform_id=participant_identity_raw['player']['currentPlatformId'],
                summoner_name=participant_identity_raw['player']['summonerName'],
                summoner_id=participant_identity_raw['player']['summonerId'],
                platform_id=participant_identity_raw['player']['platformId'],
            )
            participant_identities.append(dtos.match.ParticipantIdentityDto(
                participant_id=participant_identity_raw['participantId'],
                player=player,
            ))

        teams = []
        for team_raw in res['teams']:
            bans = []
            for ban_dto in team_raw['bans']:
                bans.append(dtos.match.TeamBansDto(
                    champion_id=ban_dto['championId'],
                    pick_turn=ban_dto['pickTurn'],
                ))

            teams.append(dtos.match.TeamStatsDto(
                tower_kills=team_raw['towerKills'],
                rift_herald_kills=team_raw['riftHeraldKills'],
                first_blood=team_raw['firstBlood'],
                inhibitor_kills=team_raw['inhibitorKills'],
                bans=bans,
                first_baron=team_raw['firstBaron'],
                first_dragon=team_raw['firstDragon'],
                dominion_victory_score=team_raw['dominionVictoryScore'],
                dragon_kills=team_raw['dragonKills'],
                baron_kills=team_raw['baronKills'],
                first_inhibitor=team_raw['firstInhibitor'],
                first_tower=team_raw['firstTower'],
                vilemaw_kills=team_raw['vilemawKills'],
                first_rift_herald=team_raw['firstRiftHerald'],
                team_id=team_raw['teamId'],
                win=team_raw['win'],
            ))

        participants = []
        for participant_raw in res['participants']:
            runes = []
            try:
                for rune_raw in participant_raw['runes']:
                    runes.append(dtos.match.RuneDto(
                        rune_id=rune_raw['runeId'],
                        rank=rune_raw['rank'],
                    ))
            except KeyError:
                # List of legacy Rune information. Not included for matches played with Runes Reforged.
                pass
            stats = dtos.match.ParticipantStatsDto(
                item0=participant_raw['stats']['item0'],
                item2=participant_raw['stats']['item2'],
                total_units_healed=participant_raw['stats']['totalUnitsHealed'],
                item1=participant_raw['stats']['item1'],
                largest_multi_kill=participant_raw['stats']['largestMultiKill'],
                gold_earned=participant_raw['stats']['goldEarned'],
                first_inhibitor_kill=participant_raw['stats']['firstInhibitorKill'],
                physical_damage_taken=participant_raw['stats']['physicalDamageTaken'],
                node_neutralize_assist=participant_raw['stats']['nodeNeutralizeAssist'],
                total_player_score=participant_raw['stats']['totalPlayerScore'],
                champ_level=participant_raw['stats']['champLevel'],
                damage_dealt_to_objectives=participant_raw['stats']['damageDealtToObjectives'],
                total_damage_taken=participant_raw['stats']['totalDamageTaken'],
                neutral_minions_killed=participant_raw['stats']['neutralMinionsKilled'],
                deaths=participant_raw['stats']['deaths'],
                triple_kills=participant_raw['stats']['tripleKills'],
                magic_damage_dealt_to_champions=participant_raw['stats']['magicDamageDealtToChampions'],
                wards_killed=participant_raw['stats']['wardsKilled'],
                penta_kills=participant_raw['stats']['pentaKills'],
                damage_self_mitigated=participant_raw['stats']['damageSelfMitigated'],
                largest_critical_strike=participant_raw['stats']['largestCriticalStrike'],
                node_neutralize=participant_raw['stats']['nodeNeutralize'],
                total_time_crowd_control_dealt=participant_raw['stats']['totalTimeCrowdControlDealt'],
                first_tower_kill=participant_raw['stats']['firstTowerKill'],
                magic_damage_dealt=participant_raw['stats']['magicDamageDealt'],
                total_score_rank=participant_raw['stats']['totalScoreRank'],
                node_capture=participant_raw['stats']['nodeCapture'],
                wards_placed=participant_raw['stats']['wardsPlaced'],
                total_damage_dealt=participant_raw['stats']['totalDamageDealt'],
                time_ccing_others=participant_raw['stats']['timeCCingOthers'],
                magical_damage_taken=participant_raw['stats']['magicalDamageTaken'],
                largest_killing_spree=participant_raw['stats']['largestKillingSpree'],
                total_damage_dealt_to_champions=participant_raw['stats']['totalDamageDealtToChampions'],
                physical_damage_dealt_to_champions=participant_raw['stats']['physicalDamageDealtToChampions'],
                neutral_minions_killed_team_jungle=participant_raw['stats']['neutralMinionsKilledTeamJungle'],
                total_minions_killed=participant_raw['stats']['totalMinionsKilled'],
                first_inhibitor_assist=participant_raw['stats']['firstInhibitorAssist'],
                vision_wards_bought_in_game=participant_raw['stats']['visionWardsBoughtInGame'],
                objective_player_score=participant_raw['stats']['objectivePlayerScore'],
                kills=participant_raw['stats']['kills'],
                first_tower_assist=participant_raw['stats']['firstTowerAssist'],
                combat_player_score=participant_raw['stats']['combatPlayerScore'],
                inhibitor_kills=participant_raw['stats']['inhibitorKills'],
                turret_kills=participant_raw['stats']['turretKills'],
                participant_id=participant_raw['stats']['participantId'],
                true_damage_taken=participant_raw['stats']['trueDamageTaken'],
                first_blood_assist=participant_raw['stats']['firstBloodAssist'],
                node_capture_assist=participant_raw['stats']['nodeCaptureAssist'],
                assists=participant_raw['stats']['assists'],
                team_objective=participant_raw['stats']['teamObjective'],
                altars_neutralized=participant_raw['stats']['altarsNeutralized'],
                gold_spent=participant_raw['stats']['goldSpent'],
                damage_dealt_to_turrets=participant_raw['stats']['damageDealtToTurrets'],
                altars_captured=participant_raw['stats']['altarsCaptured'],
                win=participant_raw['stats']['win'],
                total_heal=participant_raw['stats']['totalHeal'],
                unreal_kills=participant_raw['stats']['unrealKills'],
                vision_score=participant_raw['stats']['visionScore'],
                physical_damage_dealt=participant_raw['stats']['physicalDamageDealt'],
                first_blood_kill=participant_raw['stats']['firstBloodKill'],
                longest_time_spent_living=participant_raw['stats']['longestTimeSpentLiving'],
                killing_sprees=participant_raw['stats']['killingSprees'],
                sight_wards_bought_in_game=participant_raw['stats']['sightWardsBoughtInGame'],
                true_damage_dealt_to_champions=participant_raw['stats']['trueDamageDealtToChampions'],
                neutral_minions_killed_enemy_jungle=participant_raw['stats']['neutralMinionsKilledEnemyJungle'],
                double_kills=participant_raw['stats']['doubleKills'],
                true_damage_dealt=participant_raw['stats']['trueDamageDealt'],
                quadra_kills=participant_raw['stats']['quadraKills'],
                item4=participant_raw['stats']['item4'],
                item3=participant_raw['stats']['item3'],
                item6=participant_raw['stats']['item6'],
                item5=participant_raw['stats']['item5'],
                player_score0=participant_raw['stats']['playerScore0'],
                player_score1=participant_raw['stats']['playerScore1'],
                player_score2=participant_raw['stats']['playerScore2'],
                player_score3=participant_raw['stats']['playerScore3'],
                player_score4=participant_raw['stats']['playerScore4'],
                player_score5=participant_raw['stats']['playerScore5'],
                player_score6=participant_raw['stats']['playerScore6'],
                player_score7=participant_raw['stats']['playerScore7'],
                player_score8=participant_raw['stats']['playerScore8'],
                player_score9=participant_raw['stats']['playerScore9'],
                perk0=participant_raw['stats']['perk0'],
                perk0_var1=participant_raw['stats']['perk0Var1'],
                perk0_var2=participant_raw['stats']['perk0Var2'],
                perk0_var3=participant_raw['stats']['perk0Var3'],
                perk1=participant_raw['stats']['perk1'],
                perk1_var1=participant_raw['stats']['perk1Var1'],
                perk1_var2=participant_raw['stats']['perk1Var2'],
                perk1_var3=participant_raw['stats']['perk1Var3'],
                perk2=participant_raw['stats']['perk2'],
                perk2_var1=participant_raw['stats']['perk2Var1'],
                perk2_var2=participant_raw['stats']['perk2Var2'],
                perk2_var3=participant_raw['stats']['perk2Var3'],
                perk3=participant_raw['stats']['perk3'],
                perk3_var1=participant_raw['stats']['perk3Var1'],
                perk3_var2=participant_raw['stats']['perk3Var2'],
                perk3_var3=participant_raw['stats']['perk3Var3'],
                perk4=participant_raw['stats']['perk4'],
                perk4_var1=participant_raw['stats']['perk4Var1'],
                perk4_var2=participant_raw['stats']['perk4Var2'],
                perk4_var3=participant_raw['stats']['perk4Var3'],
                perk5=participant_raw['stats']['perk5'],
                perk5_var1=participant_raw['stats']['perk5Var1'],
                perk5_var2=participant_raw['stats']['perk5Var2'],
                perk5_var3=participant_raw['stats']['perk5Var3'],
                perk_primary_style=participant_raw['stats']['perkPrimaryStyle'],
                perk_sub_style=participant_raw['stats']['perkSubStyle'],
                stat_perk0=participant_raw['stats']['statPerk0'],
                stat_perk1=participant_raw['stats']['statPerk1'],
                stat_perk2=participant_raw['stats']['statPerk2'],
            )
            # the following deltas seem optional, therefore the inline if's
            timeline = dtos.match.ParticipantTimelineDto(
                participant_id=participant_raw['timeline']['participantId'],
                cs_diff_per_min_deltas=participant_raw['timeline']['csDiffPerMinDeltas'] if 'csDiffPerMinDeltas' in participant_raw['timeline'] else None,
                damage_taken_per_min_deltas=participant_raw['timeline']['damageTakenPerMinDeltas'] if 'damageTakenPerMinDeltas' in participant_raw['timeline'] else None,
                role=participant_raw['timeline']['role'],
                damage_taken_diff_per_min_deltas=participant_raw['timeline']['damageTakenDiffPerMinDeltas'] if 'damageTakenDiffPerMinDeltas' in participant_raw['timeline'] else None,
                xp_per_min_deltas=participant_raw['timeline']['xpPerMinDeltas'] if 'xpPerMinDeltas' in participant_raw['timeline'] else None,
                xp_diff_per_min_deltas=participant_raw['timeline']['xpDiffPerMinDeltas'] if 'xpDiffPerMinDeltas' in participant_raw['timeline'] else None,
                lane=participant_raw['timeline']['lane'],
                creeps_per_min_deltas=participant_raw['timeline']['creepsPerMinDeltas'] if 'creepsPerMinDeltas' in participant_raw['timeline'] else None,
                gold_per_min_deltas=participant_raw['timeline']['goldPerMinDeltas'] if 'goldPerMinDeltas' in participant_raw['timeline'] else None,
            )
            masteries = []
            try:
                for masteries_raw in participant_raw['masteries']:
                    masteries.append(dtos.match.MasteryDto(
                        rank=masteries_raw['rank'],
                        master_id=masteries_raw['MasterId'],
                    ))
            except KeyError:
                # List of legacy Mastery information. Not included for matches played with Runes Reforged.
                pass
            participants.append(dtos.match.ParticipantDto(
                participant_id=participant_raw['participantId'],
                champion_id=participant_raw['championId'],
                runes=runes,
                stats=stats,
                team_id=participant_raw['teamId'],
                timeline=timeline,
                spell1_id=participant_raw['spell1Id'],
                spell2_id=participant_raw['spell2Id'],
                highest_achieved_season_tier=participant_raw['highestAchievedSeasonTier'],
                masteries=masteries,
            ))

        return dtos.match.MatchDto(
            game_id=match_id,
            participant_identities=participant_identities,
            queue_id=res['queueId'],
            game_type=res['gameType'],
            game_duration=res['gameDuration'],
            teams=teams,
            platform_id=res['platformId'],
            game_creation=res['gameCreation'],
            season_id=res['seasonId'],
            game_version=res['gameVersion'],
            map_id=res['mapId'],
            game_mode=res['gameMode'],
            participants=participants,
        )

    def get_matchlist_by_accountid(self,
                                   account_id: str,
                                   begin_index=0,
                                   end_index=100,
                                   ):
        res = self._request(method='GET',
                            url=self.routes.get_matchlist_by_accountid(account_id=account_id),
                            headers={'X-Riot-Token': self.config.token},
                            params={'beginIndex': begin_index,
                                    'endIndex': end_index,
                                    },
                            ).json()

        matches = []
        for match in res['matches']:
            matches.append(dtos.matchlist.MatchReferenceDto(
                game_id=match['gameId'],
                role=match['role'],
                season=match['season'],
                platform_id=match['platformId'],
                champion=match['champion'],
                queue=match['queue'],
                lane=match['lane'],
                timestamp=match['timestamp'],
            ))

        return dtos.matchlist.MatchlistDto(
            start_index=res['beginIndex'],
            total_games=res['totalGames'],
            end_index=res['endIndex'],
            matches=matches,
        )

    def get_match_timeline_by_matchid(self,
                                      match_id: str,
                                      ):
        res = self._request(method='GET',
                            url=self.routes.get_match_timeline_by_matchid(match_id=match_id),
                            headers={'X-Riot-Token': self.config.token},
                            ).json()

        frames = []
        for frame in res['frames']:
            participants_frames = {}
            for participants_frame_key in frame['participantsFrames'].keys():
                participants_frames[participants_frame_key] = dtos.match_timeline.MatchParticipantFrameDto(
                    participant_id=frame['participantsFrames'][participants_frame_key]['participantId'],
                    minions_killed=frame['participantsFrames'][participants_frame_key]['minionsKilled'],
                    team_score=frame['participantsFrames'][participants_frame_key]['teamScore'],
                    dominion_score=frame['participantsFrames'][participants_frame_key]['dominionScore'],
                    total_gold=frame['participantsFrames'][participants_frame_key]['totalGold'],
                    level=frame['participantsFrames'][participants_frame_key]['level'],
                    xp=frame['participantsFrames'][participants_frame_key]['xp'],
                    current_gold=frame['participantsFrames'][participants_frame_key]['currentGold'],
                    position=dtos.match_timeline.MatchPositionDto(
                        x=frame['participantsFrames'][participants_frame_key]['position']['x'],
                        y=frame['participantsFrames'][participants_frame_key]['position']['y'],
                    ),
                    jungle_minions_killed=frame['participantsFrames'][participants_frame_key]['jungleMinionsKilled'],
                )

            events = []
            for event in frame['events']:
                position = dtos.match_timeline.MatchPositionDto(
                    x=event['position']['x'],
                    y=event['position']['y'],
                )
                events.append(dtos.match_timeline.MatchEventDto(
                    lane_type=event['laneType'],
                    skill_slot=event['skillShot'],
                    ascended_type=event['ascendedType'],
                    creator_id=event['creatorId'],
                    after_id=event['afterId'],
                    event_type=event['eventType'],
                    type=event['type'],
                    level_up_type=event['levelUpType'],
                    ward_type=event['wardType'],
                    participant_id=event['participantId'],
                    tower_type=event['towerType'],
                    item_id=event['itemId'],
                    before_id=event['beforeId'],
                    point_captured=event['pointCaptured'],
                    monster_type=event['monsterType'],
                    monster_sub_type=event['monsterSubType'],
                    team_id=event['teamId'],
                    position=position,
                    killer_id=event['killerID'],
                    timestamp=event['timestamp'],
                    assisting_participant_ids=event['assisting_participant_ids'],
                    building_type=event['buildingType'],
                    victim_id=event['victimId'],
                ))

            frames.append(dtos.match_timeline.MatchFrameDto(
                participant_frames=participants_frames,
                events=events,
                timestamp=frame['timestamp'],
            ))

        return dtos.match_timeline.MatchTimelineDto(
            frames=frames,
            frame_interval=res['frameInterval']
        )
