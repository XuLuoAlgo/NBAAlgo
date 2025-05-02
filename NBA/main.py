import os
import random
import time

import click
import pandas as pd
import requests
from bs4 import BeautifulSoup

from NBA.exceptions import ScraperException, RateLimitException

"""
Note that this site has a rate limit. The sleep timer is to ensure that we remain under the 
"""
YEARS = [str(year) for year in range(2020, 2016, -1)]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}
DATA_DIR = f"{os.getcwd()}/NBA/data"
os.makedirs(DATA_DIR, exist_ok=True)


def save_csv(csv_path: str, df: pd.DataFrame) -> None:
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        new_df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(
            subset=["date", "home_team", "visitor_team"]
        )
        new_df.to_csv(csv_path, index=False)
    else:
        df.to_csv(csv_path, index=False)
    
def get_df_from_response(response: requests.Response) -> pd.DataFrame:
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", id="schedule")
    games = []
    for row in table.tbody.find_all("tr"):
        if "class" in row.attrs and "thead" in row.attrs["class"]:
            continue
        cells = row.find_all("td")
        if len(cells) == 0:
            continue
        game = {
            "date": row.find("th").text,
            "start (ET)": cells[0].text,
            "visitor_team": cells[1].text,
            "visitor_pts": cells[2].text,
            "home_team": cells[3].text,
            "home_pts": cells[4].text,
            "overtime": cells[6].text,
            "attendance": cells[7].text,
            "game_duration": cells[8].text,
            "arena": cells[9].text,
        }
        games.append(game)

    df = pd.DataFrame(games)

    df["visitor_pts"] = pd.to_numeric(df["visitor_pts"], errors="coerce")
    df["home_pts"] = pd.to_numeric(df["home_pts"], errors="coerce")
    return df

def get_response(url: str) -> requests.Response:
    response = requests.get(url, headers=HEADERS)
    # sleep for random time
    time.sleep(random.randint(10, 30))
    if response.status_code == 200:
        return response
    if response.status_code == 429:
        raise RateLimitException
    elif response.status_code == 404:
        raise ScraperException("Could not find page for url:", url)
    else:
        raise ScraperException

def get_month_urls_from_response(response: requests.Response) -> list[str]:
    month_urls = []
    soup = BeautifulSoup(response.content, "html.parser")
    filters = soup.find("div", class_="filter")
    if not filters:
        raise ScraperException("Couldn't find months")
    tags = filters.find_all("a")
    for a in tags:
        if href := a.get("href"):
            month_urls.append(f"https://www.basketball-reference.com{href}")
    return month_urls


def main() -> None:
    for year in YEARS:
        csv_path = f"{DATA_DIR}/NBA_{year}_games.csv"
        if os.path.exists(csv_path) and not click.confirm(
            f"We already have data for the {year} NBA season. Would you like to update it?",
            os.path.exists(csv_path),
        ):
            continue

        base_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games.html"
        response = get_response(base_url)
        month_urls = get_month_urls_from_response(response)

        for url in month_urls:
            response = get_response(url)
            df = get_df_from_response(response)
            save_csv(csv_path, df)

if __name__ == "__main__":
    main()
