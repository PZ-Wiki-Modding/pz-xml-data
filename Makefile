.ONESHELL:
.PHONY: help generate format settings run doc

SHELL := /bin/bash

help:
	@echo "PZ Lua Parser"
	@echo "Available targets:"
	@echo "  generate: Run the generator"
	@echo "  format:   Run the formatter"
	@echo "  settings: Generate settings"
	@echo "  run:      Run the generator, formatter, and settings"
	@echo "  doc:      Generate HTML documentation from the schema"

generate:
	./.venv/bin/python ./chores/generate_output.py

format: generate
	./.venv/bin/python ./chores/format_schemas.py

settings: generate
	./.venv/bin/python ./chores/make_settings.py

run: format settings

doc:
	xsltproc xs3p.xsl schemas/animNode.xsd > schema.html