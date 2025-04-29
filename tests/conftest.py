from pathlib import Path

import pytest


@pytest.fixture
def sample_html():
    fixture_path = Path(__file__).parent / "fixtures/sample_orders_page.html"
    assert fixture_path.exists(), f"Fixture file {fixture_path} does not exist"
    return fixture_path
