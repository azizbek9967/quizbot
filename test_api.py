import uuid
from fastapi.testclient import TestClient
from main import app
from db import engine
from models import Base

client = TestClient(app)


def test_health_and_random():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    response = client.get("/questions/random")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "text" in data
    assert len(data["choices"]) == 4


def test_create_category_and_question():
    cat_name = f"Test Category {uuid.uuid4().hex[:6]}"
    # Create category
    cat_response = client.post("/categories", json={"name": cat_name, "emoji": "🧪"})
    assert cat_response.status_code == 200
    cat_data = cat_response.json()
    cat_id = cat_data["id"]

    # Create question by category_id
    q_response = client.post(
        "/questions",
        json={
            "category_id": cat_id,
            "text": "What is 2 + 2?",
            "choices": ["3", "4", "5", "6"],
            "correct_index": 1,
            "difficulty": "easy",
        },
    )
    assert q_response.status_code == 200
    q_data = q_response.json()
    assert q_data["text"] == "What is 2 + 2?"
    assert q_data["correct_index"] == 1

    # Create question by category_name
    q2_response = client.post(
        "/questions",
        json={
            "category_name": cat_name,
            "text": "What is the capital of testing?",
            "choices": ["Alpha", "Beta", "Gamma", "Delta"],
            "correct_index": 0,
            "difficulty": "medium",
        },
    )
    assert q2_response.status_code == 200
    assert q2_response.json()["category_id"] == cat_id
    print("All tests passed successfully!")


if __name__ == "__main__":
    test_health_and_random()
    test_create_category_and_question()
