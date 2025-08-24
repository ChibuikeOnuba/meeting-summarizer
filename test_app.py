#!/usr/bin/env python3
"""
Simple test script for the Meeting Summarizer API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running.")
        return False

def test_summarize_meeting():
    """Test meeting summarization"""
    print("\n📝 Testing meeting summarization...")
    
    meeting_text = """
    Today we had our weekly team meeting. We discussed the Q3 budget and upcoming projects.
    John will prepare the financial report by Friday and send it to the management team.
    Mary needs to schedule a follow-up call with the client next week.
    Alice will review the project timeline and update the documentation.
    We also talked about the new office policy - everyone should submit their time sheets by Monday.
    The meeting was productive and everyone seemed positive about the upcoming quarter.
    """
    
    data = {
        "meeting_text": meeting_text,
        "meeting_title": "Weekly Team Meeting - Q3 Planning",
        "participants": "John,Mary,Alice,Manager"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/summarize", data=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Meeting summarization successful")
            print(f"   Meeting ID: {result['id']}")
            print(f"   Summary: {result['summary']}")
            print(f"   Sentiment: {result['sentiment']}")
            print(f"   Action Items: {len(result['action_items'])}")
            
            for i, action in enumerate(result['action_items'], 1):
                print(f"     {i}. {action['task']} (assigned to: {action['assigned_to']})")
            
            return result['id']
        else:
            print(f"❌ Meeting summarization failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during summarization: {e}")
        return None

def test_get_actions(meeting_id):
    """Test getting action items"""
    print(f"\n📋 Testing action items retrieval for meeting {meeting_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/actions?meeting_id={meeting_id}")
        if response.status_code == 200:
            actions = response.json()
            print(f"✅ Retrieved {len(actions)} action items")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. {action['task']} - {action['assigned_to']} (Priority: {action['priority']})")
            return True
        else:
            print(f"❌ Failed to get action items: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting action items: {e}")
        return False

def test_get_meetings():
    """Test getting meetings list"""
    print("\n📊 Testing meetings retrieval...")
    
    try:
        response = requests.get(f"{BASE_URL}/meetings?limit=5")
        if response.status_code == 200:
            meetings = response.json()
            print(f"✅ Retrieved {len(meetings)} meetings")
            for meeting in meetings:
                print(f"   - {meeting['title']} (ID: {meeting['id']})")
            return True
        else:
            print(f"❌ Failed to get meetings: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting meetings: {e}")
        return False

def test_get_meeting_details(meeting_id):
    """Test getting specific meeting details"""
    print(f"\n🔍 Testing meeting details for meeting {meeting_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/meetings/{meeting_id}")
        if response.status_code == 200:
            meeting = response.json()
            print("✅ Meeting details retrieved successfully")
            print(f"   Title: {meeting['title']}")
            print(f"   Participants: {', '.join(meeting['participants'])}")
            print(f"   Summary: {meeting['summary']}")
            return True
        else:
            print(f"❌ Failed to get meeting details: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting meeting details: {e}")
        return False

def test_sentiment_analysis(meeting_id):
    """Test sentiment analysis"""
    print(f"\n😊 Testing sentiment analysis for meeting {meeting_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/tone/{meeting_id}")
        if response.status_code == 200:
            sentiment = response.json()
            print("✅ Sentiment analysis successful")
            print(f"   Sentiment: {sentiment['sentiment']}")
            print(f"   Meeting: {sentiment['title']}")
            return True
        else:
            print(f"❌ Failed to get sentiment: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting sentiment: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Meeting Summarizer API Tests")
    print("=" * 50)
    
    # Wait a moment for the server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Health check
    if test_health_check():
        tests_passed += 1
    
    # Test 2: Summarize meeting
    meeting_id = test_summarize_meeting()
    if meeting_id:
        tests_passed += 1
        
        # Test 3: Get action items
        if test_get_actions(meeting_id):
            tests_passed += 1
        
        # Test 4: Get meeting details
        if test_get_meeting_details(meeting_id):
            tests_passed += 1
        
        # Test 5: Sentiment analysis
        if test_sentiment_analysis(meeting_id):
            tests_passed += 1
    
    # Test 6: Get meetings list
    if test_get_meetings():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server logs for more details.")
    
    print("\n🌐 API Documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
