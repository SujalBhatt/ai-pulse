from tests.conftest import login


def test_login_lists_organizations(client):
    _, data = login(client, "ravi@consult.test")
    names = {o["org_name"] for o in data["organizations"]}
    assert names == {"Northwind Logistics", "Bluepeak Retail"}


def test_employee_sees_questions(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/diagnostic/questions", headers=headers)
    assert r.status_code == 200
    assert any(q["id"] == "sup-drafts" for q in r.json())


def test_admin_dashboard(client):
    headers, data = login(client, "asha@northwind.test", "Northwind Logistics")
    org_id = data["organizations"][0]["org_id"]
    r = client.get(f"/dashboard?org_id={org_id}", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["departments"]) == 4


def test_admin_cannot_see_other_org(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    r = client.get("/dashboard?org_id=2", headers=headers)
    assert r.status_code == 403


def test_user_cannot_select_unowned_org(client):
    headers, _ = login(client, "asha@northwind.test")
    r = client.post("/auth/select-org", json={"org_id": 2}, headers=headers)
    assert r.status_code == 403


def test_employee_cannot_access_dashboard(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/dashboard?org_id=1", headers=headers)
    assert r.status_code == 403


def test_small_departments_are_redacted(client):
    headers, data = login(client, "asha@northwind.test", "Northwind Logistics")
    org_id = data["organizations"][0]["org_id"]
    response = client.get(f"/dashboard?org_id={org_id}", headers=headers)
    assert response.status_code == 200
    departments = response.json()["departments"]
    assert all(department["redacted"] for department in departments)
    assert all(department["average_score"] is None for department in departments)
    assert response.json()["top_risks"] == []


def test_employee_can_delete_own_diagnostic_data(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")

    before = client.get("/reports/me", headers=headers).json()
    assert before["answered"] > 0

    deleted = client.delete("/reports/me", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == before["answered"]

    after = client.get("/reports/me", headers=headers)
    assert after.status_code == 200
    assert after.json()["answered"] == 0
    assert after.json()["average_score"] is None
    assert after.json()["action_plan"] == []

    repeated = client.delete("/reports/me", headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["deleted"] == 0


def test_report_includes_personalized_action_plan(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    report = client.get("/reports/me", headers=headers).json()
    assert report["action_plan"] == [{
        "priority": "Protect customer data",
        "action": "Remove customer identifiers before using an AI tool.",
        "reason": "Your diagnostic included a customer data shared risk.",
    }]
