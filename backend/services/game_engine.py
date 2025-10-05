from .power import fetch_daily_power_data
from config.config import GAME_CONFIG
from schemas.gameSession import GameSession, PlayerAction, StageResult, StageSnapshot, CumulativeState
import os
import json
import math
from datetime import datetime 

# This game has 2 types of parameters:
# 1. Static parameters: These parameters are fixed and do not change during the game. They include:
#    - Location: The geographical location where the game is played, defined by its name, longitude, and latitude.
#    - Total Turns: The total number of turns in the game.
#    - Stages: Different stages of the game, each defined by a name and a range of turns.
#    - Seasons: Different seasons in the game, each defined by a name, start date, and end date.
# 2. Dynamic parameters: These parameters can change during the game based on player actions and game events. They include:
#    - Weather Data: Daily weather data fetched from the NASA POWER API, which can influence game mechanics.
#    - Player Actions: Choices made by players that can affect game outcomes, they include:
#         + Seasons Selection: Players can choose different seasons to play in, which affects the weather conditions and crop growth.
#         + Water Regime:     
#         + Fertilizer Usage: Types and amounts of fertilizers used by players, which can impact crop growth and environmental effects.
#         + 

# Outcome: Minimizing CH4 emissions + N2O emission - Biomass   


class GameEngineError(Exception):
    """
    Custom exception for game engine errors. 
    """
    pass 


class GameEngine:
    """
    The core logic engine for this game.

    Usage:
    1. Fetch the current game state (GameSession instance) from the database.
    2. Create an instance of GameEngine with the player's actions for the current turn.
    3. Get the weather data for the current turn from the database.
    4. Process the turn using the particular method. 
    5. Update the game state in the database with the results.
    """

    def __init__(self, session: GameSession):
        self.session = session
        self.location = GAME_CONFIG['location']
        self.total_stages = GAME_CONFIG['total_stages']
        self.stages = GAME_CONFIG['stages']
        self.seasons = GAME_CONFIG['seasons']
        self.current_stage = len(session.game_history) + 1

    def _calculate_sf_w(self, water_regime, weather_data, stage_num, F):
        """
        Calculate scaling factor for water regime (SF_w)

        Args:
            water_regime (str): The water regime chosen by the player, e.g., 'traditional technique', 'AWD', 'Regular rainfed'.
            weather_data (dict): Dictionary containing weather data for the current stage
            stage_num (int): The current stage number (1, 2, 3, or 4)
            F (float): The level of flooding

        Returns:
            float: Scaling factor for water regime (SF_w)
        """

        # Default value
        SF_w = 1.0 

        a = {
            1: {
                'traditional_technique': 0.458694426,
                'AWD': 0.230519965,
                'regular_rainfed': 0.504341353,
            },
            2: {
                'traditional_technique': 0.970718789,
                'AWD': 0.411157427,
                'regular_rainfed': 0.296820827,
            },
            3: {
                'traditional_technique': 0.562444389,
                'AWD': 0.335273617,
                'regular_rainfed': 0.44668872,
            },
            4: {
                'traditional_technique': 1.120955286,
                'AWD': 0.436334021,
                'regular_rainfed': 1.22391098,
            }
        }
        b = {
            1: {
                'traditional_technique': 0.043251497,
                'AWD': 0.052121708,
                'regular_rainfed': 0.023009281,
            },
            2: {
                'traditional_technique': 3.08017e-07,
                'AWD': 0.036009981,
                'regular_rainfed': 0.048356805,
            },
            3: {
                'traditional_technique': 0.032842182,
                'AWD': 0.04353807,
                'regular_rainfed': 0.034148876,
            },
            4: {
                'traditional_technique': 2.23181E-14,
                'AWD': 0.037913224,
                'regular_rainfed': 2.25066E-14,
            }
        }
        c = {
            1: {
                'traditional_technique': 0.002195157,
                'AWD': 0.001862591,
                'regular_rainfed': 0.002453813,
            },
            2: {
                'traditional_technique': 2.22064E-14,
                'AWD': 2.26313E-14,
                'regular_rainfed': 2.28332E-14,
            },
            3: {
                'traditional_technique': 0.022408331,
                'AWD': 0.011566927,
                'regular_rainfed': 0.013843375,
            },
            4: {
                'traditional_technique': 0.007893869,
                'AWD': 0.009102005,
                'regular_rainfed': 0.008256156,
            }
        }
        d = {
            1: {
                'traditional_technique': 0.128416648,
                'AWD': 0.090983292,
                'regular_rainfed': 0.105923764,
            },
            2: {
                'traditional_technique': 0.129716815,
                'AWD': 0.724674735,
                'regular_rainfed': 2.614438373,
            },
            3: {
                'traditional_technique': 0.032354655,
                'AWD': 0.082440357,
                'regular_rainfed': 0.24326874,
            },
            4: {
                'traditional_technique': 0.794350362,
                'AWD': 0.107006198,
                'regular_rainfed': 0.399764521,
            }
        }
        e = {
            1: {
                'traditional_technique': 3.61328E-05,
                'AWD': 3.67026E-06,
                'regular_rainfed': 0.050536831,
            },
            2: {
                'traditional_technique': 0.370910015,
                'AWD': 2.22045E-14,
                'regular_rainfed': 0.031503649,
            },
            3: {
                'traditional_technique': 0.146150479,
                'AWD': 4.8745E-06,
                'regular_rainfed': 0.044627836,
            },
            4: {
                'traditional_technique': 0.423227968,
                'AWD': 3.53414E-05,
                'regular_rainfed': 0.166725189,
            }
        }

        print(weather_data)

        SF_w = a[stage_num][water_regime] * math.exp(b[stage_num][water_regime] * weather_data['avg_temp_c']) * (1 + c[stage_num][water_regime] * weather_data['total_rainfall_mm']) * (1 / (1 + math.exp(-d[stage_num][water_regime] * weather_data['avg_humidity_percent']))) * (1 / (1 + math.exp(-e[stage_num][water_regime] * F)))         

        return SF_w

    def _calculate_sf_o(self, organic_fertilizer_types):
        """
        Calculate scaling factor for organic amendments (SF_o)

        Args:
            organic_fertilizer_types (dict): Dictionary of organic fertilizer types and their amounts

            There are 5 types of organic fertilizers:
                - Type 1: Straw incorporated shortly before cultivation
                - Type 2: Straw incorporated long before cultivation
                - Type 3: Compost 
                - Type 4: Farm yard manure
                - Type 5: Green manure 
        Returns:
            float: Scaling factor for organic amendments (SF_o)
        """
        # Default value
        SF_o = 1.0

        # Mapping of organic fertilizer types to their respective conversion factors (CFOA)
        sf_o_mapping = {
            "Straw_short": 1.00,
            "Straw_long": 0.19,
            "Compost": 0.17,
            "Farm_yard_manure": 0.21,
            "Green_manure": 0.45,
        }

        for fert_type, fert_amount in organic_fertilizer_types.items():
            if fert_type in sf_o_mapping:
                SF_o_i = fert_amount * sf_o_mapping[fert_type]
                SF_o += SF_o_i ** 0.59

        return SF_o 

    def _calculate_ch4_emission(self, weather_data, water_regime, organic_fertilizer_types, F, time, area = 1.0):
        """
        Calculate CH4 emission for rice based on IPCC formula (kg CH4/ha)

        Args:
            time (int): Growth period in days (typically 120 days for rice), default is 120 days
            area (float): Area in hectares, default is 1.0 hectares 
        """

        # Emission factor baseline for continuously flooded rice fields without organic at Southeast Asia
        EF_c = {
            "dong-xuan": 1.95,
            "he-thu": 1.83,
            "thu-dong": 2.20,
        } # kg CH4/ha/day

        # Scaling factor for water regime during cultivation period
        SF_w = self._calculate_sf_w(water_regime, weather_data, self.current_stage, F)

        # Scaling factor for water regime pre-cultivation period
        SF_p = 1.0 # any default value

        # Scaling factor for organic amendments
        SF_o = self._calculate_sf_o(organic_fertilizer_types)

        # Scaling factor for soil type
        SF_s = 1.0 # default value

        # Scaling factor for rice cultivar 
        SF_r = 1.0 # default value 

        ch4_emission = EF_c[self.session.season_key] * SF_w * SF_p * SF_o * SF_s * SF_r * time * area
        
        return ch4_emission
    
    def _calculate_n2o_emission(self, synthetic_fertilizer_types):
        """
        Calculate N2O emission for rice based on IPCC formula (kg N2O/ha)

        Args:
            synthetic_fertilizer_types (dict): Dictionary of synthetic fertilizer types and their amounts

            There are 9 types of synthetic fertilizers:
                - Type 1: Urea
                - Type 2: Diammonium phosphate
                - Type 3: Ammonium sulphate
                - Type 4: Ammonium chloride
                - Type 5: Ammonium nitrate
                - Type 6: Superphosphate 
                - Type 7: Kali
                - Type 8: NPK in stage 2 (NPK_de_nhanh)
                - Type 9: NPK in stage 3 (NPK_lam_rong)
        
        Returns:
            float: N2O emission for rice (kg N2O/ha)
        """

        if not synthetic_fertilizer_types:
            return 0.0

        F_SN = {
            "Urea": 0.46,
            "Diammonium_phosphate": 0.18,
            "Ammonium_sulphate": 0.21,
            "Ammonium_chloride": 0.25,
            "Ammonium_nitrate": 0.35,
            "Lân": 0,
            "Kali": 0,
            "NPK_de_nhanh": 0.2,
            "NPK_lam_rong": 0.15,
        }

        EF_1i = {
            "dong-xuan": 0.15,
            "he-thu": 0.2,
            "thu-dong": 0.17,
        }

        F_CR = 24.57 # kg/ha - default value   

        EF_1 = 0.01 

        n2o_emission = 0.0

        for fert_type, fert_amount in synthetic_fertilizer_types.items():
            if fert_type in F_SN:
                F_sn_i = fert_amount * F_SN[fert_type]
                n2o_emission += F_sn_i

        n2o_emission = n2o_emission * EF_1i[self.session.season_key] + F_CR * EF_1

        return n2o_emission
    
    def _get_current_stage_name(self, current_stage_num: int) -> str:
        return self.stages[current_stage_num]
    
    def _get_previous_cumulative_state(self) -> CumulativeState:
        # The first stage 
        if not self.session.game_history:
            return CumulativeState(
                cumulative_ch4_emission=0.0,
                cumulative_n2o_emission=0.0,
                cumulative_emission=0.0
            )
        
        # Other stages (2nd, 3rd, ...)
        return self.session.game_history[-1].cumulative_state
    
    def _calculate_stage_result(self, player_action: PlayerAction, weather_data: dict, prev_state: CumulativeState) -> StageResult:
        """
        Calculate the results of a single stage based on player actions and weather data.

        Args:
            player_action (PlayerAction): The actions taken by the player in this stage.
            weather_data (dict): The weather data for this stage.
            prev_state (CumulativeState): The cumulative state from the previous stage.
        
        Returns:
            StageResult: The calculated results for this stage.
        """ 
        # Parse player actions
        if not player_action:
            raise GameEngineError("Player action is required to calculate stage results.")
        
        player_action = player_action.dict()
        
        player_action_type = player_action['player_action']

        if not player_action_type['fertilization']:
            raise GameEngineError("Fertilization action is required.")
        
        organic_fertilizer_types = player_action_type['fertilization']['organic_fertilizer']
        synthetic_fertilizer_types = player_action_type['fertilization']['synthetic_fertilizer']
        irrigation = player_action_type['irrigation'] 

        time = 28 # days

        area = 1 # hectares

        curr_stage_ch4_emission = self._calculate_ch4_emission(
            weather_data, self.session.water_regime, organic_fertilizer_types, irrigation['level'], time, area
        )

        curr_stage_n2o_emission = self._calculate_n2o_emission(
            synthetic_fertilizer_types
        )

        return StageResult(
            ch4_emission = curr_stage_ch4_emission,
            n2o_emission = curr_stage_n2o_emission
        )
    
    def play_stage(self, player_actions: PlayerAction, weather_data: dict) -> GameSession:
        """
        Process a single turn of the game. This is the main public method. 

        Args:
            player_actions (PlayerAction): The actions taken by the player in this turn.
            weather_data (dict): The weather data for this turn.

        Returns:
            GameSession: Updated game session with the results of this turn.
        """

        if self.session.status != "in_progress":
            raise GameEngineError(f'Game is not in progress. Current status: {self.session.status}')
        
        if self.current_stage > self.total_stages:
            raise GameEngineError(f'All stages have been played. Total turns: {self.total_stages}')
        
        previous_state = self._get_previous_cumulative_state()

        # --- Calculate stage results --- 
        curr_stage_result = self._calculate_stage_result(player_actions, weather_data, previous_state)

        # --- Update cumulative state ---
        curr_stage_total_emission = curr_stage_result.ch4_emission * 27 + curr_stage_result.n2o_emission * 273 # kg CO2e
        new_cumulative_state = CumulativeState(
            cumulative_ch4_emission= previous_state.cumulative_ch4_emission + curr_stage_result.ch4_emission,
            cumulative_n2o_emission= previous_state.cumulative_n2o_emission + curr_stage_result.n2o_emission,
            cumulative_emission= previous_state.cumulative_emission + curr_stage_total_emission
        )

        # --- Create stage snapshot ---
        curr_stage_snapshot = StageSnapshot(
            stage_number = self.current_stage,
            stage_name = self._get_current_stage_name(self.current_stage),
            player_action = player_actions,
            weather_conditions = weather_data,
            stage_result = curr_stage_result,
            cumulative_state = new_cumulative_state
        )

        # --- Update game session ---
        self.session.game_history.append(curr_stage_snapshot)

        # If this was the last stage, finalize the game
        if self.current_stage == self.total_stages:
            self.session.status = "completed"
            self.session.end_time = datetime.utcnow()

            self.session.final_metrics = {
                "final_net_emission": new_cumulative_state.cumulative_emission
            }

        return self.session 
