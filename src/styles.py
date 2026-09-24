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

    QLabel#resource_label {
        color: #B8C2CC;
        font-size: 12px;
    }
"""
