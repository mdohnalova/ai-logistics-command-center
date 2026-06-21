#!/usr/bin/env python3
"""
clean.py — Úklid a přejmenování souborů před deploymentem.
Spuštění: python clean.py
"""

import os
import shutil
from pathlib import Path

# Pracovní složka = složka, kde leží tento skript
BASE = Path(__file__).parent

# Barvy pro terminálový výstup
OK  = "\033[92m✅"
ERR = "\033[91m❌"
SKP = "\033[93m⏭️"
INF = "\033[94mℹ️"
RST = "\033[0m"


def log(icon: str, msg: str) -> None:
    print(f"  {icon}  {msg}{RST}")


def rename_file(src_name: str, dst_name: str) -> None:
    """Přejmenuje soubor src → dst. Přeskočí, pokud src neexistuje."""
    src = BASE / src_name
    dst = BASE / dst_name

    if not src.exists():
        log(SKP, f"{src_name}  →  přeskočeno (soubor nenalezen)")
        return

    if dst.exists():
        log(ERR, f"{dst_name}  →  CHYBA: cíl už existuje, přejmenování přerušeno!")
        log(INF, f"   Zkontroluj ručně: {dst}")
        return

    src.rename(dst)
    log(OK, f"{src_name}  →  {dst_name}")


def backup_file(src_name: str) -> None:
    """Přesune soubor do záložní podsložky _backup/ místo smazání."""
    src = BASE / src_name

    if not src.exists():
        log(SKP, f"{src_name}  →  přeskočeno (soubor nenalezen)")
        return

    backup_dir = BASE / "_backup"
    backup_dir.mkdir(exist_ok=True)

    dst = backup_dir / src_name
    shutil.move(str(src), str(dst))
    log(OK, f"{src_name}  →  přesunuto do zálohy _backup/{src_name}")


# ── Hlavní blok ──────────────────────────────────────────────────────────────

print()
print("  📦  AI Logistics — čistění před deploymentem")
print("  " + "─" * 52)

# 1–4: Přejmenování souborů
rename_file("logistics_command_center_2.py", "logistics_app.py")
rename_file("shipments_input_2.csv",          "shipments_input.csv")
rename_file("logistics_output_2.json",        "logistics_output.json")
rename_file("logistics_output_2.csv",         "logistics_output.csv")

print()

# 5: Záloha duplicitního Streamlit souboru
backup_file("logistics_app_2.py")

print()
print("  " + "─" * 52)
print("  ✨  Hotovo! Zkontroluj výpis výše a spusť aplikaci:")
print()
print("      streamlit run logistics_app.py")
print()
