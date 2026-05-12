from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    kb = [
        [InlineKeyboardButton("📅 Bugünün Maçları", callback_data="today")],
        [InlineKeyboardButton("📅 Yarının Maçları", callback_data="tomorrow")],
        [InlineKeyboardButton("🔴 Canlı Maçlar", callback_data="live")],
        [InlineKeyboardButton("📊 Tahmin Kategorileri", callback_data="tahminler")],
        [InlineKeyboardButton("ℹ️ Yardım", callback_data="help")],
    ]
    return InlineKeyboardMarkup(kb)


def match_list_kb(matches, source):
    kb = []
    for i, m in enumerate(matches[:20]):
        e = {"pre": "🕐", "in": "🔴", "post": "✅"}.get(m["state"], "⚪")
        sc = f"{m['home_score']}-{m['away_score']}" if m["state"] != "pre" else "vs"
        label = f"{e} {m['home_team'][:14]} {sc} {m['away_team'][:14]}"
        kb.append([InlineKeyboardButton(label, callback_data=f"m_{source}_{i}")])
    kb.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="main")])
    return InlineKeyboardMarkup(kb)


def match_detail_kb(idx, source):
    kb = [
        [
            InlineKeyboardButton("📊 MS 1X2", callback_data=f"d_{idx}_ms_{source}"),
            InlineKeyboardButton("🔄 Çifte Şans", callback_data=f"d_{idx}_dc_{source}"),
        ],
        [
            InlineKeyboardButton("🎯 İY/MS", callback_data=f"d_{idx}_htft_{source}"),
            InlineKeyboardButton("⚽ KG Var/Yok", callback_data=f"d_{idx}_gg_{source}"),
        ],
        [
            InlineKeyboardButton("📈 Alt/Üst (Maç)", callback_data=f"d_{idx}_ou_{source}"),
            InlineKeyboardButton("🥇 Alt/Üst (İY)", callback_data=f"d_{idx}_hou_{source}"),
        ],
        [
            InlineKeyboardButton("🥈 Alt/Üst (2Y)", callback_data=f"d_{idx}_sou_{source}"),
            InlineKeyboardButton("🎯 Skor Tahmini", callback_data=f"d_{idx}_skor_{source}"),
        ],
        [
            InlineKeyboardButton("📊 Form Analizi", callback_data=f"d_{idx}_form_{source}"),
            InlineKeyboardButton("📋 Tüm Tahminler", callback_data=f"d_{idx}_all_{source}"),
        ],
        [
            InlineKeyboardButton("🔙 Geri", callback_data=f"b_{source}"),
            InlineKeyboardButton("🏠 Ana Menü", callback_data="main"),
        ],
    ]
    return InlineKeyboardMarkup(kb)


def tahmin_kategorileri_kb(matches):
    guvenli = [m for m in matches if m.get("_risk") == "guvenli"]
    orta = [m for m in matches if m.get("_risk") == "orta"]
    riskli = [m for m in matches if m.get("_risk") == "riskli"]

    kb = []
    if guvenli:
        kb.append([InlineKeyboardButton(f"🟢 Güvenli ({len(guvenli)})", callback_data="kat_guvenli")])
    if orta:
        kb.append([InlineKeyboardButton(f"🟡 Orta Risk ({len(orta)})", callback_data="kat_orta")])
    if riskli:
        kb.append([InlineKeyboardButton(f"🔴 Yüksek Risk ({len(riskli)})", callback_data="kat_riskli")])

    # En iyi 4 tahmin
    en_iyi = sorted(
        [(m, m.get("_home_p", 0)) for m in matches if m.get("_home_p")],
        key=lambda x: -x[1]
    )[:4]
    kb.append([InlineKeyboardButton("🏆 En İyi 4 Tahmin", callback_data="kat_top4")])

    kb.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="main")])
    return InlineKeyboardMarkup(kb)


def category_match_kb(matches, cat, source):
    kb = []
    for i, m in enumerate(matches[:15]):
        e = {"pre": "🕐", "in": "🔴"}.get(m["state"], "⚪")
        sc = f"{m['home_score']}-{m['away_score']}" if m["state"] != "pre" else "vs"
        odds = ""
        if m["home_odds"]:
            odds = f" [{m['home_odds']}]"
        label = f"{e} {m['home_team'][:12]} {sc} {m['away_team'][:12]}{odds}"
        kb.append([InlineKeyboardButton(label, callback_data=f"mk_{cat}_{i}_{source}")])
    kb.append([InlineKeyboardButton("🔙 Kategoriler", callback_data="tahminler")])
    return InlineKeyboardMarkup(kb)


def top4_kb(matches, source):
    sorted_m = sorted(
        [(m, m.get("_home_p", 0)) for m in matches if m.get("_home_p")],
        key=lambda x: -x[1]
    )[:4]
    kb = []
    for i, (m, _) in enumerate(sorted_m):
        odds = f" [{m['home_odds']}-{m['draw_odds']}-{m['away_odds']}]" if m["home_odds"] else ""
        label = f"{i+1}. {m['home_team'][:12]} vs {m['away_team'][:12]}{odds}"
        kb.append([InlineKeyboardButton(label, callback_data=f"m_{source}_{matches.index(m)}")])
    kb.append([InlineKeyboardButton("🔙 Kategoriler", callback_data="tahminler")])
    return InlineKeyboardMarkup(kb)


def back_kb(target="main"):
    kb = [[InlineKeyboardButton("🔙 Geri", callback_data=f"b_{target}")]]
    return InlineKeyboardMarkup(kb)
