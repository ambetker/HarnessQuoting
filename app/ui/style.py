"""Design tokens and QSS approximating design_handoff_harness_quoting's
"Design Tokens" section. QSS can't do real box-shadow or CSS grid, so
shadows are approximated with subtle borders and layouts use Qt's own
box model instead of chasing pixel parity (see the plan's noted risk).
"""

COLORS = {
    "page_bg": "#f6f7f7",
    "surface": "#ffffff",
    "zebra_1": "#fbfbfa",
    "zebra_2": "#fcfcfb",
    "zebra_3": "#fafaf9",
    "border_card": "#eaeae7",
    "border_inner": "#f1f1ee",
    "border_row": "#f6f6f4",
    "border_input": "#e0e0dc",
    "border_pill": "#e4e3df",
    "border_dashed": "#d5d3cd",
    "text_primary": "#1a1917",
    "text_secondary": "#3d3b37",
    "text_secondary_2": "#5c5952",
    "text_label": "#6f6c66",
    "text_muted": "#8b887f",
    "text_disabled": "#a3a09a",
    "text_disabled_2": "#b3b0aa",
    "text_disabled_3": "#c4c1bb",
    "accent": "#b45309",
    "accent_hover": "#9a460a",
    "accent_text": "#8a4007",
    "accent_tint": "#fdf7f0",
    "accent_tint_border": "#f2e6d6",
    "accent_hover_border": "#c9a06a",
    "chart_material": "#b45309",
    "chart_labor": "#e0a463",
    "chart_other": "#e6e5e1",
    "dk_pill_bg": "#eef4f8",
    "dk_pill_fg": "#3a6b8c",
    "mfr_pill_bg": "#f2f1ec",
    "mfr_pill_fg": "#6f6c66",
    "unresolved_pill_bg": "#faf3f1",
    "unresolved_pill_fg": "#a8746a",
    "warning_bg": "#fdf3f1",
    "warning_border": "#f2ded9",
    "warning_text": "#8a4237",
    "destructive_hover_bg": "#f7eeee",
    "destructive_hover_fg": "#a8443b",
    "status_connected": "#2f8f5b",
    "status_disconnected": "#d1a24a",
}

FONT_FAMILY = "Helvetica Neue"

STYLESHEET = f"""
QWidget {{
    background: {COLORS['page_bg']};
    color: {COLORS['text_primary']};
    font-family: '{FONT_FAMILY}';
    font-size: 13.5px;
}}

QFrame[card="true"] {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border_card']};
    border-radius: 12px;
}}

QLabel[role="card-title"] {{
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}}
QLabel[role="card-subtitle"] {{
    font-size: 12.5px;
    color: {COLORS['text_muted']};
    background: transparent;
}}
QLabel[role="field-label"] {{
    font-size: 12px;
    font-weight: 500;
    color: {COLORS['text_label']};
    background: transparent;
}}
QLabel[role="section-label"] {{
    font-size: 12px;
    font-weight: 600;
    color: {COLORS['text_muted']};
    background: transparent;
}}
QLabel[role="muted"] {{
    font-size: 12.5px;
    color: {COLORS['text_muted']};
    background: transparent;
}}
QLabel[role="page-title"] {{
    font-size: 19px;
    font-weight: 600;
    background: transparent;
}}
QLabel[role="money-lg"] {{
    font-size: 22px;
    font-weight: 600;
    color: {COLORS['accent']};
    background: transparent;
}}
QLabel[role="money-xl"] {{
    font-size: 28px;
    font-weight: 600;
    color: {COLORS['accent']};
    background: transparent;
}}

QLineEdit, QComboBox {{
    padding: 9px 11px;
    border: 1px solid {COLORS['border_input']};
    border-radius: 8px;
    background: {COLORS['surface']};
    font-size: 14px;
    color: {COLORS['text_primary']};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {COLORS['accent']};
}}
/* Without explicit drop-down/down-arrow subcontrol rules, Qt's macOS
   style miscalculates the popup-arrow region once any stylesheet
   touches QComboBox at all, and can paint past the widget's own
   right edge, overlapping whatever's laid out next to it. */
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
    background: transparent;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QLineEdit[emphasized="true"] {{
    border: 1px solid {COLORS['accent']};
    background: {COLORS['accent_tint']};
    color: {COLORS['accent_text']};
    font-weight: 600;
}}

QLineEdit[bare="true"], QComboBox[bare="true"] {{
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    padding: 5px 7px;
}}
QLineEdit[bare="true"]:hover, QComboBox[bare="true"]:hover {{
    border: 1px solid {COLORS['border_card']};
    background: {COLORS['zebra_1']};
}}

QPushButton[variant="primary"] {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{ background: {COLORS['accent_hover']}; }}
QPushButton[variant="primary"]:disabled {{ background: {COLORS['text_disabled_2']}; }}

QPushButton[variant="secondary"] {{
    background: {COLORS['surface']};
    color: {COLORS['text_secondary_2']};
    border: 1px solid {COLORS['border_input']};
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
}}
QPushButton[variant="secondary"]:hover {{ border: 1px solid {COLORS['accent']}; color: {COLORS['accent']}; }}
QPushButton[variant="secondary"]:disabled {{
    background: {COLORS['zebra_1']};
    color: {COLORS['text_disabled_3']};
    border: 1px solid {COLORS['border_row']};
}}

QPushButton[variant="destructive"] {{
    background: {COLORS['surface']};
    color: {COLORS['text_secondary_2']};
    border: 1px solid {COLORS['border_input']};
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
}}
QPushButton[variant="destructive"]:hover {{ border: 1px solid #c08a80; color: {COLORS['destructive_hover_fg']}; }}

QPushButton[variant="pill"] {{
    padding: 9px 14px;
    border-radius: 9px;
    font-size: 13px;
    border: 1px solid {COLORS['border_pill']};
    background: transparent;
    color: {COLORS['text_label']};
}}
QPushButton[variant="pill"]:hover {{ border: 1px solid {COLORS['accent_hover_border']}; }}
QPushButton[variant="pill-active"] {{
    padding: 9px 14px;
    border-radius: 9px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid {COLORS['accent']};
    background: {COLORS['surface']};
    color: {COLORS['text_primary']};
}}

QPushButton[variant="dashed"] {{
    padding: 9px 14px;
    border-radius: 9px;
    font-size: 13px;
    border: 1px dashed {COLORS['border_dashed']};
    background: transparent;
    color: {COLORS['text_muted']};
}}
QPushButton[variant="dashed"]:hover {{ color: {COLORS['accent']}; }}

QTableWidget {{
    background: {COLORS['surface']};
    border: none;
    gridline-color: {COLORS['border_row']};
    font-size: 13.5px;
}}
QHeaderView::section {{
    background: {COLORS['surface']};
    color: {COLORS['text_muted']};
    font-size: 12px;
    font-weight: 500;
    border: none;
    border-bottom: 1px solid {COLORS['border_inner']};
    padding: 6px 8px;
}}
QTableWidget::item {{
    border-bottom: 1px solid {COLORS['border_row']};
    padding: 2px 4px;
}}

QScrollArea {{ border: none; background: transparent; }}
"""
