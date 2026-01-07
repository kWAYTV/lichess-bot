"""Lichess DOM Selectors - Centralized selector constants"""

from selenium.webdriver.common.by import By


class Selectors:
    """All Lichess DOM selectors in one place"""

    # URLs
    LICHESS_URL = "https://www.lichess.org"
    LICHESS_URL_ALT = "https://lichess.org"

    # Game board
    GAME_BOARD_CONTAINER = (By.CSS_SELECTOR, "main.round cg-container")
    BOARD_STYLE_CONTAINER = (
        By.XPATH,
        "/html/body/div[2]/main/div[1]/div[1]/div/cg-container",
    )

    # Move input - multiple fallbacks
    MOVE_INPUT_SELECTORS = [
        (By.CLASS_NAME, "ready"),
        (By.CSS_SELECTOR, "main.round input"),
        (By.CSS_SELECTOR, "input.ready"),
        (By.XPATH, "//main[contains(@class,'round')]//input"),
    ]

    # Move list elements
    MOVE_LIST_CLASS = "kwdb"
    MOVE_XPATH_TEMPLATE = "//kwdb[{move_number}]"
    MOVE_XPATH_MEDIUM = "//rm6/l4x/kwdb[{move_number}]"
    MOVE_XPATH_FULL = "/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[{move_number}]"

    # Player orientation
    ORIENTATION_WHITE = "orientation-white"

    # Game state
    GAME_OVER_CLASS = "follow-up"

    # Game result elements
    RESULT_SCORE = (By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[1]")
    RESULT_REASON = (By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[2]")

    # Login detection
    LOGIN_INDICATORS = [
        "#user_tag",
        ".site-title .user",
        "[data-icon='H']",
        ".dasher .toggle",
    ]
    LOGIN_PAGE_INDICATORS = ["logout", "preferences", "profile"]

    # URL patterns to exclude (not a game)
    NON_GAME_URL_PATTERNS = ["/tournament", "/study", "/training"]

    # Clocks
    CLOCK_ENEMY = (By.XPATH, "/html/body/div[2]/main/div[1]/div[7]")
    CLOCK_OUR = (By.XPATH, "/html/body/div[2]/main/div[1]/div[10]/input")
    CLOCK_CSS_BOTTOM = (By.CSS_SELECTOR, "div.rclock.rclock-bottom")

    @classmethod
    def get_move_xpaths(cls, move_number: int) -> list:
        """Get all XPath variants for a move number"""
        return [
            cls.MOVE_XPATH_TEMPLATE.format(move_number=move_number),
            cls.MOVE_XPATH_MEDIUM.format(move_number=move_number),
            cls.MOVE_XPATH_FULL.format(move_number=move_number),
        ]

