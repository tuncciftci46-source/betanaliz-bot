import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

LEAGUES = [
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
    "ned.1", "por.1", "tur.1", "bra.1", "arg.1",
    "sco.1", "bel.1", "aut.1", "gre.1",
    "den.1", "nor.1", "swe.1", "rus.1",
    "cyp.1", "irl.1",
    "uefa.champions", "uefa.europa", "uefa.europa.conf",
    "uefa.nations",
    "usa.1", "usa.nwsl",
    "bra.2",
    "conmebol.libertadores", "conmebol.sudamericana",
]
