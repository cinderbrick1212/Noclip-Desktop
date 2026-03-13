"""Tests for Phase 1 security hardening.

Validates:
- MAX_STEPS guard in core.py
- Function allowlist in interpreter.py
- Shared JSON parsing utility
"""

import json
import os
import sys
from multiprocessing import Queue
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.parse_llm_response import parse_json_from_llm_text


class TestParseJsonFromLlmText:
    """Test the shared JSON parsing utility."""

    def test_valid_json(self):
        result = parse_json_from_llm_text('{"steps": [], "done": "ok"}')
        assert result == {"steps": [], "done": "ok"}

    def test_json_with_preamble(self):
        text = 'Here is the JSON:\n```json\n{"steps": [], "done": "ok"}\n```'
        result = parse_json_from_llm_text(text)
        assert result == {"steps": [], "done": "ok"}

    def test_empty_string(self):
        assert parse_json_from_llm_text('') == {}

    def test_no_json(self):
        assert parse_json_from_llm_text('No JSON here') == {}

    def test_malformed_json(self):
        assert parse_json_from_llm_text('{broken json}') == {}

    def test_nested_json(self):
        text = '{"steps": [{"function": "click", "parameters": {"x": 100}}], "done": null}'
        result = parse_json_from_llm_text(text)
        assert result['steps'][0]['function'] == 'click'

    def test_none_input(self):
        assert parse_json_from_llm_text(None) == {}

    def test_whitespace_only(self):
        assert parse_json_from_llm_text('   \n  ') == {}


class TestInterpreterAllowlist:
    """Test that the interpreter only executes allowed functions."""

    def test_allowed_function_executes(self):
        from interpreter import Interpreter, _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'click' in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'write' in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'press' in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'hotkey' in _ALLOWED_PYAUTOGUI_FUNCTIONS

    def test_disallowed_function_blocked(self):
        from interpreter import _ALLOWED_PYAUTOGUI_FUNCTIONS
        # These should NOT be in the allowlist
        assert 'screenshot' not in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'alert' not in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'confirm' not in _ALLOWED_PYAUTOGUI_FUNCTIONS
        assert 'prompt' not in _ALLOWED_PYAUTOGUI_FUNCTIONS

    def test_click_cell_still_works(self):
        """click_cell is handled separately, not via the allowlist."""
        from interpreter import Interpreter
        interp = Interpreter(Queue())
        interp.cell_map = {'A1': (100, 200)}
        with patch('pyautogui.click') as mock_click:
            interp.execute_function('click_cell', {'cell': 'A1'})
            mock_click.assert_called_once_with(100, 200, button='left', clicks=1)

    def test_sleep_still_works(self):
        """sleep is handled separately, not via the allowlist."""
        from interpreter import Interpreter
        interp = Interpreter(Queue())
        with patch('interpreter.sleep') as mock_sleep:
            interp.execute_function('sleep', {'secs': 0.1})
            mock_sleep.assert_called_once_with(0.1)


class TestMaxStepsGuard:
    """Test that core.py enforces MAX_STEPS."""

    def test_max_steps_constant_exists(self):
        import core
        assert hasattr(core, 'MAX_STEPS')
        assert core.MAX_STEPS > 0

    def test_execute_respects_max_steps(self):
        """execute() should return an error at MAX_STEPS."""
        from core import Core, MAX_STEPS
        with patch('core.LLM'), \
             patch('core.Screen'), \
             patch('core.Settings') as MockSettings:
            MockSettings.return_value.get_dict.return_value = {}
            c = Core()
            c.llm = MagicMock()
            result = c.execute('test request', step_num=MAX_STEPS)
            assert 'maximum step limit' in result.lower() or 'max' in result.lower()
            # LLM should NOT have been called
            c.llm.get_instructions_for_objective.assert_not_called()
