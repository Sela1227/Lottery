"""
SELA 樂透一路發 - 主儀表板
"""
import flet as ft

from ui.theme import (
    BRAND_ORANGE,
    GREY_LIGHT,
    BLUE_GREY_LIGHT,
    BLUE_GREY_700,
    primary_button,
    card,
    scrollable_column,
)


class DashboardPage(ft.UserControl):
    """主儀表板頁面"""
    
    def __init__(self, user_name: str = "用戶"):
        super().__init__()
        self.user_name = user_name
    
    def build(self):
        return scrollable_column(
            controls=[
                # 頂部歡迎區
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"歡迎回來，{self.user_name}！",
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=BLUE_GREY_700,
                                    ),
                                    ft.Text(
                                        "今天是個好日子，祝您好運！🍀",
                                        size=14,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Container(expand=True),
                            primary_button("+ 建立系列團", icon=ft.Icons.ADD),
                        ],
                    ),
                    padding=20,
                ),
                
                # 統計卡片
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self._stat_card("參與中", "3", "系列團"),
                            self._stat_card("總投入", "12,500", "TWD"),
                            self._stat_card("總獎金", "4,200", "TWD"),
                            self._stat_card("投報率", "-66.4%", ""),
                        ],
                        spacing=15,
                        wrap=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=20),
                ),
                
                ft.Container(height=20),
                
                # 進行中的團
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "進行中的系列團",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=BLUE_GREY_700,
                            ),
                            ft.Container(height=10),
                            self._series_card(
                                name="不中不休 A 隊",
                                lottery_type="威力彩",
                                period=5,
                                pool=3800,
                                status="集資中",
                            ),
                            self._series_card(
                                name="發財小隊",
                                lottery_type="大樂透",
                                period=12,
                                pool=8500,
                                status="已購買",
                            ),
                            self._series_card(
                                name="幸運星",
                                lottery_type="今彩539",
                                period=3,
                                pool=2200,
                                status="已開獎",
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=20),
                ),
                
                ft.Container(height=20),
                
                # 最近活動
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "最近活動",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=BLUE_GREY_700,
                            ),
                            ft.Container(height=10),
                            self._activity_item(
                                "🎉",
                                "發財小隊中獎 $4,000",
                                "2 小時前",
                            ),
                            self._activity_item(
                                "💰",
                                "您加碼了 $500 到不中不休 A 隊",
                                "昨天",
                            ),
                            self._activity_item(
                                "🎫",
                                "幸運星第 3 期開始集資",
                                "3 天前",
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=20),
                ),
                
                ft.Container(height=40),
            ],
            expand=True,
        )
    
    def _stat_card(self, label: str, value: str, unit: str) -> ft.Container:
        """建立統計卡片"""
        return card(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=12, color=ft.Colors.GREY_600),
                    ft.Row(
                        controls=[
                            ft.Text(
                                value,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=BLUE_GREY_700,
                            ),
                            ft.Text(unit, size=12, color=ft.Colors.GREY_500),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        spacing=5,
                    ),
                ],
                spacing=5,
            ),
            padding=15,
        )
    
    def _series_card(
        self,
        name: str,
        lottery_type: str,
        period: int,
        pool: int,
        status: str,
    ) -> ft.Container:
        """建立系列團卡片"""
        status_color = {
            "集資中": BRAND_ORANGE,
            "已購買": "#4CAF50",
            "已開獎": "#2196F3",
            "已結算": "#9E9E9E",
        }.get(status, ft.Colors.GREY_500)
        
        return card(
            content=ft.Row(
                controls=[
                    # 左側資訊
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        name,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=BLUE_GREY_700,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            status,
                                            size=11,
                                            color=ft.Colors.WHITE,
                                        ),
                                        bgcolor=status_color,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=10,
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Text(
                                f"{lottery_type} · 第 {period} 期",
                                size=13,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Container(expand=True),
                    # 右側金額
                    ft.Column(
                        controls=[
                            ft.Text("資金池", size=12, color=ft.Colors.GREY_500),
                            ft.Text(
                                f"${pool:,}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=BRAND_ORANGE,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                    ),
                ],
            ),
            padding=15,
        )
    
    def _activity_item(self, icon: str, text: str, time: str) -> ft.Container:
        """建立活動項目"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(icon, size=24),
                    ft.Column(
                        controls=[
                            ft.Text(text, size=14, color=BLUE_GREY_700),
                            ft.Text(time, size=12, color=ft.Colors.GREY_500),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.symmetric(vertical=8),
        )


def create_dashboard_page(user_name: str = "用戶") -> DashboardPage:
    """建立主儀表板"""
    return DashboardPage(user_name=user_name)
