#!/usr/bin/env python3
"""
AI Logistics Command Center - Lifecycle Dispatch v10.0
Portfolio Project #3 | Martina Dohnalova
"""
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="AI Logistics Command Center",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


C_BG = "#f7f7f8"
C_SURFACE = "#ffffff"
C_TEXT = "#1a1d24"
C_MUTED = "#5c6270"
C_BORDER = "#d8dbe2"
C_ACCENT = "#a36a52"
C_CRITICAL = "#b3261e"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {C_BG}; color: {C_TEXT}; }}
    .app-shell {{
        background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 12px;
        padding: 18px 20px; margin-bottom: 14px;
    }}
    .title-line {{
        font-size: 1.35rem; font-weight: 700; letter-spacing: .3px; color: {C_TEXT};
        margin: 0;
    }}
    .subtitle-line {{
        margin-top: 6px; font-size: .9rem; color: {C_MUTED};
    }}
    .panel-note {{
        border:1px solid {C_BORDER}; background:#f1f3f7; color:{C_TEXT};
        border-radius:8px; padding:9px 10px; font-size:.86rem;
    }}
    .status-chip {{
        display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid {C_BORDER};
        background:#f7f8fa; color:{C_MUTED}; font-size:.75rem;
    }}
    .priority-note {{
        border-left:6px solid {C_CRITICAL}; padding:8px 10px; border-radius:8px;
        background:#fff5f4; color:{C_CRITICAL}; margin-bottom:10px; font-weight:600;
    }}
    .log-box {{
        background:#171a20; color:#d8dde8; border:1px solid #2a2f3a;
        border-radius:8px; padding:10px; max-height:220px; overflow-y:auto;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size:.8rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# ── DATOVÁ VRSTVA: DVA NEZÁVISLÉ OKRUHY ──
# Stejný princip jako EnterpriseDataBridge v logistics_command_center.py: appka je
# oddělená od zdroje dat, takže přechod z dema na ostrý provoz je jen změna režimu,
# ne přepis kódu. Okruh 1 (nové objednávky z e-shopu) a okruh 2 (stavy od dopravců)
# jedou nezávisle na sobě, protože v realitě to jsou dva různé systémy/API.
# ══════════════════════════════════════════════════════════════════════════════

CARRIERS = ["Zasilkovna", "PPL", "DHL", "Ceska Posta"]
REGIONS = ["Praha", "Jihomoravsky", "Moravskoslezsky", "Liberecky", "Ustecky"]

# V produkci se nastaví přes proměnné prostředí, ne ručně v kódu.
SHIPMENT_SOURCE_MODE = os.environ.get("SHIPMENT_SOURCE_MODE", "DEMO")  # DEMO | SHOPTET_API
CARRIER_SOURCE_MODE = os.environ.get("CARRIER_SOURCE_MODE", "DEMO")  # DEMO | CARRIER_API


class ShipmentInputBridge:
    """
    OKRUH 1 — vstupní zásilky z e-shopu.
    DEMO: generuje fiktivní objednávky. LIVE (SHOPTET_API): napojení na webhook/REST API
    e-shopu při expedici objednávky — musí vracet stejný tvar dat (dict se stejnými klíči).
    """

    def __init__(self, mode: str = "DEMO"):
        self.mode = mode

    def seed_initial_batch(self, count: int) -> list[dict]:
        """Počáteční snímek zásilek, které už jsou v systému (Reset Data / start appky)."""
        if self.mode == "SHOPTET_API":
            raise ConnectionError("Shoptet API není nakonfigurováno (chybí SHOPTET_API_KEY).")
        random.seed(42)
        return [self._build_seed_row(i) for i in range(1, count + 1)]

    def fetch_new_shipments(self, start_seq: int, count: int) -> list[dict]:
        """Nově expedované zásilky — jako by právě dorazily z e-shopu (čerstvé, 0h)."""
        if self.mode == "SHOPTET_API":
            raise ConnectionError("Shoptet API není nakonfigurováno (chybí SHOPTET_API_KEY).")
        rows = []
        for offset in range(count):
            seq = start_seq + offset
            carrier = random.choice(CARRIERS)
            rows.append(
                {
                    "order_id": str(458000 + seq),
                    "carrier": carrier,
                    "time_in_system": 0,
                    "status": "In Transit",
                    "action": "",
                    "hours_in_transit": 0,
                    "hours_in_box": 0,
                    "region": random.choice(REGIONS),
                    "tracking": f"{carrier[:3].upper()}-2026{seq:03d}",
                    "marketing_sent": False,
                    "created_seq": seq,
                }
            )
        return rows

    def _build_seed_row(self, i: int) -> dict:
        carrier = random.choice(CARRIERS)
        region = random.choice(REGIONS)
        p = random.random()
        if p < 0.05:
            status, hours_in_transit, hours_in_box = "Damaged", random.randint(12, 96), 0
        elif p < 0.18:
            status = "Warning - Unclaimed"
            hours_in_transit, hours_in_box = random.randint(24, 72), random.randint(8, 72)
        elif p < 0.80:
            status, hours_in_transit, hours_in_box = "In Transit", random.randint(6, 28), 0
        else:
            status, hours_in_transit, hours_in_box = "Delivered", random.randint(24, 60), 0

        return {
            "order_id": str(458000 + i),
            "carrier": carrier,
            "time_in_system": hours_in_transit + hours_in_box,
            "status": status,
            "action": "",
            "hours_in_transit": hours_in_transit,
            "hours_in_box": hours_in_box,
            "region": region,
            "tracking": f"{carrier[:3].upper()}-2026{i:03d}",
            "marketing_sent": False,
            "created_seq": i,
        }


class CarrierStatusBridge:
    """
    OKRUH 2 — stavové aktualizace od dopravců.
    DEMO: simuluje typické chování každého dopravce v čase. LIVE (CARRIER_API): pro
    každého dopravce zavolá jeho tracking API/webhook (Zásilkovna, PPL, DHL, Česká pošta)
    a promítne reálný stav zásilky do stejných polí.
    """

    def __init__(self, mode: str = "DEMO"):
        self.mode = mode

    def poll_updates(self, shipments: list[dict], hours_passed: int, resolved: set) -> None:
        if self.mode == "CARRIER_API":
            raise ConnectionError("Napojení na API dopravců není nakonfigurováno (chybí API klíče).")
        for row in shipments:
            if row["order_id"] in resolved:
                continue

            if row["status"] == "In Transit":
                row["hours_in_transit"] += hours_passed
                row["time_in_system"] = row["hours_in_transit"] + row["hours_in_box"]
                if row["hours_in_transit"] > 36:
                    if row["carrier"] == "Zasilkovna":
                        row["status"] = "Warning - Unclaimed"
                        row["hours_in_box"] = max(1, row["hours_in_box"])
                    else:
                        row["status"] = "Delivered"

            elif row["status"] == "Warning - Unclaimed":
                row["hours_in_transit"] += hours_passed
                row["hours_in_box"] += hours_passed
                row["time_in_system"] = row["hours_in_transit"] + row["hours_in_box"]


shipment_bridge = ShipmentInputBridge(mode=SHIPMENT_SOURCE_MODE)
carrier_bridge = CarrierStatusBridge(mode=CARRIER_SOURCE_MODE)


# Session state
if "system_time_hours" not in st.session_state:
    st.session_state.system_time_hours = 0
if "simulation_data" not in st.session_state:
    st.session_state.simulation_data = []
if "marketing_logs" not in st.session_state:
    st.session_state.marketing_logs = ["BOOT 00:00: Engine initialized"]
if "resolved_shipments" not in st.session_state:
    st.session_state.resolved_shipments = set()
if "cfg_unclaimed_hours" not in st.session_state:
    st.session_state.cfg_unclaimed_hours = 48
if "cfg_unclaimed_discount" not in st.session_state:
    st.session_state.cfg_unclaimed_discount = 5
if "global_carrier_filter" not in st.session_state:
    st.session_state.global_carrier_filter = "ALL"
if "action_state" not in st.session_state:
    st.session_state.action_state = {}
if "bulk_notice" not in st.session_state:
    st.session_state.bulk_notice = {}
if "selected_rows" not in st.session_state:
    st.session_state["selected_rows"] = []
if "next_shipment_seq" not in st.session_state:
    st.session_state.next_shipment_seq = 201
TAB_KEYS = [
    "predano_prepravci",
    "v_preprave",
    "doruceno_do_48h",
    "nevyzvednuto_over_48h",
    "poskozeno",
    "vyzvednuto",
]

TAB_TITLES = {
    "predano_prepravci": "Předáno přepravci",
    "v_preprave": "V přepravě/Na cestě",
    "doruceno_do_48h": "Doručeno do 48h",
    "nevyzvednuto_over_48h": "Nevyzvednuto (>48h)",
    "poskozeno": "Poškozeno",
    "vyzvednuto": "Vyzvednuto",
}

if "selection_state" not in st.session_state:
    st.session_state.selection_state = {}
if "bulk_notice" not in st.session_state:
    st.session_state.bulk_notice = {}
if "select_all_state" not in st.session_state:
    st.session_state.select_all_state = {}
for _tab_key in TAB_KEYS:
    st.session_state.selection_state.setdefault(_tab_key, [])
    st.session_state.bulk_notice.setdefault(_tab_key, "")
    st.session_state.select_all_state.setdefault(_tab_key, False)


def _now_stamp() -> str:
    return datetime.now().strftime("%H:%M")


def generate_sandbox_data() -> None:
    st.session_state.simulation_data = shipment_bridge.seed_initial_batch(200)
    st.session_state.next_shipment_seq = 201
    st.session_state.system_time_hours = 0
    st.session_state.marketing_logs = ["BOOT 00:00: Sandbox regenerated"]
    st.session_state.resolved_shipments = set()
    st.session_state.action_state = {}
    st.session_state.bulk_notice = {}
    st.session_state.selection_state = {key: [] for key in TAB_KEYS}


def update_engine_logic(hours_passed: int) -> None:
    st.session_state.system_time_hours += hours_passed

    # OKRUH 2: nezávislá aktualizace stavů od dopravců pro zásilky už v systému.
    carrier_bridge.poll_updates(
        st.session_state.simulation_data, hours_passed, st.session_state.resolved_shipments
    )

    # OKRUH 1: nezávislý přítok nových objednávek z e-shopu.
    new_count = max(1, hours_passed // 3)
    start_seq = st.session_state.next_shipment_seq
    new_rows = shipment_bridge.fetch_new_shipments(start_seq, new_count)
    st.session_state.simulation_data.extend(new_rows)
    st.session_state.next_shipment_seq = start_seq + new_count
    st.session_state.marketing_logs.insert(
        0, f"{_now_stamp()} OKRUH 1: přijato {new_count} nových objednávek z e-shopu"
    )


def log_action(order_id: str, action_type: str) -> str:
    stamp = _now_stamp()
    st.session_state.action_state.setdefault(order_id, {})[action_type] = stamp
    return stamp


def action_text(order: dict) -> str:
    actions = st.session_state.action_state.get(order["order_id"], {})
    if not actions:
        return ""
    latest_action, latest_stamp = list(actions.items())[-1]
    labels = {
        "print": "Tisk štítku",
        "apology": "Odesláno email",
        "carrier_check": "Prověřeno u dopravce",
        "pickup_reminder": "Výzva k vyzvednutí",
    }
    return f"✅ {labels.get(latest_action, 'Akce provedena')}: {latest_stamp}"


def get_filtered_rows(df, status_filter=None):
    """Vrátí filtrovaná data podle stavu."""
    if status_filter:
        return df[df["status"] == status_filter]
    return df


def load_data() -> pd.DataFrame:
    """Načte data ze souboru shipments_input.csv a doplní status z raw_status."""
    try:
        df = pd.read_csv("shipments_input.csv")
    except FileNotFoundError:
        return pd.DataFrame()

    if "status" not in df.columns:
        df["status"] = df.get("raw_status", "")

    if "raw_status" in df.columns:
        status_map = {
            "zasilkovna_received": "Předáno přepravci",
            "ppl_damaged_at_depo": "Damaged",
            "dhl_delivered_ok": "Vyzvednuto",
            "zasilkovna_unclaimed_warning": "Doručeno",
            "cp_stored_at_post_office": "Doručeno",
        }
        df["status"] = df["raw_status"].map(status_map).fillna(df["status"])

    if "hours_in_box" not in df.columns and "hours_stored_in_box" in df.columns:
        df["hours_in_box"] = df["hours_stored_in_box"]

    if "time_in_system" not in df.columns:
        transit = pd.to_numeric(df.get("hours_in_transit", 0), errors="coerce").fillna(0)
        inbox = pd.to_numeric(df.get("hours_in_box", 0), errors="coerce").fillna(0)
        df["time_in_system"] = transit + inbox

    return df


def apply_order_action(order: dict, action_type: str) -> None:
    """Provede akci nad jednou zásilkou a zapíše do logu."""
    order_id = order.get("order_id", order.get("ID objednávky", "?"))
    if action_type == "print":
        st.session_state.marketing_logs.insert(0, f"{_now_stamp()} Tisk štítku: {order_id}")
        log_action(order_id, "print")
    elif action_type == "apology":
        st.session_state.marketing_logs.insert(
            0,
            f"{_now_stamp()} Omluvný e-mail zákazníkovi (balíček poškozen při přepravě) + odesílám nový balíček + kupón na další nákup: {order_id}",
        )
        log_action(order_id, "apology")
    elif action_type == "carrier_check":
        st.session_state.marketing_logs.insert(0, f"{_now_stamp()} Prověřuji u dopravce: {order_id}")
        log_action(order_id, "carrier_check")
    elif action_type == "pickup_reminder":
        st.session_state.marketing_logs.insert(
            0,
            f"{_now_stamp()} Odesílám e-mail 'Vyzvedněte si svůj balíček ještě dnes a odkryjte 10% slevu na další nákup': {order_id}",
        )
        log_action(order_id, "pickup_reminder")


def build_table(rows: list[dict], tab_key: str) -> "pd.DataFrame":
    """Sestaví DataFrame pro st.data_editor z listu zásilek."""
    data = []
    for row in rows:
        action_stamp = ""
        if row.get("order_id") in st.session_state.action_state:
            latest = list(st.session_state.action_state[row["order_id"]].items())[-1]
            labels = {
                "print": "Tisk štítku",
                "apology": "Odesláno email",
                "carrier_check": "Prověřeno u dopravce",
                "pickup_reminder": "Výzva k vyzvednutí",
            }
            action_stamp = f"✅ {labels.get(latest[0], 'Akce')}: {latest[1]}"
        priority = "⚠ PRIORITA" if tab_key == "nevyzvednuto_over_48h" else ""
        data.append(
            {
                "Vybrat": False,
                "ID objednávky": row.get("order_id", ""),
                "Dopravce": row.get("carrier", ""),
                "Čas v systému": row.get("time_in_system", 0),
                "Stav": (row.get("status", "") + (" | " + priority if priority else "")),
                "Akce": action_stamp,
            }
        )
    return pd.DataFrame(data)


def select_queue_rows(df, queue_type):
    """Vrátí filtrovaná data pro jednotlivé záložky.

    Sandboxový engine (generate_sandbox_data/update_engine_logic) pracuje se 4 stavy:
    "In Transit", "Warning - Unclaimed", "Delivered", "Damaged". Fáze "Předáno přepravci"
    není samostatný stav, ale první hodiny "In Transit" (čerstvě předáno, ještě nejede).
    """
    if df.empty:
        return df

    if queue_type == "predano_prepravci":
        return df[(df["status"] == "In Transit") & (df["hours_in_transit"] <= 6)]
    elif queue_type == "v_preprave":
        return df[(df["status"] == "In Transit") & (df["hours_in_transit"] > 6)]
    elif queue_type == "doruceno_do_48h":
        return df[df["status"] == "Delivered"]
    elif queue_type == "nevyzvednuto_over_48h":
        return df[df["status"] == "Warning - Unclaimed"]
    elif queue_type == "poskozeno":
        return df[df["status"] == "Damaged"]
    elif queue_type == "vyzvednuto":
        return df[df["status"] == "Vyzvednuto"]
    return df


def get_visible_rows() -> list[dict]:
    rows = list(st.session_state.simulation_data)
    if st.session_state.global_carrier_filter != "ALL":
        rows = [r for r in rows if r["carrier"] == st.session_state.global_carrier_filter]
    return rows


def render_tab(tab_key: str, rows: list[dict]) -> None:
    title = TAB_TITLES[tab_key]
    st.markdown(f"### {title}")

    # Pomocná funkce pro bezpečné získání ID zásilky
    def get_id(row):
        return row.get("order_id", row.get("tracking_number", "Neznámé ID"))

    if tab_key == "nevyzvednuto_over_48h":
        st.markdown("<div class='priority-note'>Řádky v této záložce jsou prioritní k řešení.</div>", unsafe_allow_html=True)

    notice = st.session_state.bulk_notice.get(tab_key, "")
    if notice:
        st.markdown(f"<div class='panel-note'>{notice}</div>", unsafe_allow_html=True)

    selected_df_key = f"editor_{tab_key}"
    select_all_key = f"select_all_{tab_key}"

    selected_orders = st.session_state.selection_state.get(tab_key, [])
    
    # OPRAVA: Změna přístupu na get_id
    if st.session_state.select_all_state.get(tab_key, False):
        selected_orders = [get_id(row) for row in rows]
        st.session_state.selection_state[tab_key] = selected_orders
    st.session_state["selected_rows"] = selected_orders

    header_cols = st.columns([1.2, 1, 1, 1] if tab_key == "nevyzvednuto_over_48h" else [1.2, 1, 1])
    with header_cols[0]:
        select_all_checked = st.checkbox("Vybrat vše na stránce", key=select_all_key, value=st.session_state.select_all_state.get(tab_key, False))
        st.session_state.select_all_state[tab_key] = select_all_checked
        if select_all_checked:
            selected_orders = [get_id(row) for row in rows]
            st.session_state.selection_state[tab_key] = selected_orders
        st.markdown(f"<div class='panel-note'>Vybráno: {len(selected_orders)} zásilek</div>", unsafe_allow_html=True)

    table_df = build_table(rows, tab_key)
    if table_df.empty:
        st.info("V této frontě aktuálně nejsou žádné zásilky.")
    else:
        table_df["Vybrat"] = table_df["ID objednávky"].isin(selected_orders)
        edited_df = st.data_editor(
            table_df,
            hide_index=True,
            use_container_width=True,
            disabled=["ID objednávky", "Dopravce", "Čas v systému", "Stav", "Akce"],
            key=selected_df_key,
        )
        if not select_all_checked:
            edited_selection = edited_df.loc[edited_df["Vybrat"], "ID objednávky"].tolist()
            if edited_selection != selected_orders:
                selected_orders = edited_selection
                st.session_state.selection_state[tab_key] = selected_orders

    st.session_state["selected_rows"] = selected_orders

    bulk_disabled = len(selected_orders) == 0
    bulk_cols = st.columns(4)

    def _apply_to_selected(action_type):
        filtered_df = pd.DataFrame(rows)
        # OPRAVA: Filtrování podle tracking_number (které jsme si sjednotili)
        targets = filtered_df[filtered_df.apply(get_id, axis=1).isin(selected_orders)].to_dict("records")
        for order in targets:
            apply_order_action(order, action_type)
        st.session_state.bulk_notice[tab_key] = f"✅ Akce provedena"
        st.session_state.selection_state[tab_key] = []
        st.rerun()

    with bulk_cols[0]:
        if st.button("Tisk štítků", key=f"bulk_print_{tab_key}", disabled=bulk_disabled): _apply_to_selected("print")
    with bulk_cols[1]:
        if st.button("Omluva/Sleva", key=f"bulk_apology_{tab_key}", disabled=bulk_disabled): _apply_to_selected("apology")
    with bulk_cols[2]:
        if st.button("Prověřit", key=f"bulk_check_{tab_key}", disabled=bulk_disabled): _apply_to_selected("carrier_check")
    if tab_key == "nevyzvednuto_over_48h":
        with bulk_cols[3]:
            if st.button("Výzva k vyzvednutí", key=f"bulk_pickup_{tab_key}", disabled=bulk_disabled): _apply_to_selected("pickup_reminder")


if not st.session_state.simulation_data:
    generate_sandbox_data()

# Sidebar
st.sidebar.markdown("## Enterprise Control")
st.sidebar.markdown(
    f"""
    <div class="panel-note">
    Active mode: sandbox simulation<br>
    Dataset: {len(st.session_state.simulation_data)} shipments<br>
    Simulated age: {st.session_state.system_time_hours} h
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Time Shift")
ss1, ss2 = st.sidebar.columns(2)
with ss1:
    if st.button("+1h", use_container_width=True):
        update_engine_logic(1)
        st.rerun()
with ss2:
    if st.button("+24h", use_container_width=True):
        update_engine_logic(24)
        st.rerun()

if st.sidebar.button("+6h", use_container_width=True):
    update_engine_logic(6)
    st.rerun()
if st.sidebar.button("Reset Data", use_container_width=True):
    generate_sandbox_data()
    st.rerun()

st.sidebar.markdown("### Zdroje dat (2 nezávislé okruhy)")
st.sidebar.markdown(
    f"""
    <div class="panel-note">
    <span class="status-chip">{SHIPMENT_SOURCE_MODE}</span> Okruh 1 — Objednávky z e-shopu<br>
    <span class="status-chip">{CARRIER_SOURCE_MODE}</span> Okruh 2 — Stavy od dopravců
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Globální filtr")
all_rows = get_visible_rows()
carriers = sorted({row["carrier"] for row in all_rows})
options = ["ALL"] + carriers
st.session_state.global_carrier_filter = st.sidebar.selectbox(
    "Dopravce",
    options,
    index=options.index(st.session_state.global_carrier_filter)
    if st.session_state.global_carrier_filter in options
    else 0,
)


# Header
st.markdown(
    """
    <div class="app-shell">
      <p class="title-line">AI Logistics Command Center</p>
      <p class="subtitle-line">Stavový automat s tabulkami a hromadnými operacemi</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Engine progression log can shift state before rendering
filtered_rows = get_visible_rows()
for row in filtered_rows:
    if row["status"] == "Warning - Unclaimed" and row["hours_in_box"] > 48 and not row.get("marketing_sent", False):
        row["marketing_sent"] = True
        st.session_state.marketing_logs.insert(0, f"{_now_stamp()} MARKETING trigger order={row['order_id']}")
    if row["status"] == "Damaged" and not row.get("damage_alert_sent", False):
        row["damage_alert_sent"] = True
        st.session_state.marketing_logs.insert(
            0,
            f"{_now_stamp()} ALERT poškozeno při přepravě, odesílám omluvu + nový balíček + kupón: order={row['order_id']}",
        )

filtered_rows_df = pd.DataFrame(filtered_rows)


# Tabs
predano_tab, transit_tab, doruceno_tab, nevyz_tab, poskozeno_tab, vyzvednuto_tab = st.tabs(
    [
        "Předáno přepravci",
        "V přepravě/Na cestě",
        "Doručeno do 48h",
        "Nevyzvednuto (>48h)",
        "Poškozeno",
        "Vyzvednuto",
    ]
)

queue_map = {
    "predano_prepravci": select_queue_rows(filtered_rows_df, "predano_prepravci").to_dict("records"),
    "v_preprave": select_queue_rows(filtered_rows_df, "v_preprave").to_dict("records"),
    "doruceno_do_48h": select_queue_rows(filtered_rows_df, "doruceno_do_48h").to_dict("records"),
    "nevyzvednuto_over_48h": select_queue_rows(filtered_rows_df, "nevyzvednuto_over_48h").to_dict("records"),
    "poskozeno": select_queue_rows(filtered_rows_df, "poskozeno").to_dict("records"),
    "vyzvednuto": select_queue_rows(filtered_rows_df, "vyzvednuto").to_dict("records"),
}

with predano_tab:
    render_tab("predano_prepravci", queue_map["predano_prepravci"])

with transit_tab:
    render_tab("v_preprave", queue_map["v_preprave"])

with doruceno_tab:
    render_tab("doruceno_do_48h", queue_map["doruceno_do_48h"])

with nevyz_tab:
    render_tab("nevyzvednuto_over_48h", queue_map["nevyzvednuto_over_48h"])

with poskozeno_tab:
    render_tab("poskozeno", queue_map["poskozeno"])

with vyzvednuto_tab:
    render_tab("vyzvednuto", queue_map["vyzvednuto"])


# Log
st.markdown("---")
st.markdown("### Log akcí")
st.markdown(
    f"<div class='log-box'>{'<br>'.join(st.session_state.marketing_logs[:120])}</div>",
    unsafe_allow_html=True,
)
