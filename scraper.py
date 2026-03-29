import statsapi
import json
import logging
from datetime import datetime

# Set up logging so you can see what happens in GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# The MLB API sometimes uses slightly different 2- or 3-letter codes than your UI expects.
# This map ensures perfect compatibility with your PARK_FACTORS dictionary.
TEAM_MAP = {
    'AZ': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BOS': 'BOS', 'CWS': 'CWS',
    'CHC': 'CHC', 'CIN': 'CIN', 'CLE': 'CLE', 'COL': 'COL', 'DET': 'DET',
    'HOU': 'HOU', 'KC': 'KCR', 'LAA': 'LAA', 'LAD': 'LAD', 'MIA': 'MIA',
    'MIL': 'MIL', 'MIN': 'MIN', 'NYM': 'NYM', 'NYY': 'NYY', 'OAK': 'OAK',
    'PHI': 'PHI', 'PIT': 'PIT', 'SD': 'SDP', 'SF': 'SFG', 'SEA': 'SEA',
    'STL': 'STL', 'TB': 'TBR', 'TEX': 'TEX', 'TOR': 'TOR', 'WSH': 'WSN'
}

def get_normalized_team(api_abbrev):
    """Converts API abbreviations to your UI's expected format."""
    return TEAM_MAP.get(api_abbrev, api_abbrev)

def get_team_rpg(team_id):
    """Fetches season Runs Per Game for a given team."""
    try:
        stats = statsapi.team_stats(team_id, group="hitting", type="season")
        # statsapi returns a string block, we need to parse it
        # E.g., looks for 'runs' and 'gamesPlayed'
        lines = stats.split('\n')
        runs = 0
        games = 1
        for line in lines:
            if line.startswith('runs:'):
                runs = int(line.split(':')[1].strip())
            if line.startswith('gamesPlayed:'):
                games = int(line.split(':')[1].strip())
        
        rpg = runs / max(games, 1)
        return round(rpg, 2)
    except Exception as e:
        logging.warning(f"Could not fetch RPG for team {team_id}: {e}")
        return 4.5 # League average fallback

def get_team_era(team_id):
    """Fetches team season ERA as a fallback for starting pitchers."""
    try:
        stats = statsapi.team_stats(team_id, group="pitching", type="season")
        lines = stats.split('\n')
        for line in lines:
            if line.startswith('era:'):
                return float(line.split(':')[1].strip())
        return 4.00
    except Exception as e:
        logging.warning(f"Could not fetch ERA for team {team_id}: {e}")
        return 4.00 # League average fallback

def build_daily_matchups():
    today = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"Fetching schedule for {today}...")
    
    # Get today's games
    schedule = statsapi.schedule(date=today)
    matchups = []

    for game in schedule:
        # Skip postponed or cancelled games
        if game['status'] in ['Postponed', 'Cancelled']:
            continue
            
        home_abbrev = get_normalized_team(game['home_abbreviation'])
        away_abbrev = get_normalized_team(game['away_abbreviation'])
        home_id = game['home_id']
        away_id = game['away_id']

        logging.info(f"Processing matchup: {away_abbrev} @ {home_abbrev}")

        # Fetch hitting stats (Runs per Game)
        home_rpg = get_team_rpg(home_id)
        away_rpg = get_team_rpg(away_id)

        # Fetch pitching stats
        # Note: Getting exact daily SP ERA requires deep player stat parsing. 
        # For automation stability, we use overall team ERA as a highly reliable proxy.
        home_era = get_team_era(home_id)
        away_era = get_team_era(away_id)

        # Construct the JSON object matching your React state exactly
        matchup_data = {
            "homeTeam": home_abbrev,
            "awayTeam": away_abbrev,
            "homeSeasonRPG": home_rpg,
            "homeLast10RPG": home_rpg, # Defaulting to season avg for baseline
            "awaySeasonRPG": away_rpg,
            "awayLast10RPG": away_rpg, # Defaulting to season avg for baseline
            "homeERA": home_era,
            "awayERA": away_era,
            
            # --- Defaults for fields not provided by MLB Stats API ---
            # You can tweak these manually in your UI before running the sim
            "homeInnings3D": 9,
            "homeRelievers3D": 4,
            "awayInnings3D": 9,
            "awayRelievers3D": 4,
            "temperature": 72,
            "windSpeed": 5,
            "windHelping": False,
            "homeMarketOdds": -110,
            "awayMarketOdds": -110,
        }
        
        matchups.append(matchup_data)

    if not matchups:
        logging.warning("No valid matchups found for today. File will be empty.")
        
    # Write to JSON file
    output_file = 'daily_matchups.json'
    with open(output_file, 'w') as f:
        json.dump(matchups, f, indent=4)
        
    logging.info(f"✅ Successfully saved {len(matchups)} matchups to {output_file}")

if __name__ == "__main__":
    build_daily_matchups()
