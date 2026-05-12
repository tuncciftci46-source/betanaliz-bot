import logging
from telegram import Update
from telegram.ext import ContextTypes

from espn_scraper import (
    get_today_matches, get_tomorrow_matches, get_live_matches,
    get_team_form, CAT_LABELS,
)
from analyzer import full_analysis
from keyboards import (
    main_menu, match_list_kb, match_detail_kb,
    tahmin_kategorileri_kb, category_match_kb, back_kb,
)

logger = logging.getLogger(__name__)

CACHE = {}
FORM_CACHE = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *BetAnaliz Bot*\n\n"
        "ESPN verileriyle maç analizi ve tahminler.\n\n"
        "📌 *Özellikler:*\n"
        "• MS 1X2 • Çifte Şans • İY/MS\n"
        "• KG Var/Yok • Alt/Üst (Maç/İY/2Y)\n"
        "• Skor Tahmini • Form Analizi\n"
        "• Risk Kategorileri (Güvenli/Orta/Riskli)\n\n"
        "_Menüden seçim yapınız:_",
        reply_markup=main_menu(), parse_mode="Markdown"
    )


def risk_emoji(r):
    return {"guvenli": "🟢", "orta": "🟡", "riskli": "🔴"}.get(r, "⚪")


async def get_form_cached(league, team_id):
    key = f"{league}_{team_id}"
    if key not in FORM_CACHE:
        FORM_CACHE[key] = await get_team_form(league, team_id, 21)
    return FORM_CACHE[key]


async def anlas(match):
    if "_analysis" in match:
        return match["_analysis"]
    hf = await get_form_cached(match["league_code"], match["home_id"])
    af = await get_form_cached(match["league_code"], match["away_id"])
    try:
        an = full_analysis(match, hf, af)
    except:
        an = full_analysis(match)
    match["_analysis"] = an
    match["_risk"] = an.get("risk", "orta")
    match["_home_p"] = float(an["match_odds"][0]["v"].replace("%", "")) if an["match_odds"] else 0
    return an


def get_cached_matches(src):
    return CACHE.get(src, [])


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "main":
        await q.edit_message_text("📌 *Ana Menü*", reply_markup=main_menu(), parse_mode="Markdown")
        return

    if data == "help":
        await q.edit_message_text(
            "ℹ️ *Yardım*\n\n"
            "• 📅 *Bugünün Maçları* - Bugün oynanacak maçlar\n"
            "• 📅 *Yarının Maçları* - Yarınki maçlar\n"
            "• 🔴 *Canlı Maçlar* - Şu an oynanan maçlar\n"
            "• 📊 *Tahmin Kategorileri* - Güvenli/Orta/Riskli\n\n"
            "_Her maç detayında butonlarla analizler._",
            reply_markup=back_kb(), parse_mode="Markdown"
        )
        return

    if data in ("today", "tomorrow"):
        label = {"today": "Bugünün", "tomorrow": "Yarının"}[data]
        await q.edit_message_text(f"📅 {label} maçları yükleniyor...")
        try:
            if data == "today":
                m = await get_today_matches()
            else:
                m = await get_tomorrow_matches()
            if not m:
                await q.edit_message_text(f"{label} maç yok.", reply_markup=back_kb())
                return
            for match in m:
                await anlas(match)
            CACHE[data] = m
            await q.edit_message_text(
                f"📅 {label} {len(m)} maç:",
                reply_markup=match_list_kb(m, data)
            )
        except Exception as e:
            logger.error(f"{data}: {e}")
            await q.edit_message_text("Hata oluştu.", reply_markup=back_kb())
        return

    if data == "live":
        await q.edit_message_text("🔴 Canlı maçlar yükleniyor...")
        try:
            m = await get_live_matches()
            if not m:
                await q.edit_message_text("Canlı maç yok.", reply_markup=back_kb())
                return
            for match in m:
                await anlas(match)
            CACHE["live"] = m
            await q.edit_message_text(
                f"🔴 {len(m)} canlı maç:",
                reply_markup=match_list_kb(m, "live")
            )
        except Exception as e:
            logger.error(f"live: {e}")
            await q.edit_message_text("Hata oluştu.", reply_markup=back_kb())
        return

    if data == "tahminler":
        all_m = get_cached_matches("today") + get_cached_matches("tomorrow")
        guvenli = [m for m in all_m if m.get("_risk") == "guvenli"]
        orta = [m for m in all_m if m.get("_risk") == "orta"]
        riskli = [m for m in all_m if m.get("_risk") == "riskli"]

        txt = "📊 *Tahmin Kategorileri*\n\n"
        txt += f"🟢 Güvenli: {len(guvenli)} maç\n"
        txt += f"🟡 Orta Risk: {len(orta)} maç\n"
        txt += f"🔴 Yüksek Risk: {len(riskli)} maç\n"

        await q.edit_message_text(txt, reply_markup=tahmin_kategorileri_kb(all_m), parse_mode="Markdown")
        return

    if data.startswith("kat_"):
        cat = data.replace("kat_", "")
        all_m = get_cached_matches("today") + get_cached_matches("tomorrow")

        if cat == "top4":
            sorted_m = sorted(
                [m for m in all_m if m.get("_home_p")],
                key=lambda x: -x["_home_p"]
            )[:4]
            txt = "🏆 *En İyi 4 Tahmin*\n\n"
            for i, m in enumerate(sorted_m, 1):
                r = risk_emoji(m.get("_risk", ""))
                odds = f"{m['home_odds']}-{m['draw_odds']}-{m['away_odds']}" if m["home_odds"] else "Yok"
                an = m.get("_analysis", {})
                gg_txt = an["gg_ng"][0]["v"] if an.get("gg_ng") else "?"
                ou_items = [x for x in an.get("over_under", []) if "2.5" in x["t"]]
                ou_txt = f"{ou_items[0]['o']}/{ou_items[0]['u']}" if ou_items else "?"
                txt += f"{i}. {r} *{m['home_team']}* vs *{m['away_team']}*\n"
                txt += f"   Ev: %{m['_home_p']:.1f} | Oran: {odds}\n"
                txt += f"   KG: {gg_txt} | 2.5: {ou_txt}\n\n"
            await q.edit_message_text(txt, reply_markup=back_kb("tahminler"), parse_mode="Markdown")
        else:
            cat_m = [m for m in all_m if m.get("_risk") == cat]
            label = CAT_LABELS.get(cat, cat)
            if not cat_m:
                await q.edit_message_text(f"{label} kategorisinde maç yok.", reply_markup=back_kb("tahminler"))
                return
            await q.edit_message_text(
                f"{label} - {len(cat_m)} maç:",
                reply_markup=category_match_kb(cat_m, cat, "tahminler")
            )
        return

    if data.startswith("m_"):
        parts = data.split("_")
        src = parts[1]
        idx = int(parts[2])
        matches = get_cached_matches(src)
        if not matches or idx >= len(matches):
            await q.edit_message_text("Maç bulunamadı.", reply_markup=back_kb())
            return
        m = matches[idx]
        CACHE["last_match"] = m
        CACHE["last_idx"] = idx
        CACHE["last_source"] = src

        await anlas(m)
        e = {"pre": "🕐", "in": "🔴"}.get(m["state"], "⚪")
        r = risk_emoji(m.get("_risk", ""))
        txt = (
            f"{e} *{m['home_team']}* vs *{m['away_team']}*\n"
            f"🏆 {m.get('league', '')} | 🕐 {m['date']} {m['time']}\n"
        )
        if m.get("_risk"):
            txt += f"📊 {r} {CAT_LABELS.get(m['_risk'], m['_risk'])}\n"
        if m["state"] == "in":
            try:
                txt += f"🔴 *Skor:* {m['home_score']}-{m['away_score']}\n"
            except:
                pass
        if m["home_odds"]:
            txt += f"\n💰 1️⃣ {m['home_odds']} | 0️⃣ {m['draw_odds']} | 2️⃣ {m['away_odds']}\n"

        await q.edit_message_text(txt, reply_markup=match_detail_kb(idx, src), parse_mode="Markdown")
        return

    if data.startswith("mk_"):
        parts = data.split("_")
        cat = parts[1]
        idx = int(parts[2])
        src = parts[3]
        all_m = get_cached_matches("today") + get_cached_matches("tomorrow")
        cat_m = [m for m in all_m if m.get("_risk") == cat]
        if not cat_m or idx >= len(cat_m):
            await q.edit_message_text("Maç bulunamadı.", reply_markup=back_kb())
            return
        m = cat_m[idx]
        orig_src = "today" if m in get_cached_matches("today") else "tomorrow"
        orig_idx = CACHE[orig_src].index(m)
        CACHE["last_match"] = m
        CACHE["last_idx"] = orig_idx
        CACHE["last_source"] = orig_src

        await anlas(m)
        r = risk_emoji(m.get("_risk", ""))
        txt = (
            f"*{m['home_team']}* vs *{m['away_team']}*\n"
            f"🏆 {m.get('league', '')} | 🕐 {m['date']} {m['time']}\n"
        )
        if m.get("_risk"):
            txt += f"📊 {r} {CAT_LABELS.get(m['_risk'], m['_risk'])}\n"
        if m["home_odds"]:
            txt += f"\n💰 1️⃣ {m['home_odds']} | 0️⃣ {m['draw_odds']} | 2️⃣ {m['away_odds']}\n"

        await q.edit_message_text(txt, reply_markup=match_detail_kb(orig_idx, orig_src), parse_mode="Markdown")
        return

    if data.startswith("d_"):
        parts = data.split("_")
        idx = int(parts[1])
        dtype = parts[2]
        src = "_".join(parts[3:])
        matches = get_cached_matches(src)
        if not matches or idx >= len(matches):
            await q.edit_message_text("Maç bulunamadı.", reply_markup=back_kb())
            return
        m = matches[idx]
        an = await anlas(m)

        header = f"📊 *{m['home_team']} vs {m['away_team']}*\n\n"

        if dtype == "ms":
            txt = header + "🏁 *MS 1X2*\n"
            for p in an["match_odds"]:
                txt += f"• {p['p']}: `{p['v']}`\n"
            txt += f"\n⚽ Beklenen: Ev {an['home_goals']:.2f} - Dep {an['away_goals']:.2f}"

        elif dtype == "dc":
            txt = header + "🔄 *Çifte Şans*\n"
            for p in an["double_chance"]:
                txt += f"• {p['p']}: `{p['v']}`\n"

        elif dtype == "htft":
            txt = header + "🎯 *İY / MS*\n"
            for p in an["ht_ft"]:
                txt += f"• {p[0]}: `{p[1]}`\n"

        elif dtype == "gg":
            txt = header + "⚽ *KG Var / Yok*\n"
            for p in an["gg_ng"]:
                txt += f"• {p['p']}: `{p['v']}`\n"

        elif dtype == "ou":
            txt = header + "📈 *Alt / Üst (Maç)*\n"
            for p in an["over_under"]:
                txt += f"• {p['t']} Gol: ⬆{p['o']} / ⬇{p['u']}\n"

        elif dtype == "hou":
            txt = header + "🥇 *Alt / Üst (İlk Yarı)*\n"
            for p in an["half_ou"]:
                txt += f"• {p['t']} Gol: ⬆{p['o']} / ⬇{p['u']}\n"

        elif dtype == "sou":
            txt = header + "🥈 *Alt / Üst (2. Yarı)*\n"
            for p in an["second_ou"]:
                txt += f"• {p['t']} Gol: ⬆{p['o']} / ⬇{p['u']}\n"

        elif dtype == "skor":
            txt = header + "🎯 *Skor Tahminleri*\n"
            for p in an["scores"]:
                txt += f"• {p['s']}: `{p['p']}`\n"

        elif dtype == "form":
            txt = header + "📊 *Form Analizi*\n"
            for team_id, team_name, side in [(m["home_id"], m["home_team"], "🏠 Ev"), (m["away_id"], m["away_team"], "✈️ Dep")]:
                form = await get_form_cached(m["league_code"], team_id)
                txt += f"\n*{side} - {team_name}:* "
                if form:
                    txt += " ".join([{"G": "✅", "B": "➖", "M": "❌"}.get(f["result"], "?") for f in form])
                    g = sum(f["gf"] for f in form)
                    y = sum(f["ga"] for f in form)
                    w = sum(1 for f in form if f["result"] == "G")
                    d = sum(1 for f in form if f["result"] == "B")
                    l = 5 - w - d
                    txt += f"\n  AG: {g} | YG: {y} | {w}G/{d}B/{l}M"
                else:
                    txt += "Veri yok"

        elif dtype == "all":
            txt = header
            txt += "🏁 *MS 1X2*\n"
            for p in an["match_odds"]:
                txt += f"• {p['p']}: `{p['v']}`  "
            txt += "\n\n🔄 *Çifte Şans*\n"
            for p in an["double_chance"]:
                txt += f"• {p['p']}: `{p['v']}`  "
            txt += "\n\n🎯 *İY/MS (ilk 3)*\n"
            for p in an["ht_ft"][:3]:
                txt += f"• {p[0]}: `{p[1]}`  "
            txt += f"\n\n⚽ *KG:* {an['gg_ng'][0]['v']} / {an['gg_ng'][1]['v']}"
            txt += f"\n📈 *Alt/Üst 2.5:* {an['over_under'][2]['o']} / {an['over_under'][2]['u']}"
            txt += f"\n🎯 *Skor:* " + ", ".join([f"{s['s']} ({s['p']})" for s in an["scores"][:3]])

        else:
            txt = header + "Bilinmeyen analiz."

        await q.edit_message_text(txt, reply_markup=match_detail_kb(idx, src), parse_mode="Markdown")
        return

    if data.startswith("b_"):
        target = data.replace("b_", "")
        if not target or target == "main":
            await q.edit_message_text("📌 *Ana Menü*", reply_markup=main_menu(), parse_mode="Markdown")
        elif target == "tahminler":
            all_m = get_cached_matches("today") + get_cached_matches("tomorrow")
            guvenli = [m for m in all_m if m.get("_risk") == "guvenli"]
            orta = [m for m in all_m if m.get("_risk") == "orta"]
            riskli = [m for m in all_m if m.get("_risk") == "riskli"]
            txt = "📊 *Tahmin Kategorileri*\n\n"
            txt += f"🟢 Güvenli: {len(guvenli)} maç\n"
            txt += f"🟡 Orta Risk: {len(orta)} maç\n"
            txt += f"🔴 Yüksek Risk: {len(riskli)} maç\n"
            await q.edit_message_text(txt, reply_markup=tahmin_kategorileri_kb(all_m), parse_mode="Markdown")
        else:
            m = get_cached_matches(target)
            if m:
                await q.edit_message_text(f"{len(m)} maç:", reply_markup=match_list_kb(m, target))
            else:
                await q.edit_message_text("📌 *Ana Menü*", reply_markup=main_menu(), parse_mode="Markdown")
        return
