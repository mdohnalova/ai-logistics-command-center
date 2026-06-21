#!/usr/bin/env python3
"""
AI Logistics Command Center — Streamlit Dashboard v3.2
Portfolio Project #3 | Martina Dohnalová | AI Vibecoder

SaaS Dashboard Clean Look: custom HTML karty, konzistentní paleta, vzdušný layout.
Lineární flow: Záhlaví → KPI → Semafor → Mapa → ROI → Grafy
"""

import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 0: KONFIGURACE — sidebar prázdný, plná šířka, SaaS look ──
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Logistics Command Center",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OUTPUT_JSON = "logistics_output.json"

# Emoji pro standardizované stavy zásilek
STATUS_EMOJI: dict[str, str] = {
    "In Transit":          "🚚",
    "Damaged":             "💥",
    "Delivered":           "✅",
    "Warning - Unclaimed": "⏰",
}

# Barva tečky na mapě podle rizika (hex)
RISK_COLOR: dict[str, str] = {
    "low":    "#2ECC71",
    "medium": "#F39C12",
    "high":   "#E74C3C",
}

# Emoji badge pro tabulkové přehledy
RISK_BADGE: dict[str, str] = {
    "low":    "🟢 low",
    "medium": "🟡 medium",
    "high":   "🔴 high",
}

# Typ Streamlit alertu pro marketing triggery
TRIGGER_ALERT: dict[str, str] = {
    "Apology Voucher":                     "error",
    "Urgent SMS with gift coupon":         "warning",
    "Review & Cross-sell request":         "success",
    "Pre-delivery product recommendation": "info",
}

TRIGGER_ICON: dict[str, str] = {
    "Apology Voucher":                     "🙏",
    "Urgent SMS with gift coupon":         "📱",
    "Review & Cross-sell request":         "⭐",
    "Pre-delivery product recommendation": "🛍️",
}

# Fixní časy svozů dopravců
CARRIER_PICKUP_TIMES: dict[str, str] = {
    "PPL":        "14:00",
    "Zásilkovna": "15:30",
}

# 8 ukázkových Shoptet objednávek pro enterprise demo
SHOPTET_ORDERS: list[dict] = [
    {"order_id": "SHP-1001", "customer": "Jana Nováková",     "carrier": "Zásilkovna",  "value": 1_250, "priority": "normal"},
    {"order_id": "SHP-1002", "customer": "Petr Svoboda",       "carrier": "PPL",          "value": 3_890, "priority": "express"},
    {"order_id": "SHP-1003", "customer": "Marie Horáková",     "carrier": "DHL",          "value":   670, "priority": "normal"},
    {"order_id": "SHP-1004", "customer": "Tomáš Procházka",    "carrier": "Zásilkovna",  "value": 2_100, "priority": "normal"},
    {"order_id": "SHP-1005", "customer": "Kateřina Dvořáková", "carrier": "PPL",          "value": 5_499, "priority": "express"},
    {"order_id": "SHP-1006", "customer": "Ondřej Krejčí",      "carrier": "Česká Pošta", "value":   890, "priority": "normal"},
    {"order_id": "SHP-1007", "customer": "Lucie Marková",      "carrier": "DHL",          "value": 1_780, "priority": "normal"},
    {"order_id": "SHP-1008", "customer": "Martin Novák",       "carrier": "Zásilkovna",  "value":   450, "priority": "normal"},
]

# Portály dopravců
CARRIER_PORTAL_INFO: dict[str, str] = {
    "Zásilkovna":  "client.packeta.com",
    "PPL":         "myapi.ppl.cz / elogist",
    "DHL":         "developer.dhl.com",
    "Česká Pošta": "b2b.postaonline.cz",
}

# ROI parametry
ROI_RATE_CZK_PER_HOUR:    int = 300
ROI_MINUTES_PER_ANOMALY:  int = 15
ROI_RETURN_SHIPPING_CZK:  int = 150
ROI_MONTHLY_BATCH_FACTOR: int = 30


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 1: SESSION STATE ──
# ══════════════════════════════════════════════════════════════════════════════

def init_session_state() -> None:
    """Nastaví výchozí hodnoty session_state při prvním načtení stránky."""
    defaults: dict = {
        "ppl_handed_off":          False,
        "zasilkovna_handed_off":   False,
        "ppl_handoff_time":        None,
        "zasilkovna_handoff_time": None,
        "dispatched_orders":       set(),
        "printed_labels":          set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 2: DATOVÁ VRSTVA ──
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_output_data(filepath: str) -> dict | None:
    """Načte a cachuje výstupní JSON logistického pipeline."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_shipments_df(data: dict) -> pd.DataFrame:
    """Sestaví pandas DataFrame ze zásilek — základ celé aplikace."""
    rows = []
    for item in data["shipments"]:
        s = item["shipment"]
        a = item["analysis"]
        rows.append({
            "Tracking":          s["tracking_number"],
            "Carrier":           s["carrier"],
            "Status":            f"{STATUS_EMOJI.get(a['standardized_status'], '')} {a['standardized_status']}",
            "Risk":              RISK_BADGE.get(a["delivery_risk"], a["delivery_risk"]),
            "Region":            a["region"],
            "Marketing Trigger": a["marketing_trigger"],
            "Support Action":    a["proactive_support_action"],
            "lat":               a["gps_coordinates"]["lat"],
            "lon":               a["gps_coordinates"]["lon"],
            "_status":           a["standardized_status"],
            "_risk":             a["delivery_risk"],
            "_trigger":          a["marketing_trigger"],
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 3: HTML KOMPONENTY — konzistentní SaaS design ──
# ══════════════════════════════════════════════════════════════════════════════

# Striktní paleta — používá se výhradně zde, žádná odchylka
_C_BG      = "#F8F9FA"   # pozadí karet
_C_BORDER  = "#E9ECEF"   # ohraničení karet
_C_TEXT    = "#212529"   # primární text
_C_MUTED   = "#6C757D"   # sekundární text
_C_LIGHT   = "#ADB5BD"   # terciární text (sublabely)
_C_GREEN   = "#155724"   # text success
_C_GREEN_B = "#C3E6CB"   # border success
_C_GREEN_L = "#D4EDDA"   # background success
_C_AMBER   = "#856404"   # text warning
_C_AMBER_B = "#FFEEBA"   # border warning
_C_AMBER_L = "#FFF3CD"   # background warning
_C_RED     = "#721C24"   # text danger
_C_RED_B   = "#F5C6CB"   # border danger
_C_RED_L   = "#F8D7DA"   # background danger


def kpi_card(icon: str, value: str, label: str) -> str:
    """HTML kartička pro horní KPI lištu — decentní 28px číslo, popisek níže."""
    return f"""<div style="
        background:{_C_BG};border:1px solid {_C_BORDER};border-radius:8px;
        padding:18px 12px;text-align:center;box-sizing:border-box;height:84px;
        display:flex;flex-direction:column;justify-content:center">
        <div style="font-size:28px;font-weight:700;color:{_C_TEXT};line-height:1.1">{value}</div>
        <div style="font-size:12px;color:{_C_MUTED};margin-top:5px;white-space:nowrap">{icon}&nbsp;{label}</div>
    </div>"""


def stat_card(icon: str, label: str, value: str, sublabel: str = "") -> str:
    """HTML kartička pro ROI a Carrier metriky — ikona + label nahoře, hodnota prominentní."""
    sub = (f'<div style="font-size:11px;color:{_C_LIGHT};margin-top:3px">{sublabel}</div>'
           if sublabel else "")
    return f"""<div style="
        background:{_C_BG};border:1px solid {_C_BORDER};border-radius:8px;
        padding:16px 12px;text-align:center;box-sizing:border-box">
        <div style="font-size:12px;color:{_C_MUTED};margin-bottom:7px;white-space:nowrap">{icon}&nbsp;{label}</div>
        <div style="font-size:22px;font-weight:700;color:{_C_TEXT};line-height:1.2">{value}</div>
        {sub}
    </div>"""


def annual_banner(czk: int, hours: float) -> str:
    """Zelený prominentní banner pro roční ROI výsledek — headline pro manažery."""
    days = hours / 8
    return f"""<div style="
        background:linear-gradient(135deg,{_C_GREEN_L},{_C_GREEN_B});
        border:1px solid {_C_GREEN_B};border-radius:10px;
        padding:22px 24px;margin-top:12px;text-align:center">
        <div style="font-size:14px;font-weight:600;color:{_C_GREEN};margin-bottom:8px">
            🏆 Roční potenciál systému při konstantním provozu
        </div>
        <div style="font-size:38px;font-weight:800;color:{_C_GREEN};line-height:1.2">
            {czk:,} Kč
        </div>
        <div style="font-size:13px;color:{_C_GREEN};margin-top:7px;opacity:0.85">
            {hours:.0f} hodin práce ušetřeno &nbsp;·&nbsp; {days:.0f} pracovních dní ročně
        </div>
    </div>"""


def api_badge(is_prod: bool) -> str:
    """HTML badge pro stav API klíče — stylově jednotný s kartičkami."""
    bg, border, color, text = (
        (_C_GREEN_L, _C_GREEN_B, _C_GREEN, "🔑 Produkční AI")
        if is_prod
        else (_C_AMBER_L, _C_AMBER_B, _C_AMBER, "🎭 Demo režim")
    )
    return f"""<div style="
        background:{bg};border:1px solid {border};color:{color};
        padding:8px 14px;border-radius:6px;font-size:13px;font-weight:500;
        text-align:center;white-space:nowrap">{text}</div>"""


def map_legend() -> str:
    """HTML inline legenda barev mapy — barevné kolečko + černý text."""
    items = [("#E74C3C", "Vysoké riziko"), ("#F39C12", "Střední riziko"), ("#2ECC71", "Nízké riziko")]
    dots  = " &nbsp;&nbsp;&nbsp; ".join(
        f'<span style="color:{c};font-size:15px">●</span>'
        f'<span style="font-size:13px;color:{_C_TEXT};margin-left:4px">{l}</span>'
        for c, l in items
    )
    return f'<div style="margin-bottom:8px;padding-left:2px">{dots}</div>'


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 4: VÝPOČETNÍ FUNKCE ──
# ══════════════════════════════════════════════════════════════════════════════

def compute_pickup_countdown(pickup_time_str: str) -> tuple[int, int, bool]:
    """Živý odpočet do svozu. Vrací (hodiny, minuty, je_po_svozu)."""
    now = datetime.now()
    hour, minute = map(int, pickup_time_str.split(":"))
    pickup_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    delta = pickup_dt - now
    if delta.total_seconds() <= 0:
        return 0, 0, True
    total_min = int(delta.total_seconds() / 60)
    return total_min // 60, total_min % 60, False


def compute_roi(df: pd.DataFrame, bi: dict) -> dict:
    """Spočítá finanční přínos AI systému pro majitele e-shopu."""
    damaged  = bi["damaged_shipments"]
    warning  = len(df[df["_status"] == "Warning - Unclaimed"])
    total    = damaged + warning
    min_saved = total * ROI_MINUTES_PER_ANOMALY
    support   = round(min_saved / 60 * ROI_RATE_CZK_PER_HOUR)
    returns   = warning * ROI_RETURN_SHIPPING_CZK
    daily     = support + returns
    return {
        "total": total, "damaged": damaged, "warning": warning,
        "support_czk": support, "returns_czk": returns,
        "daily_czk":   daily,   "daily_h":     round(min_saved / 60, 2),
        "monthly_czk": daily * ROI_MONTHLY_BATCH_FACTOR,
        "monthly_h":   round(min_saved / 60 * ROI_MONTHLY_BATCH_FACTOR, 1),
    }


def render_semafor_card(
    name: str, icon: str, pickup_time: str,
    handed_off_key: str, handoff_time_key: str, btn_key: str,
) -> None:
    """
    Vykreslí svozovou kartu se semaforem a tlačítkem pro potvrzení.
    Díky plné šířce 2 sloupců se žádný text nikdy nerozdělí na řádky.
    """
    with st.container(border=True):
        st.markdown(f"#### {icon} {name}")
        h, m, is_past = compute_pickup_countdown(pickup_time)

        if st.session_state[handed_off_key]:
            # Zásilky předány — permanentní zelený stav s časovým razítkem
            st.success(
                f"## ✅ Odešlo\n"
                f"Řidič **{name}** odjel v **{st.session_state[handoff_time_key]}**"
            )
            return

        if is_past:
            # Svoz uplynul bez potvrzení
            st.error(
                f"⚠️ Svozové okno **{name}** ({pickup_time}) uplynulo!  \n"
                "Potvrďte předání nebo kontaktujte dispečink."
            )
            lbl, typ = "✋ Předáno (se zpožděním)", "secondary"
        else:
            total_min = h * 60 + m
            # Semafor: barva a urgence podle zbývajícího času
            sem, urg, urg_c = (
                ("🔴", "URGENT — expedovat okamžitě!",      "#DC3545") if total_min <= 30
                else ("🟡", "Připravit zásilky ke svozu",    "#FD7E14") if total_min <= 60
                else ("🟢", "Vše v pořádku, čas zbývá",     "#28A745")
            )
            # Odpočet jako čistý HTML — konzistentní velikost, žádné gigantické st.metric
            st.markdown(f"""<div style="text-align:center;padding:12px 0 8px">
                <div style="font-size:13px;color:{_C_MUTED};margin-bottom:6px">
                    {sem}&nbsp;&nbsp;Svoz v&nbsp;<strong>{pickup_time}</strong>
                </div>
                <div style="font-size:42px;font-weight:800;color:{_C_TEXT};line-height:1.1;
                            letter-spacing:-1px">
                    {h}h&nbsp;{m:02d}min
                </div>
                <div style="font-size:12px;color:{urg_c};margin-top:6px;font-weight:500">
                    {urg}
                </div>
            </div>""", unsafe_allow_html=True)
            lbl, typ = f"✋ Předáno řidiči {name}", "primary"

        if st.button(lbl, key=btn_key, use_container_width=True, type=typ):
            st.session_state[handed_off_key]   = True
            st.session_state[handoff_time_key] = datetime.now().strftime("%H:%M:%S")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 5: ZÁHLAVÍ — nadpis vlevo, API badge + Refresh vpravo ──
# ══════════════════════════════════════════════════════════════════════════════

# Sidebar je záměrně prázdný — vše je na hlavní ploše

hdr_l, hdr_r = st.columns([5, 1])

with hdr_l:
    st.title("📦 AI Logistics Command Center")
    st.markdown(
        f'<p style="color:{_C_MUTED};font-size:14px;margin-top:-8px">'
        "Enterprise BI &nbsp;·&nbsp; High-Volume Production Ready &nbsp;·&nbsp; "
        "Claude AI &nbsp;·&nbsp; Portfolio Project #3 &nbsp;·&nbsp; "
        "Martina Dohnalová | AI Vibecoder</p>",
        unsafe_allow_html=True,
    )

with hdr_r:
    # Vertikální zarovnání pod nadpis + konzistentní badge
    st.markdown('<div style="padding-top:18px"></div>', unsafe_allow_html=True)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    st.markdown(api_badge(bool(api_key)), unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    if st.button("🚀 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 6: NAČTENÍ DAT ──
# ══════════════════════════════════════════════════════════════════════════════

data = load_output_data(OUTPUT_JSON)
if data is None:
    st.error(
        "⚠️ `logistics_output.json` nenalezen.  \n"
        "Spusť nejprve: `python logistics_command_center.py`"
    )
    st.stop()

df  = build_shipments_df(data)
bi  = data["bi_statistics"]
roi = compute_roi(df, bi)


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 7: NAVIGACE — 3 záložky ihned pod záhlavím ──
# ══════════════════════════════════════════════════════════════════════════════

nav_exec, nav_shoptet, nav_tracking = st.tabs([
    "📊  Executive Control Center",
    "🛒  Shoptet Orders Dispatch",
    "🔍  Shipment Database",
])


# ════════════════════════════════════════════════════════════════════════════════
# SEKCE A ── EXECUTIVE CONTROL CENTER
# Lineární flow: KPI → Semafor (celá šířka) → Mapa (celá šířka) → ROI → Grafy
# ════════════════════════════════════════════════════════════════════════════════

with nav_exec:

    # ── A1: KPI LIŠTA — 5 custom HTML karet, žádné st.metric ──
    pending_shoptet = len(SHOPTET_ORDERS) - len(st.session_state.dispatched_orders)
    kpi_cols = st.columns(5)
    kpi_items = [
        ("📦", str(bi["total_shipments"]),                             "Zásilky celkem"),
        ("✅", str(bi["status_breakdown"].get("Delivered", 0)),        "Doručeno"),
        ("💥", str(bi["damaged_shipments"]),                           "Poškozeno"),
        ("🔴", str(bi["high_risk_shipments"]),                         "Vysoké riziko"),
        ("🏬", str(pending_shoptet),                                   "Shoptet — čeká"),
    ]
    for col, (icon, value, label) in zip(kpi_cols, kpi_items):
        col.markdown(kpi_card(icon, value, label), unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── A2: SVOZOVÁ OKNA — 2 rovnocenné sloupce přes celou šířku ──
    # Klíčová oprava: dost místa pro "Zásilkovna" bez lámání textu
    st.subheader("⏱️ Svozová okna — dnešní den")
    sem_l, sem_r = st.columns(2)
    with sem_l:
        render_semafor_card(
            "PPL", "🚛", CARRIER_PICKUP_TIMES["PPL"],
            "ppl_handed_off", "ppl_handoff_time", "exec_ppl",
        )
    with sem_r:
        render_semafor_card(
            "Zásilkovna", "📮", CARRIER_PICKUP_TIMES["Zásilkovna"],
            "zasilkovna_handed_off", "zasilkovna_handoff_time", "exec_zas",
        )

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── A3: MAPA — celá šířka, výška 420px, dominantní vizuální prvek ──
    st.subheader("🗺️ Live mapa zásilek — Česká republika")
    st.markdown(map_legend(), unsafe_allow_html=True)

    map_df = df[["lat", "lon", "_risk"]].copy()
    map_df["color"] = map_df["_risk"].map(RISK_COLOR)
    # Mapa bez st.columns = plná šířka stránky
    st.map(map_df, latitude="lat", longitude="lon", color="color", size=3000, zoom=6, height=420)

    st.divider()

    # ── A4: ROI SEKCE — 4 custom HTML stat karty + roční banner ──
    st.subheader("💰 Business ROI — přínos systému")
    roi_cols = st.columns(4)
    roi_items = [
        ("📅", "Denní úspora",      f"{roi['daily_czk']:,} Kč",   f"{roi['total']} anomálií zachyceno"),
        ("📆", "Měsíční projekce",  f"{roi['monthly_czk']:,} Kč", f"{roi['monthly_h']} h ušetřeno"),
        ("📞", "Zákaznická podpora", f"{roi['support_czk']:,} Kč", ""),
        ("📦", "Zachráněné vratky",  f"{roi['returns_czk']:,} Kč", ""),
    ]
    for col, (icon, label, value, sub) in zip(roi_cols, roi_items):
        col.markdown(stat_card(icon, label, value, sub), unsafe_allow_html=True)

    # Roční výsledek jako prominentní banner — headline pro manažerskou prezentaci
    annual_czk = roi["monthly_czk"] * 12
    annual_h   = roi["monthly_h"]   * 12
    st.markdown(annual_banner(annual_czk, annual_h), unsafe_allow_html=True)

    st.divider()

    # ── A5: GRAFY ──
    ch1, ch2 = st.columns(2)
    with ch1:
        st.subheader("📊 Stav zásilek")
        status_df = (
            pd.DataFrame(list(bi["status_breakdown"].items()), columns=["Status", "Počet"])
            .set_index("Status")
        )
        st.bar_chart(status_df, color="#4361EE", use_container_width=True)

    with ch2:
        st.subheader("📣 Marketing triggery")
        trigger_df = (
            df["_trigger"].value_counts()
            .rename_axis("Trigger").reset_index(name="Počet").set_index("Trigger")
        )
        st.bar_chart(trigger_df, color="#4FC3F7", use_container_width=True)

    st.divider()

    # ── A6: VÝKONNOST DOPRAVCŮ — custom HTML stat karty ──
    st.subheader("🚛 Výkonnost dopravců")
    carrier_data = bi["avg_transit_hours_by_carrier"]
    c_cols = st.columns(len(carrier_data))
    for col, (carrier, avg_h) in zip(c_cols, carrier_data.items()):
        speed = ("⚡ Rychlý" if avg_h < 40 else "⏱️ Průměrný" if avg_h < 80 else "🐢 Pomalý")
        col.markdown(stat_card("🚛", carrier, f"{avg_h} h", speed), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SEKCE B ── SHOPTET ORDERS DISPATCH
# ════════════════════════════════════════════════════════════════════════════════

with nav_shoptet:

    # KPI lišta Shoptetu — custom HTML, konzistentní s Executive dashboardem
    total_sh      = len(SHOPTET_ORDERS)
    dispatched_sh = len(st.session_state.dispatched_orders)
    pending_sh    = total_sh - dispatched_sh
    express_sh    = sum(
        1 for o in SHOPTET_ORDERS
        if o.get("priority") == "express"
        and o["order_id"] not in st.session_state.dispatched_orders
    )

    sh_cols = st.columns(4)
    sh_items = [
        ("📥", str(total_sh),      "Objednávky celkem"),
        ("⏳", str(pending_sh),    "Čeká na expedici"),
        ("✅", str(dispatched_sh), "Expedováno"),
        ("🚀", str(express_sh),    "Express — čeká"),
    ]
    for col, (icon, value, label) in zip(sh_cols, sh_items):
        col.markdown(kpi_card(icon, value, label), unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.divider()

    # Filtry
    with st.container(border=True):
        st.markdown(f'<span style="font-weight:600;color:{_C_TEXT}">🔍 Filtry</span>', unsafe_allow_html=True)
        sf1, sf2, sf3 = st.columns(3)
        with sf1:
            all_carriers = sorted({o["carrier"] for o in SHOPTET_ORDERS})
            sel_carrier  = st.multiselect("Dopravce", all_carriers, default=all_carriers, key="sh_carr")
        with sf2:
            sel_priority = st.multiselect("Priorita", ["express", "normal"], default=["express", "normal"], key="sh_prio")
        with sf3:
            sel_stav = st.radio("Stav", ["Vše", "Čeká na expedici", "Expedováno"], horizontal=True, key="sh_stav")

    # Aplikace filtrů
    filtered_sh = [
        o for o in SHOPTET_ORDERS
        if o["carrier"] in sel_carrier
        and o.get("priority", "normal") in sel_priority
        and (
            sel_stav == "Vše"
            or (sel_stav == "Čeká na expedici" and o["order_id"] not in st.session_state.dispatched_orders)
            or (sel_stav == "Expedováno"        and o["order_id"] in st.session_state.dispatched_orders)
        )
    ]

    # Hromadné akce
    ba1, ba2, ba3, _ = st.columns([1.6, 1.4, 2.4, 2])
    with ba1:
        if st.button("☑️ Vybrat vše čekající", use_container_width=True):
            for o in filtered_sh:
                if o["order_id"] not in st.session_state.dispatched_orders:
                    st.session_state[f"chk_{o['order_id']}"] = True
            st.rerun()
    with ba2:
        if st.button("⬜ Odznačit vše", use_container_width=True):
            for o in filtered_sh:
                st.session_state[f"chk_{o['order_id']}"] = False
            st.rerun()
    with ba3:
        sel_pending = [
            o["order_id"] for o in filtered_sh
            if o["order_id"] not in st.session_state.dispatched_orders
            and st.session_state.get(f"chk_{o['order_id']}", True)
        ]
        if sel_pending:
            if st.button(f"📦 Expedovat vybrané ({len(sel_pending)})", use_container_width=True, type="primary"):
                for oid in sel_pending:
                    st.session_state.dispatched_orders.add(oid)
                st.toast(f"✅ {len(sel_pending)} objednávek odesláno do expedice!", icon="📦")
                st.rerun()

    st.caption(f"Zobrazeno **{len(filtered_sh)}** z {total_sh} objednávek")
    st.markdown("---")

    # Záhlaví tabulky
    th0, th1, th2, th3, th4, th5, th6 = st.columns([0.5, 1.8, 2.8, 1.6, 1, 1.3, 1.5])
    for col, lbl in zip([th0, th1, th2, th3, th4, th5, th6],
                        ["☑️", "ID", "Zákazník", "Dopravce", "Priorita", "Hodnota", "Akce"]):
        col.markdown(f"**{lbl}**")
    st.markdown("---")

    # Řádky objednávek
    for order in filtered_sh:
        oid           = order["order_id"]
        is_dispatched = oid in st.session_state.dispatched_orders
        c0, c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1.8, 2.8, 1.6, 1, 1.3, 1.5])
        with c0:
            if not is_dispatched:
                st.checkbox("", key=f"chk_{oid}", value=st.session_state.get(f"chk_{oid}", True))
        c1.markdown(f"`{oid}`")
        c2.text(order["customer"])
        c3.text(order["carrier"])
        c4.markdown("🚀 **E**" if order.get("priority") == "express" else "📦")
        c5.markdown(f"{order['value']:,} Kč")
        with c6:
            if is_dispatched:
                st.success("✅ Expedováno")
            else:
                if st.button("📦 Expedovat", key=f"disp_{oid}", use_container_width=True, type="primary"):
                    st.session_state.dispatched_orders.add(oid)
                    st.session_state[f"chk_{oid}"] = False
                    st.toast(f"✅ {oid} odesláno do expedice!", icon="📦")
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# SEKCE C ── SHIPMENT DATABASE
# Filtry → fixní tabulka → expanders pouze zde (databáze 200+ záznamů)
# ════════════════════════════════════════════════════════════════════════════════

with nav_tracking:

    # Filtrační panel
    with st.container(border=True):
        st.markdown(f'<span style="font-weight:600;color:{_C_TEXT}">🔍 Vyhledávání & Filtry</span>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
        with f1:
            search_q = st.text_input("s", placeholder="zásilka, region, dopravce…", label_visibility="collapsed")
            st.caption("🔍 Fulltextové hledání")
        with f2:
            carrier_opts = sorted(df["Carrier"].unique().tolist())
            sel_c = st.multiselect("c", carrier_opts, default=carrier_opts, key="tr_c", label_visibility="collapsed")
            st.caption("🚛 Filtr: Dopravce")
        with f3:
            status_opts = sorted(df["_status"].unique().tolist())
            sel_s = st.multiselect("st", status_opts, default=status_opts, key="tr_s", label_visibility="collapsed")
            st.caption("📋 Filtr: Stav")
        with f4:
            sel_r = st.radio("r", ["Všechna", "🟢 low", "🟡 medium", "🔴 high"],
                             horizontal=True, key="tr_r", label_visibility="collapsed")
            st.caption("⚡ Filtr: Riziko")

    # Aplikace filtrů
    fdf = df.copy()
    if search_q:
        mask = (fdf["Tracking"].str.contains(search_q, case=False, na=False)
                | fdf["Carrier"].str.contains(search_q, case=False, na=False)
                | fdf["Region"].str.contains(search_q, case=False, na=False))
        fdf = fdf[mask]
    if sel_c:
        fdf = fdf[fdf["Carrier"].isin(sel_c)]
    if sel_s:
        fdf = fdf[fdf["_status"].isin(sel_s)]
    if sel_r != "Všechna":
        fdf = fdf[fdf["_risk"] == {"🟢 low": "low", "🟡 medium": "medium", "🔴 high": "high"}[sel_r]]

    badge_txt = "⚠️ Filtr aktivní — " if len(fdf) < len(df) else ""
    st.markdown(
        f'{badge_txt}Nalezeno **{len(fdf)}** z **{len(df)}** zásilek'
        + (" | výsledky omezeny filtrem" if len(fdf) < len(df) else " | zobrazeny všechny zásilky")
    )
    st.divider()

    # Hlavní tabulka — fixní výška pro plynulé listování stovkami řádků
    st.dataframe(
        fdf[["Tracking", "Carrier", "Status", "Risk", "Region", "Marketing Trigger"]],
        use_container_width=True, hide_index=True, height=320,
        column_config={
            "Tracking":          st.column_config.TextColumn("Číslo zásilky",    width="medium"),
            "Carrier":           st.column_config.TextColumn("Dopravce",          width="small"),
            "Status":            st.column_config.TextColumn("Stav",              width="medium"),
            "Risk":              st.column_config.TextColumn("Riziko",            width="small"),
            "Region":            st.column_config.TextColumn("Region",            width="medium"),
            "Marketing Trigger": st.column_config.TextColumn("Marketing Trigger", width="large"),
        },
    )

    st.divider()

    # Expanders — pouze zde, kde je databáze potenciálně stovek řádků
    if fdf.empty:
        st.info("Žádné zásilky neodpovídají zadaným filtrům.")
    else:
        st.caption("Klikni na zásilku pro AI analýzu, doporučení podpory, marketing trigger a expediční akce.")
        for _, row in fdf.iterrows():
            exp_label = (
                f"📦  {row['Tracking']}  ·  {row['Carrier']}  ·  "
                f"{row['_status']}  ·  {row['_risk'].upper()}  ·  {row['Region']}"
            )
            with st.expander(exp_label, expanded=False):
                d_l, d_r = st.columns(2)
                with d_l:
                    st.markdown("**🎧 Zákaznická podpora**")
                    {"high": st.error, "medium": st.warning}.get(row["_risk"], st.success)(row["Support Action"])
                with d_r:
                    st.markdown("**📣 Marketing trigger**")
                    getattr(st, TRIGGER_ALERT.get(row["_trigger"], "info"))(
                        f"**{TRIGGER_ICON.get(row['_trigger'], '📌')} {row['_trigger']}**"
                    )
                st.markdown("---")
                a_l, a_m, a_r = st.columns([2, 2, 3])
                with a_l:
                    if row["Tracking"] in st.session_state.printed_labels:
                        st.success("🖨️ Štítek vytištěn")
                    elif st.button("🖨️ Tisk štítku (Zebra)", key=f"print_{row['Tracking']}", use_container_width=True):
                        st.session_state.printed_labels.add(row["Tracking"])
                        st.toast(f"Štítek pro **{row['Tracking']}** odeslán na tiskárnu Zebra.", icon="🖨️")
                        st.rerun()
                with a_m:
                    st.info(f"🌐 **{row['Carrier']}**\n`{CARRIER_PORTAL_INFO.get(row['Carrier'], 'portál')}`")
                with a_r:
                    st.caption(f"Zásilka: `{row['Tracking']}`  \nGPS: `{row['lat']:.4f}°N, {row['lon']:.4f}°E`")
