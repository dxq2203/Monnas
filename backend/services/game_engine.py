from .power import fetch_daily_power_data
from ..config import GAME_CONFIG
from ..models import GameSession, PlayerAction, TurnResult, TurnSnapshot, CumulativeState
import os
import json
import math

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

    def _calculate_sf_o(self, organic_fertilizer_types):
        """
        Calculate scaling factor for organic amendments (SF_o)

        Args:
            organic_fertilizer_types (dict): Dictionary of organic fertilizer types and their amounts
        """
        # Default value
        SF_o = 1.0

        # Mapping of organic fertilizer types to their respective scaling factors
        sf_o_mapping = {
            "type1": 1.0,
            "type2": 0.8,
            "type3": 0.6
        }

        for fert_type, fert_amount in organic_fertilizer_types.items():
            if fert_type in sf_o_mapping:
                SF_o_i = fert_amount * sf_o_mapping[fert_type]
                SF_o += SF_o_i ** 0.59

        return SF_o 
    
    def _calculate_sf_w(self):
        pass 

    def _calculate_ch4_emission(self, organic_fertilizer_types, time, area):
        """
        Calculate CH4 emission for rice based on IPCC formula (kg CH4/ha)

        Args:
            time (int): Growth period in days (typically 120 days for rice)
            area (float): Area in hectares
        """

        # Emission factor baseline for continuously flooded rice fields without organic at Southeast Asia
        EF_c = 1.22 # kg CH4/ha/day

        # Scaling factor for water regime during cultivation period
        SF_w = self.calculate_sf_w()

        # Scaling factor for water regime pre-cultivation period
        SF_p = 1.0 # any default value

        # Scaling factor for organic amendments
        SF_o = self.calculate_sf_o(organic_fertilizer_types)

        # Scaling factor for soil type
        SF_s = 1.0 # default value

        # Scaling factor for rice cultivar 
        SF_r = 1.0 # default value 

        ch4_emission = EF_c * SF_w * SF_p * SF_o * SF_s * SF_r * time * area
        
        return ch4_emission
    
    def _get_current_stage_name(self, current_stage_num: int) -> str:
        return self.stages[current_stage_num]
    
    def _get_previous_cumulative_state(self) -> CumulativeState:
        # The first stage 
        if not self.session.game_history:
            return CumulativeState(
                cumualative_ch4_emission=0.0,
                cumulative_n2o_emission=0.0,
                cumulative_biomass=0.0
            )
        
        # Other stages (2nd, 3rd, ...)
        return self.session.game_history[-1].cumulative_state
    
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
        
        if self.current_turn > self.total_turns:
            raise GameEngineError(f'All turns have been played. Total turns: {self.total_turns}')