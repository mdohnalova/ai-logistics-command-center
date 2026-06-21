#!/usr/bin/env python3
"""
AI Logistics Command Center & Marketing Predictor
Portfolio Project #3 — AI Vibecoder | Martina Dohnalová

Inteligentní BI systém propojující logistiku a marketing pro e-shopy.
Analyzuje zásilky pomocí Claude AI a pro každou vrací standardizovaný stav,
riziko doručení, GPS souřadnice, marketingový trigger a doporučení pro podporu.
"""

import csv
import json
import os
import time
from datetime import datetime

# ── Pokus o import Anthropic SDK — pokud chybí, spustíme demo režim ──
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 0: KONFIGURACE — cesty k souborům, model a ukázková vstupní data ──
# ══════════════════════════════════════════════════════════════════════════════

INPUT_CSV   = "shipments_input.csv"
OUTPUT_JSON = "logistics_output.json"
OUTPUT_CSV  = "logistics_output.csv"
MODEL_NAME  = "claude-sonnet-4-6"

# Pět ukázkových zásilek simulujících reálné situace v českém e-shopu
SAMPLE_SHIPMENTS = [
    {
        "tracking_number":     "ZAS-2024-001",
        "carrier":             "Zásilkovna",
        "raw_status":          "zasilkovna_received",
        "hours_in_transit":    14,
        "hours_stored_in_box": 0,
        "customer_location":   "Brno-Slatina",
    },
    {
        "tracking_number":     "PPL-2024-002",
        "carrier":             "PPL",
        "raw_status":          "ppl_damaged_at_depo",
        "hours_in_transit":    48,
        "hours_stored_in_box": 0,
        "customer_location":   "Liberec v podještědí",
    },
    {
        "tracking_number":     "DHL-2024-003",
        "carrier":             "DHL",
        "raw_status":          "dhl_delivered_ok",
        "hours_in_transit":    36,
        "hours_stored_in_box": 0,
        "customer_location":   "Praha 4 - Chodov",
    },
    {
        "tracking_number":     "ZAS-2024-004",
        "carrier":             "Zásilkovna",
        "raw_status":          "zasilkovna_unclaimed_warning",
        "hours_in_transit":    72,
        "hours_stored_in_box": 54,
        "customer_location":   "Ostrava-Poruba",
    },
    {
        "tracking_number":     "CP-2024-005",
        "carrier":             "Česká Pošta",
        "raw_status":          "cp_stored_at_post_office",
        "hours_in_transit":    120,
        "hours_stored_in_box": 0,
        "customer_location":   "Děčín 2",
    },
]

# Předpřipravené AI odpovědi pro demo/portfolio režim (bez reálného API klíče)
# Simulují přesně to, co by vrátil Claude po analýze každé zásilky
SIMULATED_AI_RESPONSES: dict[str, dict] = {
    "ZAS-2024-001": {
        "standardized_status":      "In Transit",
        "delivery_risk":            "low",
        "region":                   "Jihomoravský kraj",
        "gps_coordinates":          {"lat": 49.1833, "lon": 16.7167},
        "proactive_support_action": "Standardní průběh — zásilka přijata na depu, doručení očekáváno do 24 h. Aktivně sledovat tracking.",
        "marketing_trigger":        "Pre-delivery product recommendation",
    },
    "PPL-2024-002": {
        "standardized_status":      "Damaged",
        "delivery_risk":            "high",
        "region":                   "Liberecký kraj",
        "gps_coordinates":          {"lat": 50.7663, "lon": 15.0543},
        "proactive_support_action": "URGENTNÍ: Okamžitě zabalit náhradní kus a připravit prioritní zásilku. Informovat zákazníka do 2 h s omluvou a novým tracking číslem.",
        "marketing_trigger":        "Apology Voucher",
    },
    "DHL-2024-003": {
        "standardized_status":      "Delivered",
        "delivery_risk":            "low",
        "region":                   "Praha",
        "gps_coordinates":          {"lat": 50.0233, "lon": 14.4747},
        "proactive_support_action": "Žádná akce nutná — zásilka úspěšně doručena zákazníkovi v termínu.",
        "marketing_trigger":        "Review & Cross-sell request",
    },
    "ZAS-2024-004": {
        "standardized_status":      "Warning - Unclaimed",
        "delivery_risk":            "high",
        "region":                   "Moravskoslezský kraj",
        "gps_coordinates":          {"lat": 49.8277, "lon": 18.1547},
        "proactive_support_action": "Zásilka v Z-Boxu přes 54 h — hrozí automatická vratka do 15 h. Okamžitě kontaktovat zákazníka telefonicky, nabídnout přesměrování na jiný box.",
        "marketing_trigger":        "Urgent SMS with gift coupon",
    },
    "CP-2024-005": {
        "standardized_status":      "Warning - Unclaimed",
        "delivery_risk":            "medium",
        "region":                   "Ústecký kraj",
        "gps_coordinates":          {"lat": 50.7727, "lon": 14.2131},
        "proactive_support_action": "Zásilka uložena na poště 120 h — odeslat e-mailovou upomínku s termínem vyzvednutí. Zvážit prodloužení úložní doby přes přepravce.",
        "marketing_trigger":        "Urgent SMS with gift coupon",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 1: VSTUPNÍ DATA — automatické vytvoření CSV, pokud neexistuje ──
# ══════════════════════════════════════════════════════════════════════════════

def ensure_input_csv_exists(filepath: str) -> None:
    """Zkontroluje existenci vstupního CSV. Pokud soubor chybí, vytvoří ho s ukázkovými daty."""
    if os.path.exists(filepath):
        print(f"✅ Vstupní soubor nalezen: {filepath}")
        return

    # Definice sloupců zásilkového CSV
    fieldnames = [
        "tracking_number", "carrier", "raw_status",
        "hours_in_transit", "hours_stored_in_box", "customer_location",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(SAMPLE_SHIPMENTS)

    print(f"📦 Soubor '{filepath}' byl automaticky vytvořen s {len(SAMPLE_SHIPMENTS)} ukázkovými zásilkami.")


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 2: NAČTENÍ DAT — import zásilek ze vstupního CSV ──
# ══════════════════════════════════════════════════════════════════════════════

def load_shipments_from_csv(filepath: str) -> list[dict]:
    """Načte zásilky ze CSV souboru se striktním UTF-8 kódováním a převede numerická pole."""
    shipments = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Převod časových polí z řetězce na celé číslo pro pozdější výpočty
            row["hours_in_transit"]    = int(row["hours_in_transit"])
            row["hours_stored_in_box"] = int(row["hours_stored_in_box"])
            shipments.append(dict(row))

    print(f"📂 Načteno {len(shipments)} zásilek z '{filepath}'.")
    return shipments


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 3: AI ANALÝZA — prompt builder, API volání, simulace ──
# ══════════════════════════════════════════════════════════════════════════════

def build_analysis_prompt(shipment: dict) -> str:
    """Sestaví přesně strukturovaný prompt pro logisticko-marketingovou analýzu jedné zásilky."""
    return f"""Jsi expert na logistiku a e-commerce marketing pro český trh. Analyzuj zásilku a vrať POUZE validní JSON bez jakéhokoliv dalšího textu, vysvětlení ani markdown formátování.

ZÁSILKA K ANALÝZE:
- Číslo sledování: {shipment['tracking_number']}
- Dopravce: {shipment['carrier']}
- Surový stav systému: {shipment['raw_status']}
- Celkem hodin na cestě: {shipment['hours_in_transit']}
- Hodin v Z-Boxu / výdejním místě: {shipment['hours_stored_in_box']}
- Lokalita zákazníka: {shipment['customer_location']}

Vrať JSON přesně v tomto formátu (bez jakéhokoliv jiného textu):
{{
  "standardized_status": "<In Transit | Damaged | Delivered | Warning - Unclaimed>",
  "delivery_risk": "<low | medium | high>",
  "region": "<název hlavního kraje nebo oblasti ČR pro marketingové segmentování>",
  "gps_coordinates": {{"lat": <zeměpisná šířka jako float>, "lon": <zeměpisná délka jako float>}},
  "proactive_support_action": "<konkrétní interní doporučení pro zákaznickou podporu>",
  "marketing_trigger": "<konkrétní marketingová akce>"
}}

Pravidla pro analýzu:
1. standardized_status: mapuj raw_status na přesně jeden z: In Transit, Damaged, Delivered, Warning - Unclaimed
2. delivery_risk: zvaž stav zásilky, dobu na cestě a riziko vrátky (poškozené/nepřevzaté = high)
3. region: použij český název kraje nebo oblasti (např. "Jihomoravský kraj", "Praha", "Ústecký kraj")
4. gps_coordinates: přibližné GPS souřadnice středu dané lokality pro vizualizaci na mapě
5. proactive_support_action: pro poškozené — urgentní akce (náhradní zásilka + kontakt); pro ohrožené vrátkou — kontakt zákazníka; pro OK — standardní sledování
6. marketing_trigger: doručené → "Review & Cross-sell request"; v boxu/na poště — urgentní připomínka → "Urgent SMS with gift coupon"; poškozené → "Apology Voucher"; na cestě → "Pre-delivery product recommendation"
"""


def analyze_shipment_via_api(client: "anthropic.Anthropic", shipment: dict) -> dict:
    """Odešle zásilku ke Claude API a vrátí parsovaná strukturovaná JSON data analýzy."""
    prompt = build_analysis_prompt(shipment)

    # Volání Anthropic Messages API — vyžadujeme JSON-only odpověď
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extrakce surového textu a parsování JSON
    raw_response = message.content[0].text.strip()
    return json.loads(raw_response)


def get_simulated_analysis(tracking_number: str) -> dict:
    """Vrátí předpřipravenou simulaci AI analýzy (demo režim bez API klíče)."""
    # Fallback pro zásilky mimo ukázkový dataset
    fallback = {
        "standardized_status":      "In Transit",
        "delivery_risk":            "medium",
        "region":                   "Nespecifikováno",
        "gps_coordinates":          {"lat": 49.8, "lon": 15.5},
        "proactive_support_action": "Sledovat stav zásilky a aktualizovat zákazníka.",
        "marketing_trigger":        "Pre-delivery product recommendation",
    }
    return SIMULATED_AI_RESPONSES.get(tracking_number, fallback)


def analyze_shipment(shipment: dict, client=None) -> dict:
    """
    Orchestruje AI analýzu jedné zásilky.
    Při dostupném klientovi volá reálné Claude API, jinak vrátí simulovaná data.
    """
    tracking = shipment["tracking_number"]

    if client is not None:
        try:
            print(f"  🤖 Volám Claude API pro {tracking}...")
            result = analyze_shipment_via_api(client, shipment)
            print(f"  ✅ [{tracking}] → {result['standardized_status']} | Riziko: {result['delivery_risk']}")
            return result
        except Exception as e:
            # Při API chybě se plynule přepne na simulaci
            print(f"  ⚠️  API chyba pro {tracking}: {e} — přepínám na simulaci.")

    # Demo/simulovaná data — portfolio showcase bez reálného API klíče
    result = get_simulated_analysis(tracking)
    print(f"  🎭 [DEMO] [{tracking}] → {result['standardized_status']} | Riziko: {result['delivery_risk']} | Trigger: {result['marketing_trigger']}")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 4: BI STATISTIKY — agregace dat pro business intelligence dashboard ──
# ══════════════════════════════════════════════════════════════════════════════

def compute_bi_statistics(analyzed_shipments: list[dict]) -> dict:
    """Vypočítá celkové BI statistiky ze všech analyzovaných zásilek pro manažerský přehled."""
    status_counts: dict[str, int]    = {}   # Počet zásilek podle standardizovaného stavu
    region_counts: dict[str, int]    = {}   # Počet zásilek podle regionu (pro top regiony)
    carrier_hours: dict[str, list]   = {}   # Hodinové hodnoty pro průměr na dopravce
    damaged_count   = 0
    high_risk_count = 0

    for item in analyzed_shipments:
        shipment = item["shipment"]
        analysis = item["analysis"]

        # Agregace stavů
        status = analysis["standardized_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

        # Agregace regionů
        region = analysis["region"]
        region_counts[region] = region_counts.get(region, 0) + 1

        # Sběr hodin pro průměr doby doručení na dopravce
        carrier = shipment["carrier"]
        if carrier not in carrier_hours:
            carrier_hours[carrier] = []
        carrier_hours[carrier].append(shipment["hours_in_transit"])

        # Speciální čítače pro kritické stavy
        if status == "Damaged":
            damaged_count += 1
        if analysis["delivery_risk"] == "high":
            high_risk_count += 1

    # Seřazení regionů sestupně podle počtu zásilek (pro heatmapu a targeting)
    top_regions = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)

    # Výpočet průměrné doby doručení na dopravce, zaokrouhlení na 1 desetinné místo
    avg_transit_by_carrier = {
        carrier: round(sum(hours) / len(hours), 1)
        for carrier, hours in carrier_hours.items()
    }

    return {
        "total_shipments":              len(analyzed_shipments),
        "status_breakdown":             status_counts,
        "damaged_shipments":            damaged_count,
        "high_risk_shipments":          high_risk_count,
        "top_regions":                  [{"region": r, "shipment_count": c} for r, c in top_regions],
        "avg_transit_hours_by_carrier": avg_transit_by_carrier,
        "generated_at":                 datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 5: VÝSTUP — uložení výsledků do JSON a CSV ──
# ══════════════════════════════════════════════════════════════════════════════

def save_output_json(analyzed_shipments: list[dict], bi_stats: dict, filepath: str) -> None:
    """Uloží kompletní výsledky analýzy včetně BI statistik do strukturovaného JSON souboru."""
    output = {
        "project":       "AI Logistics Command Center & Marketing Predictor",
        "version":       "1.0.0",
        "author":        "Martina Dohnalová | AI Vibecoder",
        "shipments":     analyzed_shipments,
        "bi_statistics": bi_stats,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON výstup uložen: {filepath}")


def save_output_csv(analyzed_shipments: list[dict], filepath: str) -> None:
    """Uloží zjednodušený přehled zásilek do CSV pro import do tabulkových nástrojů (Excel, Sheets)."""
    fieldnames = [
        "Tracking Number", "Carrier", "Standardized Status",
        "Region", "Delivery Risk", "Support Action", "Marketing Trigger",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in analyzed_shipments:
            s = item["shipment"]
            a = item["analysis"]
            writer.writerow({
                "Tracking Number":    s["tracking_number"],
                "Carrier":            s["carrier"],
                "Standardized Status": a["standardized_status"],
                "Region":             a["region"],
                "Delivery Risk":      a["delivery_risk"],
                "Support Action":     a["proactive_support_action"],
                "Marketing Trigger":  a["marketing_trigger"],
            })
    print(f"📊 CSV výstup uložen: {filepath}")


# ══════════════════════════════════════════════════════════════════════════════
# ── KROK 6: MAIN — hlavní orchestrace celého pipeline ──
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Hlavní funkce řídí celý pipeline: vstup → AI analýza → BI statistiky → výstup."""
    start_time = time.perf_counter()

    print("=" * 68)
    print("  AI Logistics Command Center & Marketing Predictor  v1.0")
    print("  Portfolio Project #3 | Martina Dohnalová | AI Vibecoder")
    print("=" * 68)

    # 1. Zajistit existenci vstupního CSV (případně ho vytvořit)
    ensure_input_csv_exists(INPUT_CSV)

    # 2. Načíst zásilky z CSV
    shipments = load_shipments_from_csv(INPUT_CSV)

    # 3. Inicializace Anthropic klienta — klíč musí být v env proměnné ANTHROPIC_API_KEY
    api_client = None
    api_key    = os.environ.get("ANTHROPIC_API_KEY", "")

    if ANTHROPIC_AVAILABLE and api_key:
        print("🔑 Anthropic API klíč nalezen — spouštím v produkčním režimu (reálné Claude API).")
        api_client = anthropic.Anthropic(api_key=api_key)
    elif not ANTHROPIC_AVAILABLE:
        print("⚠️  Anthropic SDK není nainstalován. Spusť: pip install anthropic")
        print("🎭 Demo režim — používám simulovaná AI data pro portfolio showcase.")
    else:
        print("⚠️  API klíč nenalezen v env proměnné ANTHROPIC_API_KEY.")
        print("🎭 Demo režim — používám simulovaná AI data pro portfolio showcase.")

    print(f"\n🚀 Spouštím AI analýzu {len(shipments)} zásilek...\n")

    # 4. Analyzovat každou zásilku přes AI (nebo simulaci)
    analyzed_shipments: list[dict] = []
    for shipment in shipments:
        analysis = analyze_shipment(shipment, client=api_client)
        analyzed_shipments.append({
            "shipment": shipment,
            "analysis": analysis,
        })

    # 5. Vypočítat BI statistiky z celého batche
    print("\n📈 Počítám BI statistiky...")
    bi_stats = compute_bi_statistics(analyzed_shipments)

    # 6. Uložit výstupy (JSON + CSV)
    print("\n💾 Ukládám výstupy...")
    save_output_json(analyzed_shipments, bi_stats, OUTPUT_JSON)
    save_output_csv(analyzed_shipments, OUTPUT_CSV)

    # 7. Závěrečný manažerský BI dashboard v konzoli
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 68)
    print("  📊 BI DASHBOARD — MANAŽERSKÉ SHRNUTÍ")
    print("=" * 68)
    print(f"  Celkem zásilek:            {bi_stats['total_shipments']}")
    print(f"  Poškozených zásilek:       {bi_stats['damaged_shipments']}")
    print(f"  Zásilek s vysokým rizikem: {bi_stats['high_risk_shipments']}")

    print(f"\n  Stav zásilek:")
    for status, count in bi_stats["status_breakdown"].items():
        bar = "█" * count
        print(f"    {bar} {status:<28} {count} ks")

    print(f"\n  Top regiony (marketingový targeting):")
    for r in bi_stats["top_regions"]:
        print(f"    • {r['region']:<32} {r['shipment_count']} zásilka/zásilky")

    print(f"\n  Průměrná doba doručení podle dopravce:")
    for carrier, hours in bi_stats["avg_transit_hours_by_carrier"].items():
        print(f"    • {carrier:<22} {hours} h")

    print(f"\n  ⏱️  Celkový čas běhu pipeline: {elapsed:.3f} s")
    print("=" * 68)
    print("  ✅ Pipeline úspěšně dokončen. Vygenerované soubory:")
    print(f"     📄  {OUTPUT_JSON}   (detailní analýzy + BI statistiky)")
    print(f"     📊  {OUTPUT_CSV}    (přehled pro Excel / Google Sheets)")
    print("=" * 68)


if __name__ == "__main__":
    main()
