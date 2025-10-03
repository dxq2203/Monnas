from .power import fetch_daily_power_data
from ..config import GAME_CONFIG
from ..models import GameSession, PlayerAction, StageResult, StageSnapshot, CumulativeState
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

    def _calculate_sf_w(self, season_key, water_regime, weather_data):
        """
        Calculate scaling factor for water regime (SF_w)

        Args:
            season_key (str): The key for the chosen season, e.g., 'dong-xuan'.
            water_regime (str): The water regime chosen by the player, e.g., 'traditional technique', 'AWD', 'Regular rainfed'.

        Returns:
            float: Scaling factor for water regime (SF_w)
        """

        # Default value
        SF_w = 0.0 

        a_0 = {}
        a_1 = {}
        a_2 = {}
        a_3 = {}
        a_4 = {}
        F = {}

        SF_w = a_0 + a_1 * weather_data[season_key]['avg_temp'] + a_2 * weather_data[season_key]['total_rainfall'] + a_3 * weather_data[season_key]['avg_humidity'] + a_4 * F         

        SF_w = math.exp(SF_w)

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

    def _calculate_ch4_emission(self, season_key, weather_data, water_regime, organic_fertilizer_types, time, area):
        """
        Calculate CH4 emission for rice based on IPCC formula (kg CH4/ha)

        Args:
            time (int): Growth period in days (typically 120 days for rice)
            area (float): Area in hectares
        """

        # Emission factor baseline for continuously flooded rice fields without organic at Southeast Asia
        EF_c = {
            "dong_xuan": 1.95,
            "he_thu": 1.83,
            "thu_dong": 2.20,
        } # kg CH4/ha/day

        # Scaling factor for water regime during cultivation period
        SF_w = self._calculate_sf_w(season_key, water_regime, weather_data)

        # Scaling factor for water regime pre-cultivation period
        SF_p = 1.0 # any default value

        # Scaling factor for organic amendments
        SF_o = self._calculate_sf_o(organic_fertilizer_types)

        # Scaling factor for soil type
        SF_s = 1.0 # default value

        # Scaling factor for rice cultivar 
        SF_r = 1.0 # default value 

        ch4_emission = EF_c * SF_w * SF_p * SF_o * SF_s * SF_r * time * area
        
        return ch4_emission
    
    def _calculate_n2o_emission(self, season_key, synthetic_fertilizer_types):
        """
        Calculate N2O emission for rice based on IPCC formula (kg N2O/ha)

        Args:
            synthetic_fertilizer_types (dict): Dictionary of synthetic fertilizer types and their amounts
        
        Returns:
            float: N2O emission for rice (kg N2O/ha)
        """

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
            "dong_xuan": 0.15,
            "he_thu": 0.2,
            "thu_dong": 0.17,
        }

        F_CR = 20 # kg/ha - mock data 

        EF_1 = 0.01 

        n2o_emission = 0.0

        for fert_type, fert_amount in synthetic_fertilizer_types.items():
            if fert_type in F_SN:
                F_sn_i = fert_amount * F_SN[fert_type]
                n2o_emission += F_sn_i

        n2o_emission = n2o_emission * EF_1i[season_key] + F_CR * EF_1

        return n2o_emission
    
    def _get_current_stage_name(self, current_stage_num: int) -> str:
        return self.stages[current_stage_num]
    
    def _get_previous_cumulative_state(self) -> CumulativeState:
        # The first stage 
        if not self.session.game_history:
            return CumulativeState(
                cumualative_ch4_emission=0.0,
                cumulative_n2o_emission=0.0
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
        # Mock-up calculations for demonstration purposes
        # this information will be extracted from player_action and weather_data in a real implementation
        organic_fertilizer_types={ 
            "Straw_short": 50,
            "Compost": 36
        }

        time = 32 # days

        area = 2.5 # hectares

        curr_stage_ch4_emission = self._calculate_ch4_emission(
            organic_fertilizer_types, time, area, weather_data 
        )

        curr_stage_n2o_emission = 36 

        return StageResult(
            ch4_emission = curr_stage_ch4_emission,
            n2o_emission = curr_stage_n2o_emission
        )
    
    def play_turn(self, player_actions: PlayerAction, weather_data: dict) -> GameSession:
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
