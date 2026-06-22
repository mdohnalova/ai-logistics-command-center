# AI Logistics Command Center

Moderní analytický a automatizační nástroj v Pythonu navržený pro monitorování, čištění a transformaci logistických dat (ETL) v reálném čase. Aplikace slouží jako dispečink pro správu přepravních anomálií a pomáhá managementu bleskově reagovat na provozní změny.

## Technologický Stack
* **Language:** Python 3.x
* **Framework:** Streamlit Cloud (Interactive Web UI)
* **Data Processing:** Pandas (CSV & JSON parsování, filtrace, datové transformace)
* **Version Control:** Git & GitHub

##  Hlavní Funkcionality
* **Automatizované čištění dat (ETL):** Skript `clean.py` detekuje anomálie na vstupu, opravuje nekonzistentní formáty a připravuje čistá data pro dashboard.
* **Interactive Dashboard (`logistics_app.py`):** Přehledné webové rozhraní zobrazující klíčové logistické metriky, stav zásilek v reálném čase a varovné signály při zpoždění.
* **Exporty:** Možnost stahování očištěných reportů ve formátech `.csv` a `.json` pro další firemní systémy.

## Jak aplikaci spustit lokálně
1. Naklonujte repozitář: `git clone https://github.com/mdohnnalova/ai-logistics-command-center.git`
2. Nainstalujte závislosti: `pip install -r requirements.txt`
3. Spusťte Streamlit: `streamlit run logistics_app.py`
