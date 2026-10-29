main_windows_style = """
    QWidget#title_bar {
        background-color: #161B22;
        border-bottom: 1px solid #30363D;
    }
    
    QLabel#title_label {
        color: #E6EDF3;
        font-size: 13px;
        font-weight: 500;
    }
    
    QPushButton#title_button {
        background-color: transparent;
        color: #B8C2CC;
        border: none;
        font-size: 17px;
        font-weight: 600;
    }
    
    QPushButton#title_button:hover {
        background-color: #21262D;
        color: #FFFFFF;
    }
    
    QPushButton#close_button {
        background-color: transparent;
        color: #F85149;
        border: none;
        font-size: 20px;
        font-weight: 600;
    }
    
    QPushButton#close_button:hover {
        background-color: #F85149;
        color: #FFFFFF;
    }
    
    QMainWindow {
        background-color: #0D1117;
        color: #C9D1D9;
    }
    
    QTabWidget {
        background-color: #161B22;
    }
    
    QTabBar::tab {
        background-color: #161B22;
        color: #B8C2CC;
        padding: 8px 16px;
        border: 1px solid #30363D;
        border-bottom: none;
        font-weight: 500;
    }
    
    QTabBar::tab:selected {
        background-color: #0D1117;
        color: #E6EDF3;
        font-weight: 500;
    }
    
    QTabBar::tab:hover {
        background-color: #21262D;
        color: #C9D1D9;
    }
    
    QComboBox#grid_selector {
        background-color: #161B22;
        color: #C9D1D9;
        border: 1px solid #30363D;
        border-radius: 4px;
        padding: 5px 10px;
    }
    
    QComboBox#grid_selector:hover {
        background-color: #21262D;
        border-color: #8B949E;
    }
    
    QComboBox#grid_selector QAbstractItemView {
        background-color: #161B22;
        color: #C9D1D9;
        border: 1px solid #30363D;
        selection-background-color: #1F6FEB;
        selection-color: #FFFFFF;
    }
    
    QComboBox#grid_selector:disabled {
        background-color: #21262D;
        color: #6E7681;
        border: 1px solid #30363D;
    }
    
    QWidget#status_bar {
        background-color: #161B22;
        border-top: 1px solid #30363D;
    }

    QLabel#status_indicator {
        color: #3FB950;
        font-size: 12px;
    }

    QLabel#status_label {
        color: #E6EDF3;
        font-size: 12px;
    }

    QLabel#active_profile_label {
    color: #E6EDF3;
    font-size: 12px;
    }

    QLabel#resource_label {
        color: #B8C2CC;
        font-size: 12px;
    }
"""

"""
#####################################
# Configuration tab                 #
#####################################
"""

# Configuration tab: general panels
configuration_panel_style = """
    QWidget#configuration_left {
        border: 1px solid white;
        border-radius: 6px;
    }
"""

configuration_scroll_area_style = """
    QScrollArea {
        border: 1px solid white;
        border-radius: 6px;
        background: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
"""

# Configuration tab: action buttons
configuration_action_button_style = """
    QPushButton {
        color: white;
        font-size: 13px;
        font-weight: bold;
        padding: 6px 12px;
        border: 1px solid #666666;
        border-radius: 4px;
        background-color: #333333;
    }

    QPushButton:hover {
        background-color: #444444;
        border: 1px solid #888888;
    }

    QPushButton:pressed {
        background-color: #555555;
    }
"""

configuration_menu_button_style = """
    QPushButton {
        color: white;
        font-size: 14px;
        font-weight: bold;
        text-align: left;
        padding: 8px 12px;
        border: 1px solid #666666;
        border-radius: 4px;
        background-color: #333333;
    }

    QPushButton:hover {
        background-color: #444444;
        border: 1px solid #888888;
    }

    QPushButton:pressed {
        background-color: #555555;
    }
"""

# Configuration tab: input fields
configuration_field_style = """
    QLineEdit {
        color: white;
        font-size: 14px;
        padding: 5px 8px;
        border: 1px solid #666666;
        border-radius: 4px;
        background-color: #333333;
    }

    QLineEdit:focus {
        border: 1px solid #888888;
    }
"""

# Configuration tab: editing profile indicator
configuration_editing_label_style = """
    font-weight: bold;
    color: #d97706;
"""

configuration_title_style = """
    QLabel {
        color: white;
        font-size: 18px;
        font-weight: bold;
        border: none;
    }
"""

"""
#####################################
# Configuration tab / NVR           #
#####################################
"""

configuration_section_title_style = """
    QLabel {
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
    }
"""

configuration_section_description_style = """
    QLabel {
        color: #CCCCCC;
        font-size: 13px;
        border: none;
    }
"""

configuration_subsection_title_style = """
    QLabel {
        color: white;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
"""

configuration_field_label_style = """
    QLabel {
        color: white;
        font-size: 14px;
        border: none;
    }
"""

configuration_separator_style = """
    QLabel {
        background-color: #555555;
        border: none;
    }
"""

configuration_status_found_style = """
    QLabel {
        color: #00FF00;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
"""

configuration_status_not_found_style = """
    QLabel {
        color: #F85149;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
"""

configuration_profile_list_style = """
    QListWidget {
        color: white;
        font-size: 14px;
        border: 1px solid #666666;
        border-radius: 4px;
        background-color: #333333;
        padding: 4px;
    }

    QListWidget::item {
        padding: 6px;
    }

    QListWidget::item:selected {
        background-color: #555555;
    }
"""

# ---------------------------------------------------------------------
# NVR connection test dialog styles
# ---------------------------------------------------------------------

connection_test_title_style = """
    QLabel {
        font-weight: bold;
        font-size: 16px;
        border: none;
    }
"""

connection_test_pending_style = """
    QLabel {
        color: #9CA3AF;
        border: none;
    }
"""

connection_test_success_style = """
    QLabel {
        color: #3FB950;
        border: none;
    }
"""

connection_test_failure_style = """
    QLabel {
        color: #F85149;
        border: none;
    }
"""

# Configuration tab: RTSP template table
rtsp_template_table_style = """
    QTableWidget {
        color: white;
        font-size: 13px;
        gridline-color: #666666;
        border: 1px solid #666666;
        border-radius: 4px;
        background-color: #333333;
        selection-background-color: #555555;
        selection-color: white;
    }

    QTableWidget::item {
        padding: 6px;
    }

    QHeaderView::section {
        color: white;
        font-weight: bold;
        padding: 6px;
        border: 1px solid #666666;
        background-color: #292929;
    }
""" 
