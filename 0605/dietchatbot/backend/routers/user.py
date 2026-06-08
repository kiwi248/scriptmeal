"""
즐겨찾기 / 레시피 히스토리 엔드포인트

POST /api/history       - 레시피 히스토리 저장 (프론트에서 응답 완료 후 자동 호출)
GET  /api/history       - 히스토리 조회 (?session_id=xxx)
POST /api/favorites     - 즐겨찾기 저장
GET  /api/favorites     - 즐겨찾기 조회 (?session_id=xxx)
DELETE /api/favorites/{id} - 즐겨찾기 삭제
"""

from fastapi import APIRouter, HTTPException, Query, Response
from backend.db.user_db import get_user_db
from backend.schemas import RecordCreate, RecordResponse, FavoriteCreate, FavoriteResponse

router = APIRouter(prefix="/api", tags=["user"])


# ── 히스토리 ───────────────────────────────────────────────────────────────────

@router.post("/history", response_model=RecordResponse, status_code=201)
def save_history(body: RecordCreate):
    print(f"🛜 POST /history - session: {body.session_id[:8]}, intent: {body.intent}")
    try:
        return get_user_db().save_history(
            body.session_id, body.user_message, body.recipe_reply, body.intent
        )
    except Exception as e:
        print(f"🛜❌ /history 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=list[RecordResponse])
def get_history(session_id: str = Query(..., description="세션 ID")):
    print(f"🛜 GET /history - session: {session_id[:8]}")
    try:
        return get_user_db().get_history(session_id)
    except Exception as e:
        print(f"🛜❌ /history 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{history_id}")
def delete_history(history_id: int):
    print(f"🛜 DELETE /history/{history_id}")
    try:
        deleted = get_user_db().delete_history(history_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="히스토리를 찾을 수 없습니다.")
        return {"message": "삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"🛜❌ /history 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── 즐겨찾기 ───────────────────────────────────────────────────────────────────
# POST /favorites
@router.post("/favorites", response_model=FavoriteResponse, status_code=201)  # ← response_model 교체
def save_favorite(body: FavoriteCreate, response: Response):                   # ← body 타입 교체
    print(f"🛜 POST /favorites - session: {body.session_id[:8]}, intent: {body.intent}")
    try:
        db = get_user_db()
        check = db.conn.cursor()
        check.execute(
            "SELECT id FROM favorites WHERE session_id=%s AND user_message=%s AND recipe_reply=%s",
            (body.session_id, body.user_message, body.recipe_reply)
        )
        existing_id = check.fetchone()
        check.close()

        if existing_id:
            raise HTTPException(status_code=400, detail="이미 즐겨찾기에 저장된 항목입니다.")

        return db.save_favorite(
            body.session_id, body.user_message, body.recipe_reply,
            body.intent, body.history_id   # ← history_id 전달
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"🛜❌ /favorites 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites", response_model=list[FavoriteResponse])
def get_favorites(session_id: str = Query(..., description="세션 ID")):
    print(f"🛜 GET /favorites - session: {session_id[:8]}")
    try:
        return get_user_db().get_favorites(session_id)
    except Exception as e:
        print(f"🛜❌ /favorites 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: int):
    print(f"🛜 DELETE /favorites/{favorite_id}")
    try:
        deleted = get_user_db().delete_favorite(favorite_id)
        if not deleted:
            print(f"🛜⚠️ /favorites/{favorite_id} - 해당 id 없음")
            raise HTTPException(status_code=404, detail="즐겨찾기를 찾을 수 없습니다.")
        return {"message": "삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"🛜❌ /favorites 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
