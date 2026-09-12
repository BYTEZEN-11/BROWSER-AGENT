import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import base64
from io import BytesIO
from PIL import Image

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    AgentConfig,
    load_config,
    parse,
    format_descriptions,
    update_scratchpad,
    BBox,
    Prediction,
    AgentState,
)


class TestAgentConfig:
    def test_default_config(self):
        config = AgentConfig()
        assert config.model == "gpt-4-turbo"
        assert config.max_tokens == 4096
        assert config.temperature == 0.1
        assert config.max_steps == 150
        assert config.start_url == "https://www.google.com"
        assert config.headless is False

    def test_custom_config(self):
        config = AgentConfig(
            model="gpt-3.5-turbo",
            max_tokens=2048,
            temperature=0.5,
            max_steps=100,
            headless=True,
        )
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.max_steps == 100
        assert config.headless is True


class TestParseFunction:
    def test_parse_valid_action_with_args(self):
        text = "Some reasoning\nAction: Click [1]"
        result = parse(text)
        assert result["action"] == "Click"
        assert result["args"] == ["1"]

    def test_parse_valid_action_without_args(self):
        text = "Some reasoning\nAction: Wait"
        result = parse(text)
        assert result["action"] == "Wait"
        assert result["args"] is None

    def test_parse_answer_action(self):
        text = "Reasoning\nAction: ANSWER [Found the answer]"
        result = parse(text)
        assert result["action"] == "ANSWER"
        assert result["args"] == ["Found the answer"]

    def test_parse_invalid_format(self):
        text = "No action prefix here"
        result = parse(text)
        assert result["action"] == "retry"
        assert "Could not parse LLM Output" in result["args"]

    def test_parse_multiple_args(self):
        text = "Reasoning\nAction: Type [1; hello world]"
        result = parse(text)
        assert result["action"] == "Type"
        assert result["args"] == ["1", "hello world"]

    def test_parse_scroll_action(self):
        text = "Reasoning\nAction: Scroll [WINDOW; down]"
        result = parse(text)
        assert result["action"] == "Scroll"
        assert result["args"] == ["WINDOW", "down"]


class TestFormatDescriptions:
    def test_format_descriptions_basic(self):
        state = {
            "bboxes": [
                {"x": 100, "y": 200, "text": "Click me", "type": "button", "ariaLabel": ""},
                {"x": 300, "y": 400, "text": "", "type": "input", "ariaLabel": "Search"},
            ]
        }
        result = format_descriptions(state)
        assert "bbox_descriptions" in result
        assert "0 (<button/>): \"Click me\"" in result["bbox_descriptions"]
        assert '1 (<input/>): "Search"' in result["bbox_descriptions"]

    def test_format_descriptions_empty(self):
        state = {"bboxes": []}
        result = format_descriptions(state)
        assert result["bbox_descriptions"] == "\nValid Bounding Boxes:\n"


class TestUpdateScratchpad:
    def test_update_scratchpad_first_step(self):
        state = {"observation": "Clicked button 1", "scratchpad": []}
        result = update_scratchpad(state)
        assert len(result["scratchpad"]) == 1
        assert "1. Clicked button 1" in result["scratchpad"][0].content

    def test_update_scratchpad_subsequent_steps(self):
        state = {
            "observation": "Typed in search",
            "scratchpad": [Mock(content="Previous action observations:\n1. Clicked button 1")],
        }
        result = update_scratchpad(state)
        assert "2. Typed in search" in result["scratchpad"][0].content


class TestBBoxTypedDict:
    def test_bbox_structure(self):
        bbox: BBox = {
            "x": 100.0,
            "y": 200.0,
            "text": "Test",
            "type": "button",
            "ariaLabel": "Test button",
        }
        assert bbox["x"] == 100.0
        assert bbox["type"] == "button"


class TestPredictionTypedDict:
    def test_prediction_structure(self):
        pred: Prediction = {
            "action": "Click",
            "args": ["1"],
        }
        assert pred["action"] == "Click"
        assert pred["args"] == ["1"]

    def test_prediction_without_args(self):
        pred: Prediction = {
            "action": "Wait",
            "args": None,
        }
        assert pred["action"] == "Wait"
        assert pred["args"] is None


# Fixtures for async tests
@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.mouse = AsyncMock()
    page.keyboard = AsyncMock()
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot")
    page.go_back = AsyncMock()
    page.goto = AsyncMock()
    page.url = "https://example.com"
    return page


@pytest.fixture
def sample_state(mock_page):
    return {
        "page": mock_page,
        "input": "Test task",
        "img": base64.b64encode(b"fake").decode(),
        "bboxes": [
            {"x": 100, "y": 200, "text": "Button", "type": "button", "ariaLabel": ""},
            {"x": 300, "y": 400, "text": "Input", "type": "input", "ariaLabel": "Search"},
        ],
        "prediction": {"action": "Click", "args": ["0"]},
        "scratchpad": [],
        "observation": "",
        "bbox_descriptions": "",
    }


# Tool tests would require more complex mocking
# These are placeholder tests for the tool functions


class TestConfigLoading:
    def test_load_config_default(self, tmp_path):
        # Test that default config is returned when no file exists
        with patch("main.CONFIG_PATH", tmp_path / "nonexistent.yaml"):
            config = load_config()
            assert isinstance(config, AgentConfig)
            assert config.model == "gpt-4-turbo"

    def test_load_config_from_file(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("model: gpt-3.5-turbo\nmax_steps: 100\n")
        with patch("main.CONFIG_PATH", config_file):
            config = load_config()
            assert config.model == "gpt-3.5-turbo"
            assert config.max_steps == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])