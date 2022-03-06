#!/bin/bash
pytest -v tests/test_gui_tabs.py && sleep 5 && \
pytest -v tests/test_gui_share.py && sleep 5 && \
pytest -v tests/test_gui_receive.py && sleep 5 && \
pytest -v tests/test_gui_website.py && sleep 5 && \
pytest -v tests/test_gui_chat.py
