import aiohttp
from datetime import datetime, timedelta, timezone

from config import ESPN_BASE, LEAGUES

async def fetch_json(url):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=15) as r:
                return await r.json()
    except:
        return {}

def parse_match(event, league_code=""):
    try:
        comp = event.get("competitions")
        if not comp:
            return None
        comp = comp[0]
        competitors = comp.get("competitors")
        if not competitors or len(competitors) < 2:
            return None

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_id = home["team"].get("id", "")
        away_id = away["team"].get("id", "")
        home_team = home["team"].get("displayName", home["team"].get("name", "?"))
        away_team = away["team"].get("displayName", away["team"].get("name", "?"))
        home_score = home.get("score")
        away_score = away.get("score")

        st = comp.get("status", {}).get("type", {})
        state = st.get("state", "pre")
        detail = st.get("detail", "")
        clock = comp.get("status", {}).get("clock", 0)

        date_str = comp.get("date", event.get("date", ""))
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            match_time = dt.strftime("%H:%M")
            match_date = dt.strftime("%Y-%m-%d")
        except:
            match_time = ""
            match_date = ""

        odds = comp.get("odds", [{}])[0] if comp.get("odds") else {}
        home_odds = None
        away_odds = None
        draw_odds = None
        if odds:
            home_odds = odds.get("homeTeamOdds", {})
            home_odds = home_odds.get("value") if isinstance(home_odds, dict) else None
            away_odds = odds.get("awayTeamOdds", {})
            away_odds = away_odds.get("value") if isinstance(away_odds, dict) else None
            draw_odds = odds.get("drawOdds", {})
            draw_odds = draw_odds.get("value") if isinstance(draw_odds, dict) else None

        league_info = comp.get("league") or event.get("league") or {}
        league_name = league_info.get("name") or league_info.get("slug") or ""

        return {
            "id": event.get("id") or event.get("uid") or "",
            "home_id": home_id,
            "away_id": away_id,
            "league_code": league_code,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "state": state,
            "detail": detail,
            "clock": clock,
            "time": match_time,
            "date": match_date,
            "home_odds": home_odds,
            "away_odds": away_odds,
            "draw_odds": draw_odds,
            "league": league_name,
        }
    except:
        return None

def get_matches(data, league_code=""):
    events = data.get("events") or []
    matches = []
    for ev in events:
        m = parse_match(ev, league_code)
        if m:
            matches.append(m)
    return matches

async def get_scoreboard(league, date_str=None):
    url = f"{ESPN_BASE}/{league}/scoreboard"
    if date_str:
        url = f"{ESPN_BASE}/{league}/scoreboard?dates={date_str}"
    return await fetch_json(url)

async def get_all_matches_for_date(date_str):
    all_m = []
    for lig in LEAGUES:
        data = await get_scoreboard(lig, date_str)
        if data:
            all_m.extend(get_matches(data, lig))
    return all_m

async def get_team_schedule(league, team_id):
    url = f"{ESPN_BASE}/{league}/teams/{team_id}/schedule"
    return await fetch_json(url)

async def get_team_form(league, team_id, days_back=30):
    form = []
    today = datetime.now(timezone.utc)
    for d in range(days_back, 0, -1):
        dt = today - timedelta(days=d)
        ds = dt.strftime("%Y%m%d")
        data = await get_scoreboard(league, ds)
        if not data:
            continue
        for ev in data.get("events") or []:
            m = parse_match(ev, league)
            if not m or m["state"] != "post":
                continue
            if m["home_id"] == team_id or m["away_id"] == team_id:
                try:
                    hs = int(m["home_score"])
                    as_ = int(m["away_score"])
                except:
                    continue
                if m["home_id"] == team_id:
                    if hs > as_:  result = "G"
                    elif hs == as_: result = "B"
                    else: result = "M"
                    gf, ga = hs, as_
                else:
                    if as_ > hs:  result = "G"
                    elif as_ == hs: result = "B"
                    else: result = "M"
                    gf, ga = as_, hs
                form.append({"result": result, "gf": gf, "ga": ga, "opponent": m["away_team"] if m["home_id"] == team_id else m["home_team"]})
                if len(form) >= 5:
                    return form
    return form

async def get_today_matches():
    ds = datetime.now(timezone.utc).strftime("%Y%m%d")
    return await get_all_matches_for_date(ds)

async def get_tomorrow_matches():
    dt = datetime.now(timezone.utc) + timedelta(days=1)
    ds = dt.strftime("%Y%m%d")
    return await get_all_matches_for_date(ds)

async def get_live_matches():
    all_live = []
    for lig in LEAGUES:
        data = await get_scoreboard(lig)
        if data:
            for m in get_matches(data, lig):
                if m["state"] == "in":
                    all_live.append(m)
    return all_live

def format_match(m, show_odds=False):
    e = {"pre": "🕐", "in": "🔴", "post": "✅"}.get(m["state"], "⚪")
    sc = f"{m['home_score']}-{m['away_score']}" if m["state"] != "pre" else "vs"
    t = m["time"] if m["time"] else ""
    league = m.get("league", "")
    line = f"{e} {m['home_team']} {sc} {m['away_team']} {t}"
    if show_odds and m["home_odds"]:
        line += f" [{m['home_odds']}-{m['draw_odds']}-{m['away_odds']}]"
    return line

def categorize_match(m):
    odds = []
    if m["home_odds"]: odds.append(m["home_odds"])
    if m["draw_odds"]: odds.append(m["draw_odds"])
    if m["away_odds"]: odds.append(m["away_odds"])
    if not odds:
        return "orta"
    min_odds = min(odds)
    if min_odds <= 1.60:
        return "guvenli"
    elif min_odds <= 2.50:
        return "orta"
    else:
        return "riskli"

CAT_LABELS = {"guvenli": "🟢 Güvenli", "orta": "🟡 Orta Risk", "riskli": "🔴 Yüksek Risk"}
