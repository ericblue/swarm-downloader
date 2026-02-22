.PHONY: help download export csv search stats venues timeline categories restaurants recent clean env-check

# Load .env file if it exists
ifneq (,$(wildcard .env))
  include .env
  export
endif

PYTHON := python3
DATA_DIR := data
JSON_FILE := $(DATA_DIR)/all_checkins.json
CSV_FILE := $(DATA_DIR)/checkins.csv

help: ## Show this help
	@echo ""
	@echo "Swarm Download - Foursquare/Swarm Checkin Exporter"
	@echo "=================================================="
	@echo ""
	@echo "Setup:"
	@echo "  make env          Create .env file from template"
	@echo "  make download     Download all checkins from Foursquare API"
	@echo ""
	@echo "Export:"
	@echo "  make csv          Export checkins to CSV"
	@echo "  make export       Alias for csv"
	@echo ""
	@echo "Explore:"
	@echo "  make search       Interactive search mode"
	@echo "  make stats        Overall stats dashboard"
	@echo "  make stats-year Y=2023    Stats for a specific year"
	@echo "  make venues       Top venues ranking"
	@echo "  make timeline     Monthly timeline chart"
	@echo "  make categories   Category breakdown"
	@echo ""
	@echo "Dining (combine Y= and T= freely):"
	@echo "  make restaurants                         All dining breakdown"
	@echo "  make restaurants Y=2023                  Dining for a year"
	@echo "  make restaurants T=restaurants            Sit-down restaurants only"
	@echo "  make restaurants Y=2023 T=restaurants     Sit-down restaurants for a year"
	@echo "  make recent                              Last 20 dining visits"
	@echo "  make recent T=restaurants                Last 20 sit-down restaurants"
	@echo "  make recent Y=2024 T=coffee              Coffee shops in 2024"
	@echo "  make recent-range A=2024-01-01 B=2024-06-30"
	@echo ""
	@echo "  T= types: restaurants, fast-food, coffee, bars, bakery, brewery"
	@echo ""
	@echo "Queries (examples):"
	@echo "  make find Q=starbucks              Search by venue name"
	@echo "  make find-cat Q=sushi              Search by category"
	@echo "  make find-city Q='san francisco'   Search by city"
	@echo "  make find-year Y=2019              All checkins for a year"
	@echo ""
	@echo "Maintenance:"
	@echo "  make info         Show data file stats"
	@echo "  make clean        Remove downloaded data"
	@echo ""

# ── Setup ────────────────────────────────────────────────────────────────────

env: ## Create .env file from template
	@if [ -f .env ]; then \
		echo ".env already exists. Edit it directly to update your token."; \
	else \
		cp .env.example .env; \
		echo "Created .env from .env.example — paste your OAuth token in the file."; \
	fi

env-check:
	@if [ -z "$(OAUTH_TOKEN)" ]; then \
		echo "Error: OAUTH_TOKEN not set. Run 'make env' and add your token to .env"; \
		exit 1; \
	fi

# ── Download ─────────────────────────────────────────────────────────────────

download: env-check ## Download all checkins from Foursquare API
	$(PYTHON) download_checkins.py

# ── Export ───────────────────────────────────────────────────────────────────

csv: $(JSON_FILE) ## Export checkins to CSV
	$(PYTHON) export_csv.py

export: csv ## Alias for csv

csv-year: $(JSON_FILE) ## Export a single year to CSV (usage: make csv-year Y=2023)
	$(PYTHON) export_csv.py --year $(Y) -o $(DATA_DIR)/checkins_$(Y).csv

csv-city: $(JSON_FILE) ## Export a single city to CSV (usage: make csv-city C="los angeles")
	$(PYTHON) export_csv.py --city "$(C)" -o $(DATA_DIR)/checkins_city.csv

# ── Explore ──────────────────────────────────────────────────────────────────

search: $(JSON_FILE) ## Launch interactive search mode
	$(PYTHON) search_checkins.py

stats: $(JSON_FILE) ## Show overall stats dashboard
	$(PYTHON) search_checkins.py stats

stats-year: $(JSON_FILE) ## Stats for a specific year (usage: make stats-year Y=2023)
	$(PYTHON) search_checkins.py stats --year $(Y)

venues: $(JSON_FILE) ## Top venues ranking
	$(PYTHON) search_checkins.py venues

timeline: $(JSON_FILE) ## Monthly timeline chart
	$(PYTHON) search_checkins.py timeline

categories: $(JSON_FILE) ## Category breakdown
	$(PYTHON) search_checkins.py categories

# ── Dining ───────────────────────────────────────────────────────────────────
# T= dining type filter: restaurants, fast-food, coffee, bars, bakery, brewery

restaurants: $(JSON_FILE) ## Dining breakdown (usage: make restaurants [Y=2023] [T=restaurants] [L=30])
	$(PYTHON) search_checkins.py restaurants $(if $(Y),--year $(Y)) $(if $(T),--type $(T)) $(if $(L),--limit $(L))

recent: $(JSON_FILE) ## Recent dining visits (usage: make recent [Y=2024] [T=restaurants] [L=50])
	$(PYTHON) search_checkins.py recent $(if $(Y),--year $(Y)) $(if $(T),--type $(T)) $(if $(L),--limit $(L))

recent-range: $(JSON_FILE) ## Dining in date range (usage: make recent-range A=2024-01-01 B=2024-06-30 [T=restaurants] [L=100])
	$(PYTHON) search_checkins.py recent --after $(A) --before $(B) $(if $(T),--type $(T)) $(if $(L),--limit $(L),--limit 50)

# ── Quick queries ────────────────────────────────────────────────────────────

find: $(JSON_FILE) ## Search by venue name (usage: make find Q=starbucks [L=50])
	$(PYTHON) search_checkins.py search --venue "$(Q)" $(if $(L),--limit $(L),--limit 50)

find-cat: $(JSON_FILE) ## Search by category (usage: make find-cat Q=sushi [L=50])
	$(PYTHON) search_checkins.py search --category "$(Q)" $(if $(L),--limit $(L),--limit 50)

find-city: $(JSON_FILE) ## Search by city (usage: make find-city Q="san francisco" [L=50])
	$(PYTHON) search_checkins.py search --city "$(Q)" $(if $(L),--limit $(L),--limit 50)

find-year: $(JSON_FILE) ## All checkins for a year (usage: make find-year Y=2019 [L=100])
	$(PYTHON) search_checkins.py search --year $(Y) $(if $(L),--limit $(L),--limit 100)

# ── Info / Maintenance ───────────────────────────────────────────────────────

info: ## Show data file stats
	@echo ""
	@if [ -f $(JSON_FILE) ]; then \
		echo "JSON: $(JSON_FILE)"; \
		echo "  Size: $$(du -h $(JSON_FILE) | cut -f1)"; \
		echo "  Checkins: $$($(PYTHON) -c "import json; d=json.load(open('$(JSON_FILE)')); print(d.get('total_checkins', len(d.get('checkins',[]))))")"; \
		echo "  Downloaded: $$($(PYTHON) -c "import json; print(json.load(open('$(JSON_FILE)')).get('downloaded_at','unknown'))")"; \
	else \
		echo "No data downloaded yet. Run 'make download' first."; \
	fi
	@if [ -f $(CSV_FILE) ]; then \
		echo ""; \
		echo "CSV:  $(CSV_FILE)"; \
		echo "  Size: $$(du -h $(CSV_FILE) | cut -f1)"; \
		echo "  Rows: $$(tail -n +2 $(CSV_FILE) | wc -l | tr -d ' ')"; \
	fi
	@echo ""

clean: ## Remove downloaded data
	@echo "This will delete all files in $(DATA_DIR)/."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && rm -rf $(DATA_DIR) && echo "Cleaned." || echo "Cancelled."
