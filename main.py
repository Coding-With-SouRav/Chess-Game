import configparser
import os
import sys, ctypes
import threading
import tkinter as tk
from tkinter import messagebox
import chess
import chess.engine
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.example.ChessAI")

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Resource not found: {full_path}")
    return full_path

LIGHT_COLOR = "#f0d9b5"  # Standard light chess square
DARK_COLOR = "#b58863"   # Standard dark chess square
HIGHLIGHT_COLOR = "#7c3aed"
LEGAL_MOVE_COLOR = "#06b6d4"
SQUARE_SIZE = 100

COMMON_STOCKFISH_PATHS = [
    os.getenv("STOCKFISH_PATH"),
    "/usr/bin/stockfish",
    "/usr/local/bin/stockfish",
    "C:\\Program Files\\Stockfish\\stockfish.exe",
    "C:\\Program Files (x86)\\Stockfish\\stockfish.exe",
    "stockfish"
]
PIECE_VALUES = {
    chess.PAWN:  100,
    chess.KNIGHT:320,
    chess.BISHOP:330,
    chess.ROOK:  500,
    chess.QUEEN: 900,
    chess.KING:  20000
}

def material_evaluation(board: chess.Board) -> int:
    score = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)

        if p:
            val = PIECE_VALUES.get(p.piece_type, 0)
            score += val if p.color == chess.WHITE else -val
    return score

def negamax(board: chess.Board, depth: int, alpha: int, beta: int, color: int) -> int:

    if depth == 0 or board.is_game_over():
        return color * material_evaluation(board)
    max_eval = -10**9
    for move in board.legal_moves:
        board.push(move)
        val = -negamax(board, depth-1, -beta, -alpha, -color)
        board.pop()

        if val > max_eval:
            max_eval = val
        alpha = max(alpha, val)

        if alpha >= beta:
            break
    return max_eval

def find_best_move_negamax(board: chess.Board, depth: int) -> chess.Move:
    best, best_move = -10**9, None
    color = 1 if board.turn == chess.WHITE else -1
    for move in board.legal_moves:
        board.push(move)
        val = -negamax(board, depth-1, -10**9, 10**9, -color)
        board.pop()

        if val > best:
            best = val
            best_move = move
    return best_move

class ChessApp(tb.Window):

    def __init__(self):
        super().__init__(themename="darkly")
        self.title("AI Chess — By SouRav Bhattacharya")
        self.resizable(False, False)
        self.geometry("1200x900")
        self.minsize(1200, 900)
        self.maxsize(1200, 900)

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.example.Chessai")

        try:
            self.iconbitmap(resource_path(r"icons/icon.ico"))

        except:
            pass
        self.data_dir = os.path.join(os.path.expanduser("~"), ".ChessAI")
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_file = os.path.join(self.data_dir, "config.ini")
        self.board = chess.Board()
        self.move_history = []
        self.selected_sq = None
        self.legal_squares = set()
        self.engine_available = False
        self.ai_enabled = True
        self.human_color = chess.WHITE
        self.ai_thinking = False
        self.use_stockfish = False
        self.stockfish_path = None
        self.search_depth = tk.IntVar(value=2)
        self.has_saved_game = False
        self.start_frame = None
        self._try_load_stockfish()
        self.load_window_geometry()
        self.load_game_state()

        if self.has_saved_game:
            self.show_start_options()
        else:
            self._build_ui()
            self._render_board()
            self.after(100, self._maybe_ai_move_on_start)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_start_options(self):
        self.start_frame = tb.Frame(self)
        self.start_frame.pack(fill='both', expand=True)

        try:
            bg_img_path = resource_path(os.path.join("icons", "chess_bg.png"))
            bg_img = Image.open(bg_img_path)
            bg_img = bg_img.resize((self.winfo_width(), self.winfo_height()), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_img)

        except Exception as e:
            print(f"Error loading start background: {e}")
            self.bg_photo = None

        if self.bg_photo:
            bg_label = tb.Label(self.start_frame, image=self.bg_photo)
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        title = tb.Label(self.start_frame, text="Chess Game",
                        background="#0E0E0F" ,
                        foreground="white",
                        font=('Arial', 30, 'bold'))
        title.pack(pady=(50, 20))
        continue_btn = tb.Button(self.start_frame, text="Continue Saved Game",
                                command=self.continue_game,
                                bootstyle="success",
                                width=18)
        continue_btn.pack(pady=10)
        restart_btn = tb.Button(self.start_frame, text="Start New Game",
                                command=self.start_new_game,
                                bootstyle="primary",
                                width=18)
        restart_btn.pack(pady=10)

    def show_game_over_ui(self, result: str):

        if hasattr(self, "game_over_frame") and self.game_over_frame.winfo_exists():
            return
        self.game_over_frame = tb.Frame(self)
        self.game_over_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        try:
            bg_img_path = resource_path(os.path.join("icons", "chess_bg.png"))
            bg_img = Image.open(bg_img_path)
            bg_img = bg_img.resize((self.winfo_width(), self.winfo_height()), Image.LANCZOS)
            self.game_over_bg_photo = ImageTk.PhotoImage(bg_img)

        except Exception as e:
            print(f"Error loading game over background: {e}")
            self.game_over_bg_photo = None

        if self.game_over_bg_photo:
            bg_label = tb.Label(self.game_over_frame, image=self.game_over_bg_photo)
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg_label.lower()
        tb.Label(self.game_over_frame, text="Game Over",
                font=("Arial", 36, "bold"),
                background="#0E0E0F",
                foreground="white",
                bootstyle="inverse-dark").pack(pady=(50,0))
        tb.Label(self.game_over_frame, text=result,
                font=("Arial", 24, "bold"),
                foreground="white",
                background="#0E0E0F",
                bootstyle="success").pack(pady=5)
        tb.Button(self.game_over_frame, text="Start New Game",
                bootstyle="primary",
                command=lambda: [self.game_over_frame.destroy(), self.new_game()]).pack(pady=5)

    def continue_game(self):
        self.start_frame.destroy()
        self._build_ui()
        self._render_board()
        self.after(100, self._maybe_ai_move_on_start)

    def start_new_game(self):
        self.save_game_state(clear=True)
        self.board = chess.Board()
        self.move_history = []
        self.start_frame.destroy()
        self._build_ui()
        self._render_board()
        self.after(100, self._maybe_ai_move_on_start)

    def load_game_state(self):

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)

            if "GameState" in config:

                try:
                    fen = config["GameState"].get("fen", chess.STARTING_FEN)
                    self.board = chess.Board(fen)
                    moves_uci = config["GameState"].get("moves", "").split()
                    self.move_history = [chess.Move.from_uci(move) for move in moves_uci]
                    self.human_color = chess.WHITE if config["GameState"].get("human_color", "white") == "white" else chess.BLACK
                    self.ai_enabled = config["GameState"].getboolean("ai_enabled", True)
                    self.search_depth.set(config["GameState"].getint("search_depth", 3))
                    self.has_saved_game = True

                except Exception as e:
                    print(f"Error loading game state: {e}")
                    self.has_saved_game = False

    def save_game_state(self, clear=False):
        config = configparser.ConfigParser()

        if os.path.exists(self.config_file):
            config.read(self.config_file)

        if clear:

            if "GameState" in config:
                config.remove_section("GameState")
        else:

            if not config.has_section("GameState"):
                config.add_section("GameState")
            config["GameState"]["fen"] = self.board.fen()
            config["GameState"]["moves"] = " ".join(move.uci() for move in self.move_history)
            config["GameState"]["human_color"] = "white" if self.human_color == chess.WHITE else "black"
            config["GameState"]["ai_enabled"] = str(self.ai_enabled)
            difficulty = config["GameState"].get("difficulty", "Medium")
            self.difficulty_var = tk.StringVar(value=difficulty)
            self.on_difficulty_change()
            config["GameState"]["difficulty"] = self.difficulty_var.get()

        if not config.has_section("Geometry"):
            config.add_section("Geometry")
        config["Geometry"]["size"] = self.geometry()
        config["Geometry"]["state"] = self.state()

        with open(self.config_file, "w") as f:
            config.write(f)

    def _try_load_stockfish(self):
        path = None
        for p in COMMON_STOCKFISH_PATHS:

            if not p:
                continue

            try:
                engine = chess.engine.SimpleEngine.popen_uci(p)
                engine.quit()
                path = p
                break

            except Exception:
                continue

        if path:
            self.use_stockfish = True
            self.stockfish_path = path
            self.engine_available = True

    def _build_ui(self):
        ctrl = tb.Frame(self)
        ctrl.pack(side='top', fill='x', padx=10, pady=8)
        new_btn = tb.Button(ctrl,
                            text="New Game",
                            command=self.new_game,
                            bootstyle="success",
                            width=12)
        new_btn.pack(side='left', padx=6)
        self.ai_toggle_btn = tb.Button(ctrl,
                                      text="Disable AI" if self.ai_enabled else "Enable AI",
                                      command=self.toggle_ai,
                                      bootstyle="primary",
                                      width=12)
        self.ai_toggle_btn.pack(side='left', padx=6)
        tb.Label(ctrl, text="Play as:", font=('Arial', 12)).pack(side='left', padx=(12, 4))
        self.side_var = tk.StringVar(value='White' if self.human_color == chess.WHITE else 'Black')
        side_choice = tb.Combobox(ctrl, textvariable=self.side_var, values=['White', 'Black'], width=7,
                                font=('Segoe UI', 10), state='readonly', bootstyle="secondary")
        side_choice.pack(side='left', padx=4)
        side_choice.bind("<<ComboboxSelected>>", self.on_side_change)
        tb.Label(ctrl, text="Difficulty:", font=('Arial', 12)).pack(side='left', padx=(12, 4))
        self.difficulty_var = tk.StringVar(value="Medium")
        difficulty_choice = tb.Combobox(ctrl, textvariable=self.difficulty_var,
                                        values=["Easy", "Medium", "Hard"],
                                        width=8, state="readonly",
                                        font=('Segoe UI', 10), bootstyle="secondary")
        difficulty_choice.pack(side='left', padx=4)
        difficulty_choice.bind("<<ComboboxSelected>>", self.on_difficulty_change)
        tb.Label(ctrl, text="(Stockfish if found)", foreground="gray",
                font=('Arial', 10), bootstyle="darkly").pack(side='left', padx=(6, 0))
        self.piece_images = {}
        pieces = {
            "P": "white_pawn.png", "R": "white_rook.png", "N": "white_knight.png", "B": "white_bishop.png", "Q": "white_queen.png", "K": "white_king.png",
            "p": "black_pawn.png", "r": "black_rook.png", "n": "black_knight.png", "b": "black_bishop.png", "q": "black_queen.png", "k": "black_king.png",
        }
        for symbol, filename in pieces.items():

            try:
                img = Image.open(resource_path(os.path.join("icons", filename))).resize((50, 50), Image.LANCZOS)
                self.piece_images[symbol] = ImageTk.PhotoImage(img)

            except Exception as e:
                print(f"Error loading {filename}: {e}")
        board_frame = tb.Frame(self)
        board_frame.pack(side='left', padx=12, pady=8)
        self.board_canvas = tk.Canvas(board_frame, width=8*SQUARE_SIZE, height=8*SQUARE_SIZE, highlightthickness=0)
        self.board_canvas.pack()
        self.squares = {}
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)
                x1, y1 = c*SQUARE_SIZE, r*SQUARE_SIZE
                x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
                color = LIGHT_COLOR if (r+c)%2==0 else DARK_COLOR
                rect = self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='')
                self.squares[sq] = rect
        self.board_canvas.bind("<Button-1>", self.on_canvas_click)
        right = tb.Frame(self, width=350)
        right.pack(side='right', fill='y', padx=(0, 12), pady=8)
        right.pack_propagate(False)
        self.status_label = tb.Label(right, text='Ready —     ', foreground="white",
                                     background="#222222",
                font=('arial', 12), anchor='w', justify='left', bootstyle="darkly")
        self.status_label.pack(fill='x', padx=6, pady=(0, 6))
        tb.Label(right, text='Moves', foreground="white", font=('Times New Roman', 25), bootstyle="darkly").pack(anchor='center', padx=6)
        text_frame = tb.Frame(right)
        text_frame.pack(fill='both', expand=True, padx=6, pady=4)
        scrollbar = tb.Scrollbar(text_frame, bootstyle="round",)
        scrollbar.pack(side='right', fill='y')
        self.moves_text = tk.Text(text_frame, width=70, height=50, bg='#111217', fg='white',
                                 state='disabled', font=('arial', 18), yscrollcommand=scrollbar.set)
        self.moves_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.moves_text.yview)
        scrollbar.bind("<Enter>", lambda e: scrollbar.configure(bootstyle="info-round"))
        scrollbar.bind("<Leave>", lambda e: scrollbar.configure(bootstyle="round"))
        self.moves_text.bind("<Enter>", lambda e: scrollbar.configure(bootstyle="info-round"))
        self.moves_text.bind("<Leave>", lambda e: scrollbar.configure(bootstyle="round"))
        engine_label = tb.Label(right, text=f"Engine: {'Stockfish' if self.engine_available else 'Fallback'}",
                               font=('arial', 12), bootstyle="inverse-dark")
        engine_label.pack(anchor='w', padx=6, pady=(6, 0))

    def on_difficulty_change(self, event=None):
        mapping = {"Easy": 1, "Medium": 2, "Hard": 3}
        choice = self.difficulty_var.get()
        self.search_depth.set(mapping.get(choice, 2))

    def _render_board(self):
        for sq, rect in self.squares.items():
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            color = LIGHT_COLOR if (file + rank) % 2 == 0 else DARK_COLOR
            self.board_canvas.itemconfig(rect, fill=color)

        if self.selected_sq is not None:
            self.board_canvas.itemconfig(self.squares[self.selected_sq], fill=HIGHLIGHT_COLOR)
            for lm in self.legal_squares:
                self.board_canvas.itemconfig(self.squares[lm], fill=LEGAL_MOVE_COLOR)
        self.board_canvas.delete("piece")
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)

            if piece:
                symbol = piece.symbol()

                if symbol in self.piece_images:
                    x = (chess.square_file(sq) + 0.5) * SQUARE_SIZE
                    y = (7 - chess.square_rank(sq) + 0.5) * SQUARE_SIZE
                    self.board_canvas.create_image(x, y, image=self.piece_images[symbol], tags="piece")
        self._update_move_list()
        turn_color = "White" if self.board.turn == chess.WHITE else "Black"
        self.status_label.config(text=f"Ready —        {turn_color} to move")

        if hasattr(self, "status_label_color_canvas"):
            self.status_label_color_canvas.destroy()
        self.status_label_color_canvas = tk.Canvas(self.status_label, width=24, height=24,bg="#0E0E0F", highlightthickness=0)
        self.status_label_color_canvas.place(x=95, y=5)
        circle_color = "white" if turn_color == "White" else "black"
        self.status_label_color_canvas.create_oval(2, 2, 22, 22, fill=circle_color, outline="black")

        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.status_label.config(text=f"Checkmate — {winner} wins")
            self.show_game_over_ui(f"Checkmate! {winner} Wins!")
        elif self.board.is_stalemate():
            self.status_label.config(text="Stalemate — draw")
            self.show_game_over_ui("Stalemate! It's a Draw")
        elif self.board.is_insufficient_material():
            self.status_label.config(text="Draw — insufficient material")
            self.show_game_over_ui("Draw! Insufficient Material")
        elif self.board.can_claim_threefold_repetition():
            self.status_label.config(text="Draw — threefold repetition")
            self.show_game_over_ui("Draw! Threefold Repetition")
        elif self.board.can_claim_fifty_moves():
            self.status_label.config(text="Draw — fifty-move rule")
            self.show_game_over_ui("Draw! Fifty-Move Rule")

    def on_canvas_click(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        sq = chess.square(col, 7-row)
        self.on_square_click(sq)

    def on_square_click(self, sq):

        if self.ai_thinking:
            return
        piece = self.board.piece_at(sq)

        if self.selected_sq is None:

            if piece and (piece.color==self.human_color or not self.ai_enabled):
                self.selected_sq = sq
                self.legal_squares = {m.to_square for m in self.board.legal_moves if m.from_square==sq}
        else:
            move = chess.Move(self.selected_sq, sq)

            if self.board.piece_type_at(self.selected_sq)==chess.PAWN and chess.square_rank(sq) in (0,7):

                if chess.Move(self.selected_sq, sq, promotion=chess.QUEEN) in self.board.legal_moves:
                    move = chess.Move(self.selected_sq, sq, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self._push_move(move)
                self.selected_sq = None
                self.legal_squares = set()
                self._render_board()

                if self.ai_enabled and not self.board.is_game_over():
                    self.after(100, self._ai_move_async)
            else:

                if piece and piece.color==self.human_color:
                    self.selected_sq = sq
                    self.legal_squares = {m.to_square for m in self.board.legal_moves if m.from_square==sq}
                else:
                    self.selected_sq = None
                    self.legal_squares = set()
        self._render_board()

    def _push_move(self, move: chess.Move):

        try:
            self.board.push(move)
            self.move_history.append(move)

        except Exception as e:
            print("Invalid move push:", e)

    def _ai_move_async(self):

        if self.ai_thinking or self.board.is_game_over():
            return
        self.ai_thinking = True
        t = threading.Thread(target=self._ai_move_worker, daemon=True)
        t.start()

    def _ai_move_worker(self):

        try:

            if self.use_stockfish and self.engine_available:

                try:
                    engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                    depth = max(1, int(self.search_depth.get()))
                    limit = chess.engine.Limit(depth=depth)
                    result = engine.play(self.board, limit)
                    engine.quit()
                    move = result.move

                except Exception as e:
                    print("Stockfish error, falling back:", e)
                    move = find_best_move_negamax(self.board, depth=self.search_depth.get())
            else:
                move = find_best_move_negamax(self.board, depth=self.search_depth.get())

        except Exception as e:
            print("AI exception:", e)
            move = None

        def final():

            if move:
                self._push_move(move)
            self.ai_thinking = False
            self._render_board()
        self.after(10, final)

    def _maybe_ai_move_on_start(self):

        if self.ai_enabled and self.human_color==chess.BLACK and not self.board.is_game_over():
            self._ai_move_async()

    def _update_move_list(self):
        san_list = []
        temp_board = chess.Board()
        for mv in self.move_history:
            san_list.append(temp_board.san(mv))
            temp_board.push(mv)
        lines = []
        i = 0

        while i < len(san_list):
            move_no = (i // 2) + 1

            if i + 1 < len(san_list):
                lines.append(f"{move_no}. {san_list[i]} {san_list[i+1]}")
            else:
                lines.append(f"{move_no}. {san_list[i]}")
            i += 2
        self.moves_text.config(state='normal')
        self.moves_text.delete('1.0', tk.END)
        self.moves_text.insert(tk.END, "\n".join(lines))
        self.moves_text.config(state='disabled')
        self.moves_text.see(tk.END)

    def new_game(self):

        if self.ai_thinking:
            messagebox.showinfo("Please wait", "AI is thinking. Try again shortly.")
            return
        self.board.reset()
        self.move_history.clear()
        self.selected_sq = None
        self.legal_squares = set()
        self._render_board()
        self.after(100, self._maybe_ai_move_on_start)

    def toggle_ai(self):
        self.ai_enabled = not self.ai_enabled
        self.ai_toggle_btn.config(text="Disable AI" if self.ai_enabled else "Enable AI")

        if self.ai_enabled and self.board.turn != self.human_color and not self.board.is_game_over():
            self.after(100, self._ai_move_async)

    def on_side_change(self, event):
        val = self.side_var.get()
        self.human_color = chess.WHITE if val=='White' else chess.BLACK
        self.new_game()

    def on_closing(self):
        self.save_game_state()
        self.save_window_geometry()
        self.destroy()

    def load_window_geometry(self):

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)

            if "Geometry" in config:
                geometry = config["Geometry"].get("size", "")
                state = config["Geometry"].get("state", "normal")

                if geometry:
                    self.geometry(geometry)
                    self.update_idletasks()
                    self.update()

                if state == "zoomed":
                    self.state("zoomed")
                elif state == "iconic":
                    self.iconify()

    def save_window_geometry(self):
        config = configparser.ConfigParser()

        if os.path.exists(self.config_file):
            config.read(self.config_file)

        if not config.has_section("Geometry"):
            config.add_section("Geometry")
        config["Geometry"]["size"] = self.geometry()
        config["Geometry"]["state"] = self.state()

        with open(self.config_file, "w") as f:
            config.write(f)

if __name__ == "__main__":
    app = ChessApp()
    app.mainloop()
