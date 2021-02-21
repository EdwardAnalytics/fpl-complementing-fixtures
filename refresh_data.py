import requests
import json
from datetime import datetime

# Get current date to timestamp data
date = datetime.today().strftime("%Y%m%d")

# Bootstrap-static
# Load JSON
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
data = requests.get(url)
data = data.json()

# Write JSON
path = f'data/bootstrap_static/bootstrap_static_{date}.json'
with open(path, 'w') as f:
    json.dump(data, f)

# Fixtures
# Load JSON
url = 'https://fantasy.premierleague.com/api/fixtures/'
data = requests.get(url)
data = data.json()

# Write JSON
path = f'data/fixtures/fixtures_{date}.json'
with open(path, 'w') as f:
    json.dump(data, f)
