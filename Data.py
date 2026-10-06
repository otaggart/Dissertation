import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import time
from datetime import datetime, UTC

client_id = "c24wlxu46hqaep093nu1xvesscudt4"
client_secret = "os2smnm2j8mubg6psxw57gdtynoonl"

token_url = "https://id.twitch.tv/oauth2/token"
token_params = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "client_credentials",
}

token_response = requests.post(token_url, params=token_params)
print("TOKEN STATUS:", token_response.status_code)
print("TOKEN TEXT:", token_response.text)
token_response.raise_for_status()

access_token = token_response.json()["access_token"]

# --- IGDB helper ---
def igdb_get_game_modes(client_id1, access_token1):
    url = "https://api.igdb.com/v4/game_modes"
    headers = {
        "Client-ID": client_id1,
        "Authorization": f"Bearer {access_token1}",
        "Accept": "application/json",
    }
    body = "fields id,name,slug; limit 500;"
    r = requests.post(url, headers=headers, data=body)
    r.raise_for_status()
    return r.json()

def igdb_search_games_by_game_mode(client_id2, access_token2, game_mode_id, limit=50):
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id2,
        "Authorization": f"Bearer {access_token2}",
        "Accept": "application/json",
    }

    body = f"""
    fields name, first_release_date, platforms.name, game_modes.name, player_perspectives.name, url;
    where game_modes = ({game_mode_id}) & first_release_date >= 1421280000;
    sort first_release_date asc;
    limit {limit};
    """

    r = requests.post(url, headers=headers, data=body)
    r.raise_for_status()
    return r.json()



# --- TVTropes helper ---
def scrape_tropes_from_tvtropes(url):
    try:
        r = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        webpage = urlopen(r).read()
        print(f"Status for {url}: {r.status_code}")

        if webpage.status_code != 200:
            print(f"Failed: {url}")
            return []

        soup = BeautifulSoup(webpage, "html.parser")

        tropes = set()

        #li_elements = soup.find_all("li")
        #for i, li in enumerate(li_elements, start=1):
            #print(f"{i}: {li.get_text(strip=True)}")

        for a in soup.select("a[href*='/pmwiki/pmwiki.php/Main/']"):
            trope = a.get_text(strip=True)


            if trope and 2 < len(trope) < 40:
                tropes.add(trope)


        if len(tropes) == 0:
            print(f"CHECK MANUALLY: {title}")

        return list(tropes)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

modes = igdb_get_game_modes(client_id, access_token)
modes_df = pd.DataFrame(modes)


battle_mode_id = int(modes_df[modes_df["name"].str.contains("battle", case=False, na=False)].iloc[0]["id"])

games = igdb_search_games_by_game_mode(client_id, access_token, battle_mode_id)

import re

def format_title_for_tvtropes(title):
    # remove non-alphanumeric characters
    title = re.sub(r'[^A-Za-z0-9 ]', '', title)
    # remove spaces
    return title.replace(" ", "")

def get_tvtropes_url(title):
    formatted = format_title_for_tvtropes(title)
    return f"https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/{formatted}"

def convert_timestamp_to_year(timestamp):
    try:
        return datetime.fromtimestamp(timestamp, UTC).year
    except:
        return None

rows = []

for game in games:
    title = game.get("name")
    tvtropes_url = get_tvtropes_url(title)

    print(f"Scraping: {title}")

    tropes = scrape_tropes_from_tvtropes(tvtropes_url)
    time.sleep(1)

    rows.append({
        "title": title,
        "release_year": convert_timestamp_to_year(game.get("first_release_date")),
        "source_url": tvtropes_url,
        "tropes": ";".join(tropes)
    })
df = pd.DataFrame(rows)
df.to_csv("battle_royale_games.csv", index=False)
print(df.head())