"""
SELA 樂透一路發 - Flet UI 入口
"""
import flet as ft

from ui.theme import FONT_FAMILY, BRAND_ORANGE, BLUE_GREY_LIGHT, show_snackbar
from ui.services.auth import auth_manager
from ui.services.api import api
from ui.pages.login import create_login_page
from ui.pages.dashboard import create_dashboard_page
from ui.components.navbar import NavBar


class App:
    """應用程式主類別"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_route = "/login"
        self._setup_page()
        self._setup_routes()
    
    def _setup_page(self):
        """設定頁面"""
        self.page.title = "SELA 樂透一路發"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = BLUE_GREY_LIGHT
        
        # 字型設定
        self.page.fonts = {
            "Noto Sans TC": "https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap",
        }
        self.page.theme = ft.Theme(font_family="Noto Sans TC")
        
        # 視窗設定（桌面版）
        self.page.window.min_width = 1200
        self.page.window.min_height = 700
        self.page.window.width = 1440
        self.page.window.height = 900
    
    def _setup_routes(self):
        """設定路由"""
        self.page.on_route_change = self._handle_route_change
        
        # 嘗試從 storage 載入認證狀態
        if auth_manager.load_from_storage(self.page):
            # 設定 API token
            api.set_token(auth_manager.token)
            self.navigate_to("/dashboard")
        else:
            self.navigate_to("/login")
    
    def _handle_route_change(self, e):
        """處理路由變更"""
        self.navigate_to(e.route)
    
    def navigate_to(self, route: str):
        """導覽到指定路由"""
        # 檢查認證
        if route != "/login" and not auth_manager.is_authenticated:
            route = "/login"
        
        self.current_route = route
        self.page.clean()
        
        if route == "/login":
            self._show_login()
        else:
            self._show_main_layout(route)
        
        self.page.update()
    
    def _show_login(self):
        """顯示登入頁"""
        self.page.add(create_login_page(on_login_success=self._on_login_success))
    
    def _show_main_layout(self, route: str):
        """顯示主佈局（含導覽列）"""
        user = auth_manager.user
        
        # 導覽列
        navbar = NavBar(
            current_route=route,
            user_name=user.display if user else "用戶",
            user_picture=user.picture_url if user else None,
            on_navigate=self.navigate_to,
            on_logout=self._on_logout,
        )
        
        # 主內容區
        content = self._get_page_content(route)
        
        # 組合佈局
        layout = ft.Row(
            controls=[
                navbar,
                ft.Container(
                    content=content,
                    expand=True,
                    bgcolor=BLUE_GREY_LIGHT,
                ),
            ],
            expand=True,
            spacing=0,
        )
        
        self.page.add(layout)
    
    def _get_page_content(self, route: str) -> ft.Control:
        """取得頁面內容"""
        user = auth_manager.user
        user_name = user.display if user else "用戶"
        
        if route == "/dashboard":
            return create_dashboard_page(user_name=user_name)
        elif route == "/series":
            return self._placeholder_page("我的系列團", "🎰")
        elif route == "/statistics":
            return self._placeholder_page("統計報表", "📊")
        elif route == "/wallet":
            return self._placeholder_page("錢包", "💰")
        elif route == "/personal":
            return self._placeholder_page("個人彩券", "🎫")
        elif route == "/settings":
            return self._placeholder_page("設定", "⚙️")
        else:
            return self._placeholder_page("找不到頁面", "❓")
    
    def _placeholder_page(self, title: str, icon: str) -> ft.Container:
        """佔位頁面（Step 2 會實作）"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(icon, size=64),
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "此功能將在 Step 2 實作",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
    
    def _on_login_success(self, token: str, user_data: dict):
        """登入成功回調"""
        # 儲存認證狀態
        auth_manager.login(token, user_data, self.page)
        api.set_token(token)
        
        # 導覽到首頁
        self.navigate_to("/dashboard")
        show_snackbar(self.page, f"歡迎回來，{auth_manager.user.display}！")
    
    def _on_logout(self):
        """登出"""
        auth_manager.logout(self.page)
        api.clear_token()
        self.navigate_to("/login")
        show_snackbar(self.page, "已登出", success=True)


def main(page: ft.Page):
    """Flet 主函數"""
    App(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8000)
