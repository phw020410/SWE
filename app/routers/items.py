from fastapi import APIRouter, HTTPException, status

from app.schemas import Item, ItemCreate, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

# 간단한 인메모리 저장소 (서버 재시작 시 초기화됨)
_db: dict[int, Item] = {}
_next_id = 1


@router.get("", response_model=list[Item])
def list_items():
    return list(_db.values())


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: int):
    if item_id not in _db:
        raise HTTPException(status_code=404, detail="Item not found")
    return _db[item_id]


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate):
    global _next_id
    item = Item(id=_next_id, **payload.model_dump())
    _db[_next_id] = item
    _next_id += 1
    return item


@router.patch("/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemUpdate):
    if item_id not in _db:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = _db[item_id].model_copy(update=payload.model_dump(exclude_unset=True))
    _db[item_id] = updated
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    if _db.pop(item_id, None) is None:
        raise HTTPException(status_code=404, detail="Item not found")
