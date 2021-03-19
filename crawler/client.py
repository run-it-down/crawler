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

    def __init__(
        self,
        endpoint: str,
    ):
        self.endpoint = endpoint

    def get_summoner_by_summonername(
        self,
        summoner_name: str,
    ):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/summoner/v4/summoners/by-name/', summoner_name),
        )

    def get_summoner_by_account_id(
        self,
        account_id: str,
    ):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/summoner/v4/summoners/by-account/', account_id),
        )

    def get_summoner_by_summoner_id(
        self,
        summoner_id: str,
    ):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/summoner/v4/summoners/', summoner_id),
        )

    def get_matchlist_by_accountid(
        self,
        account_id: str
    ):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/match/v4/matchlists/by-account/', account_id),
        )

    def get_match_by_matchid(
        self,
        match_id: int
    ):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/match/v4/matches/', match_id),
        )

    def get_match_timeline_by_matchid(
        self,
        match_id: str):
        return util.urljoin(
            self.endpoint,
            util.urljoin('/lol/match/v4/timelines/by-match/', match_id),
        )


@dataclasses.dataclass()
class ClientConfig:
    token: str


class RiotAPINotOkayException(Exception):
    def __init__(
        self,
        res: requests.Response,
        msg: str,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.res = res
        self.msg = msg


class Client:

    def __init__(
        self,
        config: ClientConfig,
        routes: ClientRoutes,
    ):
        self.config = config
        self.routes = routes

    def _request(
        self, method: str,
        *args,
        **kwargs,
    ):
        while True:
            res = requests.request(
                method=method,
                verify=False,
                *args,
                **kwargs,
            )
            if res.ok:
                break
            else:
                if res.status_code != 429:
                    msg = f'{method} request to url {res.url} failed with {res.status_code=} {res.reason=}'
                    raise RiotAPINotOkayException(res=res, msg=msg)

                # triggered if quota limit is reached, add some delay to avoid firewall
                time.sleep(5)

        return res

    def get_summoner_by_summonername(
        self,
        summoner_name: str,
    ):
        res = self._request(
            method='GET',
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

    def get_summoner_by_account_id(
        self,
        account_id: str,
    ):
        res = self._request(
            method='GET',
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

    def get_summoner_by_summoner_id(
        self,
        summoner_id: str,
    ):
        res = self._request(
            method='GET',
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

    def get_match_by_matchid(
        self,
        match_id: int,
    ) -> dtos.match.MatchDto:

        res = self._request(
            method='GET',
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
                item0=participant_raw['stats'].get('item0'),
                item2=participant_raw['stats'].get('item2'),
                total_units_healed=participant_raw['stats'].get('totalUnitsHealed'),
                item1=participant_raw['stats'].get('item1'),
                largest_multi_kill=participant_raw['stats'].get('largestMultiKill'),
                gold_earned=participant_raw['stats'].get('goldEarned'),
                first_inhibitor_kill=participant_raw['stats'].get('firstInhibitorKill'),
                physical_damage_taken=participant_raw['stats'].get('physicalDamageTaken'),
                node_neutralize_assist=participant_raw['stats'].get('nodeNeutralizeAssist'),
                total_player_score=participant_raw['stats'].get('totalPlayerScore'),
                champ_level=participant_raw['stats'].get('champLevel'),
                damage_dealt_to_objectives=participant_raw['stats'].get('damageDealtToObjectives'),
                total_damage_taken=participant_raw['stats'].get('totalDamageTaken'),
                neutral_minions_killed=participant_raw['stats'].get('neutralMinionsKilled'),
                deaths=participant_raw['stats'].get('deaths'),
                triple_kills=participant_raw['stats'].get('tripleKills'),
                magic_damage_dealt_to_champions=participant_raw['stats'].get('magicDamageDealtToChampions'),
                wards_killed=participant_raw['stats'].get('wardsKilled'),
                penta_kills=participant_raw['stats'].get('pentaKills'),
                damage_self_mitigated=participant_raw['stats'].get('damageSelfMitigated'),
                largest_critical_strike=participant_raw['stats'].get('largestCriticalStrike'),
                node_neutralize=participant_raw['stats'].get('nodeNeutralize'),
                total_time_crowd_control_dealt=participant_raw['stats'].get('totalTimeCrowdControlDealt'),
                first_tower_kill=participant_raw['stats'].get('firstTowerKill'),
                magic_damage_dealt=participant_raw['stats'].get('magicDamageDealt'),
                total_score_rank=participant_raw['stats'].get('totalScoreRank'),
                node_capture=participant_raw['stats'].get('nodeCapture'),
                wards_placed=participant_raw['stats'].get('wardsPlaced'),
                total_damage_dealt=participant_raw['stats'].get('totalDamageDealt'),
                time_ccing_others=participant_raw['stats'].get('timeCCingOthers'),
                magical_damage_taken=participant_raw['stats'].get('magicalDamageTaken'),
                largest_killing_spree=participant_raw['stats'].get('largestKillingSpree'),
                total_damage_dealt_to_champions=participant_raw['stats'].get('totalDamageDealtToChampions'),
                physical_damage_dealt_to_champions=participant_raw['stats'].get('physicalDamageDealtToChampions'),
                neutral_minions_killed_team_jungle=participant_raw['stats'].get('neutralMinionsKilledTeamJungle'),
                total_minions_killed=participant_raw['stats'].get('totalMinionsKilled'),
                first_inhibitor_assist=participant_raw['stats'].get('firstInhibitorAssist'),
                vision_wards_bought_in_game=participant_raw['stats'].get('visionWardsBoughtInGame'),
                objective_player_score=participant_raw['stats'].get('objectivePlayerScore'),
                kills=participant_raw['stats'].get('kills'),
                first_tower_assist=participant_raw['stats'].get('firstTowerAssist'),
                combat_player_score=participant_raw['stats'].get('combatPlayerScore'),
                inhibitor_kills=participant_raw['stats'].get('inhibitorKills'),
                turret_kills=participant_raw['stats'].get('turretKills'),
                participant_id=participant_raw['stats'].get('participantId'),
                true_damage_taken=participant_raw['stats'].get('trueDamageTaken'),
                first_blood_assist=participant_raw['stats'].get('firstBloodAssist'),
                node_capture_assist=participant_raw['stats'].get('nodeCaptureAssist'),
                assists=participant_raw['stats'].get('assists'),
                team_objective=participant_raw['stats'].get('teamObjective'),
                altars_neutralized=participant_raw['stats'].get('altarsNeutralized'),
                gold_spent=participant_raw['stats'].get('goldSpent'),
                damage_dealt_to_turrets=participant_raw['stats'].get('damageDealtToTurrets'),
                altars_captured=participant_raw['stats'].get('altarsCaptured'),
                win=participant_raw['stats'].get('win'),
                total_heal=participant_raw['stats'].get('totalHeal'),
                unreal_kills=participant_raw['stats'].get('unrealKills'),
                vision_score=participant_raw['stats'].get('visionScore'),
                physical_damage_dealt=participant_raw['stats'].get('physicalDamageDealt'),
                first_blood_kill=participant_raw['stats'].get('firstBloodKill'),
                longest_time_spent_living=participant_raw['stats'].get('longestTimeSpentLiving'),
                killing_sprees=participant_raw['stats'].get('killingSprees'),
                sight_wards_bought_in_game=participant_raw['stats'].get('sightWardsBoughtInGame'),
                true_damage_dealt_to_champions=participant_raw['stats'].get('trueDamageDealtToChampions'),
                neutral_minions_killed_enemy_jungle=participant_raw['stats'].get('neutralMinionsKilledEnemyJungle'),
                double_kills=participant_raw['stats'].get('doubleKills'),
                true_damage_dealt=participant_raw['stats'].get('trueDamageDealt'),
                quadra_kills=participant_raw['stats'].get('quadraKills'),
                item4=participant_raw['stats'].get('item4'),
                item3=participant_raw['stats'].get('item3'),
                item6=participant_raw['stats'].get('item6'),
                item5=participant_raw['stats'].get('item5'),
                player_score0=participant_raw['stats'].get('playerScore0'),
                player_score1=participant_raw['stats'].get('playerScore1'),
                player_score2=participant_raw['stats'].get('playerScore2'),
                player_score3=participant_raw['stats'].get('playerScore3'),
                player_score4=participant_raw['stats'].get('playerScore4'),
                player_score5=participant_raw['stats'].get('playerScore5'),
                player_score6=participant_raw['stats'].get('playerScore6'),
                player_score7=participant_raw['stats'].get('playerScore7'),
                player_score8=participant_raw['stats'].get('playerScore8'),
                player_score9=participant_raw['stats'].get('playerScore9'),
                perk0=participant_raw['stats'].get('perk0'),
                perk0_var1=participant_raw['stats'].get('perk0Var1'),
                perk0_var2=participant_raw['stats'].get('perk0Var2'),
                perk0_var3=participant_raw['stats'].get('perk0Var3'),
                perk1=participant_raw['stats'].get('perk1'),
                perk1_var1=participant_raw['stats'].get('perk1Var1'),
                perk1_var2=participant_raw['stats'].get('perk1Var2'),
                perk1_var3=participant_raw['stats'].get('perk1Var3'),
                perk2=participant_raw['stats'].get('perk2'),
                perk2_var1=participant_raw['stats'].get('perk2Var1'),
                perk2_var2=participant_raw['stats'].get('perk2Var2'),
                perk2_var3=participant_raw['stats'].get('perk2Var3'),
                perk3=participant_raw['stats'].get('perk3'),
                perk3_var1=participant_raw['stats'].get('perk3Var1'),
                perk3_var2=participant_raw['stats'].get('perk3Var2'),
                perk3_var3=participant_raw['stats'].get('perk3Var3'),
                perk4=participant_raw['stats']['perk4'],
                perk4_var1=participant_raw['stats'].get('perk4Var1'),
                perk4_var2=participant_raw['stats'].get('perk4Var2'),
                perk4_var3=participant_raw['stats'].get('perk4Var3'),
                perk5=participant_raw['stats'].get('perk5'),
                perk5_var1=participant_raw['stats'].get('perk5Var1'),
                perk5_var2=participant_raw['stats'].get('perk5Var2'),
                perk5_var3=participant_raw['stats'].get('perk5Var3'),
                perk_primary_style=participant_raw['stats'].get('perkPrimaryStyle'),
                perk_sub_style=participant_raw['stats'].get('perkSubStyle'),
                stat_perk0=participant_raw['stats'].get('statPerk0'),
                stat_perk1=participant_raw['stats'].get('statPerk1'),
                stat_perk2=participant_raw['stats'].get('statPerk2'),
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
                highest_achieved_season_tier=participant_raw.get('highestAchievedSeasonTier'),
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

    def get_matchlist_by_accountid(
        self,
        account_id: str,
        begin_index=0,
        end_index=100,
    ):
        res = self._request(
            method='GET',
            url=self.routes.get_matchlist_by_accountid(account_id=account_id),
            headers={'X-Riot-Token': self.config.token},
            params={
                'beginIndex': begin_index,
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
            start_index=res['startIndex'],
            total_games=res['totalGames'],
            end_index=res['endIndex'],
            matches=matches,
        )

    def get_match_timeline_by_matchid(
        self,
        match_id: str,
    ):
        res = self._request(
            method='GET',
            url=self.routes.get_match_timeline_by_matchid(match_id=match_id),
            headers={'X-Riot-Token': self.config.token},
        ).json()

        frames = []
        for frame in res['frames']:
            participants_frames = {}
            for participants_frame_key in frame['participantFrames'].keys():
                position = None
                if 'position' in frame['participantFrames'][participants_frame_key]:
                    position = dtos.match_timeline.MatchPositionDto(
                        x=frame['participantFrames'][participants_frame_key]['position']['x'],
                        y=frame['participantFrames'][participants_frame_key]['position']['y'],
                    )
                participants_frames[participants_frame_key] = dtos.match_timeline.MatchParticipantFrameDto(
                    participant_id=frame['participantFrames'][participants_frame_key].get('participantId'),
                    minions_killed=frame['participantFrames'][participants_frame_key].get('minionsKilled'),
                    team_score=frame['participantFrames'][participants_frame_key].get('teamScore'),
                    dominion_score=frame['participantFrames'][participants_frame_key].get('dominionScore'),
                    total_gold=frame['participantFrames'][participants_frame_key].get('totalGold'),
                    level=frame['participantFrames'][participants_frame_key].get('level'),
                    xp=frame['participantFrames'][participants_frame_key].get('xp'),
                    current_gold=frame['participantFrames'][participants_frame_key].get('currentGold'),
                    position=position,
                    jungle_minions_killed=frame['participantFrames'][participants_frame_key].get('jungleMinionsKilled'),
                )

            events = []
            for event in frame['events']:
                position = None
                if 'position' in event:
                    position = dtos.match_timeline.MatchPositionDto(
                        x=event['position']['x'],
                        y=event['position']['y'],
                    )
                events.append(dtos.match_timeline.MatchEventDto(
                    lane_type=event.get('laneType'),
                    skill_slot=event.get('skillShot'),
                    ascended_type=event.get('ascendedType'),
                    creator_id=event.get('creatorId'),
                    after_id=event.get('afterId'),
                    event_type=event.get('eventType'),
                    type=event.get('type'),
                    level_up_type=event.get('levelUpType'),
                    ward_type=event.get('wardType'),
                    participant_id=event.get('participantId'),
                    tower_type=event.get('towerType'),
                    item_id=event.get('itemId'),
                    before_id=event.get('beforeId'),
                    point_captured=event.get('pointCaptured'),
                    monster_type=event.get('monsterType'),
                    monster_sub_type=event.get('monsterSubType'),
                    team_id=event.get('teamId'),
                    position=position,
                    killer_id=event.get('killerId'),
                    timestamp=event.get('timestamp'),
                    assisting_participant_ids=event.get('assisting_participant_ids'),
                    building_type=event.get('buildingType'),
                    victim_id=event.get('victimId'),
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
