"""Game Result Popup - Non-blocking popup for game results"""

import tkinter as tk
from typing import Callable, Optional


class GameResultPopup(tk.Toplevel):
    """Non-blocking game result popup with auto-close capability"""

    _instance: Optional["GameResultPopup"] = None

    def __init__(self, parent, result_data: dict, on_close: Optional[Callable] = None):
        # Close any existing popup
        if GameResultPopup._instance is not None:
            try:
                GameResultPopup._instance.destroy()
            except Exception:
                pass
        
        GameResultPopup._instance = self
        
        super().__init__(parent)
        
        self.on_close = on_close
        self.auto_close_id = None
        self._is_closed = False
        
        # Window setup
        self.title("Game Finished")
        self.configure(bg="#1a1a1a")
        self.resizable(False, False)
        
        # Make it stay on top but not modal (non-blocking)
        self.attributes("-topmost", True)
        
        # Center on screen
        self.update_idletasks()
        
        # Parse result data
        score = result_data.get("score", "Game completed")
        reason = result_data.get("reason", "")
        our_color = result_data.get("our_color", "unknown")
        move_count = result_data.get("move_count", 0)
        
        # Determine result type for styling
        result_type = "unknown"
        if "1-0" in score:
            result_type = "win" if our_color.lower() == "white" else "loss"
        elif "0-1" in score:
            result_type = "win" if our_color.lower() == "black" else "loss"
        elif "1/2" in score or "draw" in score.lower():
            result_type = "draw"
        
        # Colors based on result
        if result_type == "win":
            accent_color = "#00AA00"
            result_emoji = "🏆"
        elif result_type == "loss":
            accent_color = "#AA0000"
            result_emoji = "💔"
        elif result_type == "draw":
            accent_color = "#888888"
            result_emoji = "🤝"
        else:
            accent_color = "#666666"
            result_emoji = "🏁"
        
        # Content frame
        content = tk.Frame(self, bg="#1a1a1a", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Result emoji and score
        tk.Label(
            content,
            text=f"{result_emoji} {score}",
            font=("Segoe UI", 18, "bold"),
            fg=accent_color,
            bg="#1a1a1a"
        ).pack(pady=(0, 10))
        
        # Reason
        if reason:
            tk.Label(
                content,
                text=reason,
                font=("Segoe UI", 11),
                fg="#cccccc",
                bg="#1a1a1a"
            ).pack(pady=(0, 5))
        
        # Move count
        if move_count > 0:
            tk.Label(
                content,
                text=f"{move_count} moves",
                font=("Segoe UI", 9),
                fg="#888888",
                bg="#1a1a1a"
            ).pack(pady=(0, 15))
        
        # OK button
        ok_btn = tk.Button(
            content,
            text="OK",
            command=self._close,
            font=("Segoe UI", 10),
            bg="#333333",
            fg="#ffffff",
            activebackground="#444444",
            activeforeground="#ffffff",
            relief="flat",
            padx=30,
            pady=5,
            cursor="hand2"
        )
        ok_btn.pack(pady=(5, 0))
        
        # Auto-close hint
        self.countdown_label = tk.Label(
            content,
            text="Auto-closing in 10s...",
            font=("Segoe UI", 8),
            fg="#555555",
            bg="#1a1a1a"
        )
        self.countdown_label.pack(pady=(10, 0))
        
        # Bind escape key
        self.bind("<Escape>", lambda e: self._close())
        self.bind("<Return>", lambda e: self._close())
        
        # Focus the window
        self.focus_force()
        ok_btn.focus_set()
        
        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Start auto-close countdown
        self._start_countdown(10)
    
    def _start_countdown(self, seconds: int):
        """Start the auto-close countdown"""
        if self._is_closed:
            return
        
        if seconds <= 0:
            self._close()
            return
        
        try:
            self.countdown_label.configure(text=f"Auto-closing in {seconds}s...")
            self.auto_close_id = self.after(1000, lambda: self._start_countdown(seconds - 1))
        except Exception:
            # Widget was destroyed
            pass
    
    def _close(self):
        """Close the popup and trigger callback"""
        if self._is_closed:
            return
        self._is_closed = True
        
        if self.auto_close_id:
            try:
                self.after_cancel(self.auto_close_id)
            except Exception:
                pass
            self.auto_close_id = None
        
        GameResultPopup._instance = None
        
        # Destroy first, then callback (prevents re-triggering)
        try:
            self.destroy()
        except Exception:
            pass
        
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
    
    @classmethod
    def close_existing(cls):
        """Close any existing popup"""
        if cls._instance is not None:
            try:
                cls._instance._close()
            except Exception:
                pass
            cls._instance = None


def show_game_result(result_data: dict, parent: tk.Tk = None, on_close: Callable = None):
    """Show game result in a non-blocking popup
    
    Args:
        result_data: Dict with score, reason, our_color, move_count
        parent: Parent Tk window (optional, creates temp root if None)
        on_close: Callback when popup closes
    """
    if parent is None:
        # Try to find existing Tk root
        try:
            parent = tk._default_root
        except Exception:
            pass
    
    if parent is None:
        # Fallback - no GUI available, just call the callback
        if on_close:
            on_close()
        return None
    
    return GameResultPopup(parent, result_data, on_close)
