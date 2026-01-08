"""
SELA 樂透一路發 - 登入頁面
"""
import flet as ft
from typing import Callable, Optional

from ui.theme import (
    BRAND_ORANGE,
    BLUE_GREY_700,
    FONT_FAMILY,
    create_logo_with_tagline,
    primary_button,
    card,
)


class LoginPage(ft.UserControl):
    """登入頁面"""
    
    def __init__(self, on_login_success: Optional[Callable] = None):
        super().__init__()
        self.on_login_success = on_login_success
        self._loading = False
    
    def build(self):
        self._login_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg",
                        width=24,
                        height=24,
                        error_content=ft.Text("LINE", color=ft.Colors.WHITE),
                    ),
                    ft.Text(
                        "以 LINE 帳號登入",
                        size=16,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            width=280,
            height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor="#06C755",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self._handle_line_login,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # LOGO
                    create_logo_with_tagline(logo_size=56, tagline_size=20),
                    
                    ft.Container(height=40),
                    
                    # 登入卡片
                    card(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "歡迎使用",
                                    size=18,
                                    color=BLUE_GREY_700,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                
                                ft.Container(height=20),
                                
                                # LINE 登入按鈕
                                self._login_button,
                                
                                ft.Container(height=20),
                                
                                ft.Text(
                                    "登入即表示您同意服務條款",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                        ),
                        padding=30,
                    ),
                    
                    ft.Container(height=20),
                    
                    # 測試登入按鈕（開發用）
                    ft.TextButton(
                        text="開發模式：模擬登入",
                        on_click=self._handle_dev_login,
                        style=ft.ButtonStyle(color=ft.Colors.GREY_400),
                    ),
                    
                    ft.Container(height=10),
                    
                    # 版權資訊
                    ft.Text(
                        "© 2024 SELA. All rights reserved.",
                        size=12,
                        color=ft.Colors.GREY_400,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.WHITE, ft.Colors.GREY_100],
            ),
        )
    
    def _handle_line_login(self, e):
        """處理 LINE 登入"""
        if self._loading:
            return
        
        # 開啟 LINE 登入頁面
        if self.page:
            self.page.launch_url("/api/v1/auth/line")
    
    def _handle_dev_login(self, e):
        """開發模式：模擬登入"""
        if self._loading:
            return
        
        # 模擬登入成功
        mock_token = "dev_token_12345"
        mock_user = {
            "id": 1,
            "line_user_id": "U1234567890",
            "display_name": "測試用戶",
            "picture_url": None,
            "nickname": None,
            "email": None,
            "phone": None,
            "status": "active",
            "role": "admin",
            "wallet_balance": 1000.0,
        }
        
        if self.on_login_success:
            self.on_login_success(mock_token, mock_user)


def create_login_page(on_login_success: Optional[Callable] = None) -> LoginPage:
    """建立登入頁面"""
    return LoginPage(on_login_success=on_login_success)
