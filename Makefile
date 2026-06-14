.ONESHELL:
.PHONY: help format

SHELL := /bin/bash

help:
	@echo "PZ Lua Parser"
	@echo "Available targets:"
	@echo "  format:   Run the formatter"

format:
	./.venv/bin/python ./chores/format_schemas.py
