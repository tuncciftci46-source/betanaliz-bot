import math


def poisson(k, lam):
    if lam <= 0:
        return 0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def estimate_goals(h_odds, d_odds, a_odds):
    if all([h_odds, d_odds, a_odds]):
        total_implied = (1 / h_odds) + (1 / d_odds) + (1 / a_odds)
        if total_implied > 0:
            hp = (1 / h_odds) / total_implied
            ap = (1 / a_odds) / total_implied
            hg = hp * 2.5
            ag = ap * 2.5
            return round(hg, 2), round(ag, 2)
    return 1.3, 1.1


def adjust_with_form(hg, ag, home_form, away_form):
    if home_form:
        avg_gf = sum(f["gf"] for f in home_form) / len(home_form)
        avg_ga = sum(f["ga"] for f in home_form) / len(home_form)
        hg = (hg + avg_gf) / 2
        ag = (ag + avg_ga) / 2
    if away_form:
        avg_gf = sum(f["gf"] for f in away_form) / len(away_form)
        avg_ga = sum(f["ga"] for f in away_form) / len(away_form)
        ag = (ag + avg_gf) / 2
        hg = (hg + avg_ga) / 2
    return max(0.2, round(hg, 2)), max(0.2, round(ag, 2))


def form_points(form):
    if not form:
        return 0, 0, 0
    w = sum(1 for f in form if f["result"] == "G")
    d = sum(1 for f in form if f["result"] == "B")
    l = sum(1 for f in form if f["result"] == "M")
    return w, d, l


def form_score(form):
    w, d, l = form_points(form)
    return w * 3 + d


def predict_1x2(hg, ag, home_form=None, away_form=None):
    hg, ag = adjust_with_form(hg, ag, home_form or [], away_form or [])
    ph = sum(poisson(h, hg) * sum(poisson(a, ag) for a in range(0, h)) for h in range(1, 12))
    pa = sum(poisson(a, ag) * sum(poisson(h, hg) for h in range(0, a)) for a in range(1, 12))
    pd = sum(poisson(k, hg) * poisson(k, ag) for k in range(0, 12))
    t = ph + pa + pd or 1
    return ph / t, pd / t, pa / t, hg, ag


def predict_ht_ft(hg, ag):
    half_hg = hg * 0.42
    half_ag = ag * 0.42
    full_hg = hg * 0.58
    full_ag = ag * 0.58

    ht_outs = {}
    for hh, ha in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2), (2, 2)]:
        p_ht = poisson(hh, half_hg) * poisson(ha, half_ag)
        if hh > ha:
            ht_r = "1"
        elif hh < ha:
            ht_r = "2"
        else:
            ht_r = "X"
        for fh, fa in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2), (2, 2)]:
            p_ft = poisson(fh, full_hg) * poisson(fa, full_ag)
            if fh > fa:
                ft_r = "1"
            elif fh < fa:
                ft_r = "2"
            else:
                ft_r = "X"
            key = f"{ht_r}/{ft_r}"
            ht_outs[key] = ht_outs.get(key, 0) + p_ht * p_ft

    total = sum(ht_outs.values()) or 1
    return sorted([(k, f"{v/total*100:.1f}%") for k, v in ht_outs.items()], key=lambda x: -float(x[1].replace("%","")))[:6]


def predict_gg_ng(hg, ag):
    home_s = 1 - poisson(0, hg)
    away_s = 1 - poisson(0, ag)
    gg = home_s * away_s
    ng = 1 - gg
    gg = max(0.01, min(0.99, gg))
    return gg, ng


def predict_ou(hg, ag):
    tl = hg + ag
    res = []
    for t in [0.5, 1.5, 2.5, 3.5, 4.5]:
        un = sum(poisson(k, tl) for k in range(0, int(t) + 1))
        ov = 1 - un
        un = max(0.01, min(0.99, un))
        ov = max(0.01, min(0.99, ov))
        res.append({"t": f"{t}", "o": f"Üst {ov*100:.1f}%", "u": f"Alt {un*100:.1f}%"})
    return res


def predict_half_ou(hg, ag):
    hl = (hg + ag) * 0.4
    res = []
    for t in [0.5, 1.0, 1.5]:
        un = sum(poisson(k, hl) for k in range(0, int(t) + 1))
        ov = 1 - un
        un = max(0.01, min(0.99, un))
        ov = max(0.01, min(0.99, ov))
        res.append({"t": f"İY {t}", "o": f"Üst {ov*100:.1f}%", "u": f"Alt {un*100:.1f}%"})
    return res


def predict_second_half_ou(hg, ag):
    hl = (hg + ag) * 0.6
    res = []
    for t in [0.5, 1.0, 1.5]:
        un = sum(poisson(k, hl) for k in range(0, int(t) + 1))
        ov = 1 - un
        un = max(0.01, min(0.99, un))
        ov = max(0.01, min(0.99, ov))
        res.append({"t": f"2Y {t}", "o": f"Üst {ov*100:.1f}%", "u": f"Alt {un*100:.1f}%"})
    return res


def predict_score(hg, ag):
    scores = []
    for h in range(0, 7):
        for a in range(0, 7):
            p = poisson(h, hg) * poisson(a, ag)
            if p > 0.005:
                scores.append({"s": f"{h}-{a}", "p": f"{p*100:.1f}%"})
    scores.sort(key=lambda x: -float(x["p"].replace("%", "")))
    return scores[:6]


def risk_category(hg, ag, ph, pd, pa):
    if ph > 0.55 or pa > 0.55:
        return "guvenli"
    elif ph > 0.40 or pa > 0.40:
        return "orta"
    return "riskli"


def full_analysis(match, home_form=None, away_form=None):
    h_odds = match.get("home_odds")
    d_odds = match.get("draw_odds")
    a_odds = match.get("away_odds")

    hg, ag = estimate_goals(h_odds, d_odds, a_odds)
    ph, pd, pa, hg_a, ag_a = predict_1x2(hg, ag, home_form, away_form)

    gg, ng = predict_gg_ng(hg_a, ag_a)

    return {
        "home_goals": hg_a,
        "away_goals": ag_a,
        "match_odds": [
            {"p": f"1 (Ev)", "v": f"{ph*100:.1f}%"},
            {"p": f"0 (Beraberlik)", "v": f"{pd*100:.1f}%"},
            {"p": f"2 (Deplasman)", "v": f"{pa*100:.1f}%"},
        ],
        "double_chance": [
            {"p": "1X (Ev/Ber)", "v": f"{(ph+pd)*100:.1f}%"},
            {"p": "12 (Ev/Dep)", "v": f"{(ph+pa)*100:.1f}%"},
            {"p": "X2 (Ber/Dep)", "v": f"{(pd+pa)*100:.1f}%"},
        ],
        "ht_ft": predict_ht_ft(hg_a, ag_a),
        "gg_ng": [
            {"p": "GG (Var)", "v": f"{gg*100:.1f}%"},
            {"p": "NG (Yok)", "v": f"{ng*100:.1f}%"},
        ],
        "over_under": predict_ou(hg_a, ag_a),
        "half_ou": predict_half_ou(hg_a, ag_a),
        "second_ou": predict_second_half_ou(hg_a, ag_a),
        "scores": predict_score(hg_a, ag_a),
        "risk": risk_category(hg_a, ag_a, ph, pd, pa),
    }
