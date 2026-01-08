"""
SELA 樂透一路發 - 導覽列元件
"""
import flet as ft
from typing import Callable, Optional

from ui.theme import (
    BRAND_ORANGE,
    GREY_LIGHT,
    BLUE_GREY_700,
    create_logo,
)


class NavItem(ft.UserControl):
    """導覽項目"""
    
    def __init__(
        self,
        icon: str,
        label: str,
        route: str,
        selected: bool = False,
        on_click: Optional[Callable] = None,
    ):
        super().__init__()
        self.icon = icon
        self.label = label
        self.route = route
        self.selected = selected
        self._on_click = on_click
    
    def build(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(self.icon, size=20),
                    ft.Text(
                        self.label,
                        size=14,
                        weight=ft.FontWeight.W_500 if self.selected else ft.FontWeight.W_400,
                        color=BRAND_ORANGE if self.selected else BLUE_GREY_700,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=ft.Colors.with_opacity(0.1, BRAND_ORANGE) if self.selected else None,
            border=ft.border.only(left=ft.BorderSide(3, BRAND_ORANGE)) if self.selected else None,
            on_click=self._handle_click,
            ink=True,
        )
    
    def _handle_click(self, e):
        if self._on_click:
            self._on_click(self.route)


class NavBar(ft.UserControl):
    """側邊導覽列"""
    
    NAV_ITEMS = [
        ("🏠", "首頁", "/dashboard"),
        ("🎰", "我的系列團", "/series"),
        ("📊", "統計報表", "/statistics"),
        ("💰", "錢包", "/wallet"),
        ("🎫", "個人彩券", "/personal"),
        ("⚙️", "設定", "/settings"),
    ]
    
    def __init__(
        self,
        current_route: str = "/dashboard",
        user_name: str = "用戶",
        user_picture: Optional[str] = None,
        on_navigate: Optional[Callable] = None,
        on_logout: Optional[Callable] = None,
    ):
        super().__init__()
        self.current_route = current_route
        self.user_name = user_name
        self.user_picture = user_picture
        self._on_navigate = on_navigate
        self._on_logout = on_logout
    
    def build(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    # LOGO
                    ft.Container(
                        content=create_logo(36),
                        padding=ft.padding.only(left=20, top=20, bottom=10),
                    ),
                    
                    ft.Divider(height=1),
                    
                    # 導覽選單
                    *[
                        NavItem(
                            icon=icon,
                            label=label,
                            route=route,
                            selected=(route == self.current_route),
                            on_click=self._handle_navigate,
                        )
                        for icon, label, route in self.NAV_ITEMS
                    ],
                    
                    ft.Container(expand=True),
                    
                    ft.Divider(height=1),
                    
                    # 用戶資訊
                    self._build_user_section(),
                ],
            ),
            width=220,
            bgcolor=GREY_LIGHT,
        )
    
    def _build_user_section(self) -> ft.Container:
        """建立用戶區塊"""
        avatar = (
            ft.CircleAvatar(
                foreground_image_src=self.user_picture,
                content=ft.Text(self.user_name[0] if self.user_name else "?"),
                bgcolor=BRAND_ORANGE,
                color=ft.Colors.WHITE,
            )
            if self.user_picture
            else ft.CircleAvatar(
                content=ft.Text(self.user_name[0] if self.user_name else "?"),
                bgcolor=BRAND_ORANGE,
                color=ft.Colors.WHITE,
            )
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            avatar,
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        self.user_name,
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        "查看個人資料",
                                        size=12,
                                        color=ft.Colors.GREY_500,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=10),
                    ft.TextButton(
                        text="登出",
                        icon=ft.Icons.LOGOUT,
                        on_click=self._handle_logout,
                        style=ft.ButtonStyle(color=ft.Colors.GREY_600),
                    ),
                ],
            ),
            padding=20,
        )
    
    def _handle_navigate(self, route: str):
        """處理導覽"""
        if self._on_navigate:
            self._on_navigate(route)
    
    def _handle_logout(self, e):
        """處理登出"""
        if self._on_logout:
            self._on_logout()
