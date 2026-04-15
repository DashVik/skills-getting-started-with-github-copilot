"""Pytest configuration and fixtures for API tests"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store the initial state
    initial_state = copy.deepcopy(activities)
    
    yield
    
    # Restore to initial state after test
    activities.clear()
    activities.update(initial_state)
