.ONESHELL:
.PHONY: help generate format settings run doc

SHELL := /bin/bash

help:
	@echo "PZ Lua Parser"
	@echo "Available targets:"
	@echo "  format:   Run the formatter"

generate:
	./.venv/bin/python ./chores/generate_output.py

format: generate
	./.venv/bin/python ./chores/format_schemas.py

settings: generate
	./.venv/bin/python ./chores/make_settings.py

run: format settings

doc:
	xsltproc xs3p.xsl schemas/animNode.xsd > schema.html