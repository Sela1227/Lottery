"""
SELA 樂透一路發 - 認證 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.config import settings
from app.services.auth.line_auth import line_auth
from app.services.auth.user_service import user_service
from app.schemas.user import TokenResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])

# 暫存 state（正式環境應用 Redis）
_state_store: dict[str, bool] = {}


@router.get("/line")
async def line_login():
    """
    LINE 登入
    
    重導向到 LINE 授權頁面
    """
    state = line_auth.generate_state()
    _state_store[state] = True  # 記錄有效的 state
    
    auth_url = line_auth.get_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/line/callback")
async def line_callback(
    code: str = Query(..., description="LINE 授權碼"),
    state: str = Query(..., description="CSRF 防護參數"),
    error: str = Query(None, description="錯誤代碼"),
    error_description: str = Query(None, description="錯誤說明"),
    db: Session = Depends(get_db)
):
    """
    LINE 登入回調
    
    處理 LINE 授權完成後的回調
    """
    # 檢查錯誤
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LINE 登入失敗: {error_description or error}"
        )
    
    # 驗證 state（CSRF 防護）
    if state not in _state_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的 state 參數"
        )
    del _state_store[state]  # 用過即刪
    
    # 用授權碼換取 Token
    token_data = await line_auth.get_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法取得 LINE Token"
        )
    
    # 取得用戶資料
    access_token = token_data.get("access_token")
    profile = await line_auth.get_profile(access_token)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法取得 LINE 用戶資料"
        )
    
    # 取得或建立用戶
    user, is_new = user_service.get_or_create_from_line(
        db=db,
        line_user_id=profile["userId"],
        display_name=profile["displayName"],
        picture_url=profile.get("pictureUrl")
    )
    
    # 產生 JWT Token
    jwt_token = create_access_token(
        user_id=user.id,
        extra_data={
            "display_name": user.display_name,
            "role": user.role.value
        }
    )
    
    # TODO: 正式環境應重導向到前端頁面，並透過 URL 參數或 Cookie 傳遞 Token
    # 目前先直接回傳 JSON（方便測試）
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=settings.jwt_expires_seconds,
        user=UserResponse.model_validate(user)
    )


@router.get("/line/url")
async def get_line_login_url():
    """
    取得 LINE 登入 URL
    
    給前端用，不自動重導向
    """
    state = line_auth.generate_state()
    _state_store[state] = True
    
    return {
        "url": line_auth.get_auth_url(state),
        "state": state
    }
