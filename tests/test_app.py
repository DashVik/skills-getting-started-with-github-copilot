"""Unit tests for the Mergington High School API endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_list(self, client, reset_activities):
        """Test that GET /activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that all 9 activities are returned"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Tennis Club", "Drama Club",
            "Art Studio", "Debate Team", "Science Club"
        }
        assert set(data.keys()) == expected_activities
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in data.items():
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity {activity_name} missing required fields"
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_activities_have_participants(self, client, reset_activities):
        """Test that activities have participant lists initialized"""
        response = client.get("/activities")
        data = response.json()
        
        # At least some activities should have participants
        has_participants = any(
            len(activity["participants"]) > 0 
            for activity in data.values()
        )
        assert has_participants, "At least one activity should have participants"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_with_valid_activity_and_email(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Sign up for an activity
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_signup_with_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signup fails with 404 if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant_returns_400(self, client, reset_activities):
        """Test that signing up twice for same activity returns 400"""
        email = "michael@mergington.edu"
        
        # Try to sign up again (michael is already in Chess Club)
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Drama Club"]
        
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        data = response.json()
        for activity_name in activities_to_join:
            assert email in data[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister successfully removes a participant"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Verify they're in the activity
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify they're no longer in the activity
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_with_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregister fails with 404 if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_participant_returns_400(self, client, reset_activities):
        """Test that unregister fails with 400 if student not signed up"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_signup_then_unregister_cycle(self, client, reset_activities):
        """Test the complete cycle of sign up and unregister"""
        email = "cycling@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
