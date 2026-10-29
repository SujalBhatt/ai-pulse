from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def level_for(avg):
    if avg is None:
        return "Not assessed"
    if avg < 1.5:
        return "Beginner"
    if avg < 2.5:
        return "Exploring"
    if avg < 3.5:
        return "Practitioner"
    return "Leader"


@router.get("")
def org_dashboard(org_id: int, m: models.Membership = Depends(current_membership), db: Session = Depends(get_db)):
    if m.role != "admin":
        raise HTTPException(403, "Admins only")
    if m.org_id != org_id:
        raise HTTPException(403, "Organization does not match selected organization")

    org = db.get(models.Organization, org_id)
    if not org:
        raise HTTPException(404, "Organization not found")

    members = db.query(models.Membership).filter_by(org_id=org_id).all()
    departments = []
    all_flags = {}
    for dept in org.departments:
        dept_members = [x for x in members if x.department_id == dept.id]
        responded = 0
        member_averages = []
        department_flags = {}
        for dm in dept_members:
            rows = db.query(models.Response).filter_by(membership_id=dm.id).all()
            if rows:
                responded += 1
                scores = [r.score for r in rows if r.score is not None]
                if scores:
                    member_averages.append(sum(scores) / len(scores))
        if responded < 5:
            departments.append({
                "department": dept.name,
                "responded": responded,
                "average_score": None,
                "level": "Hidden",
                "redacted": True,
            })
            continue

        for dm in dept_members:
            rows = db.query(models.Response).filter_by(membership_id=dm.id).all()
            for r in rows:
                for f in r.flags or []:
                    department_flags[f] = department_flags.get(f, 0) + 1
        avg = sum(member_averages) / len(member_averages) if member_averages else None
        for flag, count in department_flags.items():
            all_flags[flag] = all_flags.get(flag, 0) + count
        departments.append({
            "department": dept.name,
            "employees": len(dept_members),
            "responded": responded,
            "average_score": round(avg, 2) if avg is not None else None,
            "level": level_for(avg),
            "redacted": False,
        })

    return {
        "organization": org.name,
        "departments": departments,
        "top_risks": sorted(all_flags.items(), key=lambda kv: -kv[1])[:5],
    }
