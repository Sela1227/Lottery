"""
SELA 樂透一路發 - 品牌主題
🚫 品牌色彩與 LOGO 樣式不可更改
"""
import flet as ft


# ===========================================
# 🎨 品牌色彩（不可更改）
# ===========================================
BRAND_ORANGE = "#FA7A35"  # SELA 企業識別色（愛馬仕橘）

# 輔助色
GREY_LIGHT = ft.Colors.GREY_50           # 左側面板背景
BLUE_GREY_LIGHT = ft.Colors.BLUE_GREY_50 # 右側面板背景
BLUE_GREY_700 = ft.Colors.BLUE_GREY_700  # 標題文字

# 狀態色
SUCCESS_GREEN = "#4CAF50"
WARNING_YELLOW = "#FF9800"
ERROR_RED = "#F44336"
INFO_BLUE = "#2196F3"


# ===========================================
# 📝 字型設定
# ===========================================
FONT_FAMILY = "Microsoft JhengHei UI"  # 主要 UI 字型
FONT_MONOSPACE = "Consolas"            # 等寬字型


# ===========================================
# 📐 尺寸規範
# ===========================================
# 對話框尺寸（固定值）
DIALOG_SMALL = (350, 280)     # 確認刪除
DIALOG_NORMAL = (400, 380)    # 新增/編輯
DIALOG_LARGE = (420, 450)     # 含時間欄位

# 最低支援螢幕
MIN_WIDTH = 1440
MIN_HEIGHT = 900


# ===========================================
# 🏷️ LOGO 元件（不可更改樣式）
# ===========================================
def create_logo(size: int = 48) -> ft.Text:
    """
    建立 SELA LOGO
    
    Args:
        size: 字型大小（36-56px）
    
    🚫 顏色與字重不可更改
    """
    return ft.Text(
        "SELA",
        size=size,
        color=BRAND_ORANGE,
        weight=ft.FontWeight.BOLD,
        font_family=FONT_FAMILY,
    )


def create_logo_with_tagline(logo_size: int = 48, tagline_size: int = 16) -> ft.Column:
    """
    建立 SELA LOGO + 標語
    
    Args:
        logo_size: LOGO 字型大小
        tagline_size: 標語字型大小
    """
    return ft.Column(
        controls=[
            create_logo(logo_size),
            ft.Text(
                "樂透一路發",
                size=tagline_size,
                color=BLUE_GREY_700,
                font_family=FONT_FAMILY,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
    )


# ===========================================
# 🔘 按鈕樣式
# ===========================================
def primary_button(text: str, on_click=None, icon=None, width=None) -> ft.ElevatedButton:
    """主要按鈕（橘色）"""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=BRAND_ORANGE,
        ),
    )


def secondary_button(text: str, on_click=None, icon=None, width=None) -> ft.OutlinedButton:
    """次要按鈕（邊框）"""
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        style=ft.ButtonStyle(
            color=BRAND_ORANGE,
        ),
    )


def text_button(text: str, on_click=None, icon=None) -> ft.TextButton:
    """文字按鈕"""
    return ft.TextButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=BRAND_ORANGE,
        ),
    )


# ===========================================
# 📋 表單元件
# ===========================================
def text_field(
    label: str,
    value: str = "",
    hint_text: str = None,
    password: bool = False,
    multiline: bool = False,
    on_change=None,
    width=None,
) -> ft.TextField:
    """文字輸入框（必須使用 dense=True）"""
    return ft.TextField(
        label=label,
        value=value,
        hint_text=hint_text,
        password=password,
        multiline=multiline,
        on_change=on_change,
        width=width,
        dense=True,  # 必須
        border_color=BRAND_ORANGE,
        focused_border_color=BRAND_ORANGE,
    )


def dropdown(
    label: str,
    options: list[str],
    value: str = None,
    on_change=None,
    width=None,
) -> ft.Dropdown:
    """下拉選單（必須使用 dense=True）"""
    return ft.Dropdown(
        label=label,
        value=value,
        options=[ft.dropdown.Option(opt) for opt in options],
        on_change=on_change,
        width=width,
        dense=True,  # 必須
        border_color=BRAND_ORANGE,
        focused_border_color=BRAND_ORANGE,
    )


# ===========================================
# 📦 容器元件
# ===========================================
def card(content: ft.Control, padding: int = 20) -> ft.Container:
    """卡片容器"""
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
        ),
    )


def scrollable_column(controls: list, **kwargs) -> ft.Column:
    """可捲動的 Column（必須設定 scroll）"""
    return ft.Column(
        controls=controls,
        scroll=ft.ScrollMode.AUTO,  # 必須
        **kwargs,
    )


# ===========================================
# 🔔 通知元件
# ===========================================
def show_snackbar(page: ft.Page, message: str, success: bool = True):
    """顯示底部通知"""
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=SUCCESS_GREEN if success else ERROR_RED,
    )
    page.snack_bar.open = True
    page.update()


def confirm_dialog(
    title: str,
    content: str,
    on_confirm,
    on_cancel=None,
) -> ft.AlertDialog:
    """確認對話框"""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[
            ft.TextButton("取消", on_click=on_cancel),
            primary_button("確認", on_click=on_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
