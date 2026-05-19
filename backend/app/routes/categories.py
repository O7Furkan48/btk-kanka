from fastapi import APIRouter, Request

from app.schemas import Category

router = APIRouter()

_KATEGORILER: list[Category] = [
    Category(key="dress", label="Elbise"),
    Category(key="shirt", label="Gömlek & Tişört"),
    Category(key="shoe", label="Ayakkabı"),
    Category(key="bag", label="Çanta"),
    Category(key="home", label="Ev & Yaşam"),
    Category(key="cosmetics", label="Kozmetik"),
    Category(key="tech", label="Teknoloji"),
    Category(key="sport", label="Spor"),
    Category(key="baby", label="Bebek"),
]

@router.get("/categories", response_model=list[Category])
async def get_categories(request: Request):
    return _KATEGORILER
