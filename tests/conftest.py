import sys
import os
import pytest
from unittest.mock import AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure pytest-asyncio
pytest_asyncio_mode = "auto"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_browser_page():
    """Create a mock Playwright page for testing."""
    page = AsyncMock()
    page.mouse = AsyncMock()
    page.keyboard = AsyncMock()
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.go_back = AsyncMock()
    page.goto = AsyncMock()
    page.url = "https://example.com"
    page.wait_for_load_state = AsyncMock()
    return page


@pytest.fixture
def sample_bboxes():
    """Sample bounding boxes for testing."""
    return [
        {
            "x": 100.0,
            "y": 200.0,
            "text": "Click me",
            "type": "button",
            "ariaLabel": "Submit button",
        },
        {
            "x": 300.0,
            "y": 400.0,
            "text": "",
            "type": "input",
            "ariaLabel": "Search input",
        },
        {
            "x": 500.0,
            "y": 100.0,
            "text": "Link text",
            "type": "a",
            "ariaLabel": "",
        },
    ]


@pytest.fixture
def sample_agent_state(mock_browser_page, sample_bboxes):
    """Sample agent state for testing."""
    return {
        "page": mock_browser_page,
        "input": "Find information about Python",
        "img": "base64_encoded_image",
        "bboxes": sample_bboxes,
        "prediction": {"action": "Click", "args": ["0"]},
        "scratchpad": [],
        "observation": "",
        "bbox_descriptions": "",
    }


# Markers for test categories
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "browser: Tests requiring browser")