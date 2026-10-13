from fastapi import APIRouter

router = APIRouter()

CATEGORY_NAMES = {
    "investment_platform": "Fake investment platform",
    "pyramid": "Financial pyramid",
    "betting": "Illegal betting promotion",
    "giveaway": "Fake giveaway",
    "job_offer": "Fake job offer",
    "none": "No fraud detected",
}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/categories")
def categories():
    result = []
    for category_id in CATEGORY_NAMES:
        result.append({"id": category_id, "label": CATEGORY_NAMES[category_id]})
    return result
