def _make_department(client, name="Engineering"):
    r = client.post("/api/departments", json={"name": name}, headers=_admin_auth(client))
    assert r.status_code == 200, r.text
    return r.json()


def _admin_auth(client):
    # Bootstrap: create an admin employee directly then log in.
    r = client.post("/api/employees", json={
        "name": "Admin User", "email": "admin@example.com", "role": "admin",
        "hourly_cost": 0, "password": "adminpass123",
    })
    assert r.status_code == 200, r.text
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "adminpass123"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_employee_creation_and_duplicate_rejected(client):
    r = client.post("/api/employees", json={
        "name": "Jane Doe", "email": "jane@example.com", "role": "employee",
        "hourly_cost": 500, "password": "pass1234",
    })
    assert r.status_code == 200
    dup = client.post("/api/employees", json={
        "name": "Jane Doe 2", "email": "jane@example.com", "role": "employee",
        "hourly_cost": 500, "password": "pass1234",
    })
    assert dup.status_code == 422


def test_department_requires_admin(client):
    # Non-admin (employee) cannot create a department.
    client.post("/api/employees", json={
        "name": "Bob", "email": "bob@example.com", "role": "employee",
        "hourly_cost": 100, "password": "pass1234",
    })
    login = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "pass1234"})
    token = login.json()["access_token"]
    r = client.post("/api/departments", json={"name": "Sales"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_login_invalid_credentials(client):
    client.post("/api/employees", json={
        "name": "Sam", "email": "sam@example.com", "role": "employee",
        "hourly_cost": 100, "password": "correctpass",
    })
    r = client.post("/api/auth/login", json={"email": "sam@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_full_task_lifecycle_with_ai_cost(client):
    emp = client.post("/api/employees", json={
        "name": "Dev One", "email": "dev1@example.com", "role": "employee",
        "hourly_cost": 500, "password": "pass1234",
    }).json()

    start = client.post("/api/tasks/start", json={
        "employee_id": emp["id"], "title": "Add validation endpoint",
        "baseline_minutes": 60,
    })
    assert start.status_code == 200
    task = start.json()
    assert task["status"] == "in_progress"

    ai_event = client.post(f"/api/tasks/{task['id']}/ai-events", json={
        "employee_id": emp["id"], "provider": "openai", "model": "gpt-5",
        "input_tokens": 1_000_000, "output_tokens": 500_000, "source": "observed",
    })
    assert ai_event.status_code == 200
    assert ai_event.json()["cost"] is not None  # priced provider + observed source

    outcome = client.post(f"/api/tasks/{task['id']}/outcome", json={
        "files_changed": 2, "lines_added": 40, "lines_removed": 5, "commits": 1,
        "tests_run": 4, "tests_passed": 4, "build_passed": True, "output_generated": True,
    })
    assert outcome.status_code == 200

    complete = client.post(f"/api/tasks/{task['id']}/complete", json={"notes": "done"})
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    assert complete.json()["actual_minutes"] is not None

    roi = client.get(f"/api/tasks/{task['id']}/roi")
    assert roi.status_code == 200
    body = roi.json()
    assert body["calculation_status"] == "calculated"
    assert body["estimated_labor_value"] is not None
    assert body["ai_cost"] is not None
    assert body["roi_percentage"] is not None


def test_task_roi_without_ai_cost_is_partial(client):
    emp = client.post("/api/employees", json={
        "name": "Dev Two", "email": "dev2@example.com", "role": "employee",
        "hourly_cost": 500, "password": "pass1234",
    }).json()
    task = client.post("/api/tasks/start", json={
        "employee_id": emp["id"], "title": "Refactor function", "baseline_minutes": 30,
    }).json()
    client.post(f"/api/tasks/{task['id']}/complete", json={})
    roi = client.get(f"/api/tasks/{task['id']}/roi").json()
    assert roi["calculation_status"] == "partial"
    assert roi["ai_cost"] is None
    assert roi["roi_percentage"] is None


def test_antigravity_connector_reports_unavailable(client):
    r = client.get("/api/connectors")
    assert r.status_code == 200
    entries = {c["name"]: c for c in r.json()}
    assert entries["antigravity"]["available"] is False
    assert "internal" in entries["antigravity"]["reason"].lower() or "external" in entries["antigravity"]["reason"].lower()


def test_task_not_found_404(client):
    r = client.get("/api/tasks/does-not-exist")
    assert r.status_code == 404


def test_double_complete_is_400(client):
    emp = client.post("/api/employees", json={
        "name": "Dev Three", "email": "dev3@example.com", "role": "employee",
        "hourly_cost": 100, "password": "pass1234",
    }).json()
    task = client.post("/api/tasks/start", json={"employee_id": emp["id"], "title": "T"}).json()
    client.post(f"/api/tasks/{task['id']}/complete", json={})
    second = client.post(f"/api/tasks/{task['id']}/complete", json={})
    assert second.status_code == 400


def test_negative_baseline_rejected(client):
    emp = client.post("/api/employees", json={
        "name": "Dev Four", "email": "dev4@example.com", "role": "employee",
        "hourly_cost": 100, "password": "pass1234",
    }).json()
    r = client.post("/api/tasks/start", json={
        "employee_id": emp["id"], "title": "Bad baseline", "baseline_minutes": -10,
    })
    assert r.status_code == 400


def test_management_dashboard_shape(client):
    r = client.get("/api/dashboard/management")
    assert r.status_code == 200
    body = r.json()
    for key in ["ai_spend", "ai_assisted_tasks", "time_saved_minutes", "estimated_business_value",
                "department_stats", "provider_stats"]:
        assert key in body


def test_prompt_analyze_flags_missing_elements(client):
    r = client.post("/api/prompt/analyze", json={"prompt": "Build an API for users."})
    assert r.status_code == 200
    body = r.json()
    assert "technology/framework" in body["missing"]
    assert "testing requirements" in body["missing"]
    assert len(body["suggestions"]) > 0
    assert "improved_prompt" in body


def test_prompt_analyze_well_specified_prompt_has_fewer_gaps(client):
    good = (
        "Build a REST API for user management using FastAPI and PostgreSQL. "
        "Implement create, read, update, delete. Return proper status codes. "
        "Handle invalid input and validation errors. Include unit tests."
    )
    r = client.post("/api/prompt/analyze", json={"prompt": good})
    body = r.json()
    assert "technology/framework" not in body["missing"]
    assert "testing requirements" not in body["missing"]
