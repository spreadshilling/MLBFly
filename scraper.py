import statsapi
import json
from datetime import datetime

def calculate_wrg(team_id):
    """Calculates Weighted Runs per Game (Season vs Last 10)"""
    # Fetch team season stats
    stats = statsapi.team_stats(team_id, group="hitting", type="season")
    # Parse out runs and games (simplified logic)
    # Note: statsapi returns formatted strings, you'll extract the raw numbers
    # For robust automation, you pull season runs / games played.
    # Then query the last 10 games via statsapi.schedule() to find runs scored.
    pass # implementation depends on specific statsapi dictionary structure

def get_todays_matchups():
    today = datetime.now().strftime("%Y-%m-%d")
    schedule = statsapi.schedule(date=today)
    
    matchups = []
    for game in schedule:
        if game['status'] != 'Scheduled':
            continue
            
        home_id = game['home_id']
        away_id = game['away_id']
        
        # Example data mapping structure
        matchup_data = {
            "homeTeam": game['home_abbreviation'],  # e.g., 'LAD'
            "awayTeam": game['away_abbreviation'],  # e.g., 'SDP'
            # You would populate these via helper functions querying the API
            "homeERA": get_pitcher_era(game.get('home_probable_pitcher')), 
            "awayERA": get_pitcher_era(game.get('away_probable_pitcher')),
            "homeSeasonRPG": 4.5, # Replace with calculate_wrg(home_id)
            "homeLast10RPG": 4.8, 
            # ... continue mapping your required variables
        }
        matchups.append(matchup_data)
        
    # Save the daily output to a JSON file
    with open('public/daily_matchups.json', 'w') as f:
        json.dump(matchups, f, indent=4)
        
    print(f"✅ Generated {len(matchups)} matchups for {today}")

if __name__ == "__main__":
    get_todays_matchups()
