.PHONY: help download export csv search stats venues timeline categories clean env-check

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

# ── Quick queries ────────────────────────────────────────────────────────────

find: $(JSON_FILE) ## Search by venue name (usage: make find Q=starbucks)
	$(PYTHON) search_checkins.py search --venue "$(Q)" --limit 50

find-cat: $(JSON_FILE) ## Search by category (usage: make find-cat Q=sushi)
	$(PYTHON) search_checkins.py search --category "$(Q)" --limit 50

find-city: $(JSON_FILE) ## Search by city (usage: make find-city Q="san francisco")
	$(PYTHON) search_checkins.py search --city "$(Q)" --limit 50

find-year: $(JSON_FILE) ## All checkins for a year (usage: make find-year Y=2019)
	$(PYTHON) search_checkins.py search --year $(Y) --limit 100

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
