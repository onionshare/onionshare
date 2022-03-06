#!/bin/bash
pytest -v tests/test_gui_tabs.py && \
pytest -v tests/test_gui_share.py && \
pytest -v tests/test_gui_receive.py && \
pytest -v tests/test_gui_website.py && \
pytest -v tests/test_gui_chat.py
