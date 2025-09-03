
## Core Features

1. **Chess Engine Integration**:
   - Primary engine: Stockfish (automatically detected from common installation paths)
   - Fallback engine: Custom negamax algorithm with basic piece-value evaluation
   - Adjustable difficulty levels (depth 1-3)

2. **User Interface**:
   - Graphical chess board with piece images
   - Move history panel
   - Game controls (new game, AI toggle, side selection)
   - Status information and turn indicators
   - Start screen with continue/new game options
   - Game over screen with result display

3. **Game Management**:
   - Persistent game state saving/loading
   - Window geometry preservation
   - Configurable human player side (white/black)
   - AI opponent toggle

## Technical Implementation

- **Framework**: Built with tkinter for the GUI
- **Chess Library**: python-chess for game logic
- **Image Handling**: PIL/Pillow for piece graphics
- **Platform Support**: Windows-specific app ID setting
- **Resource Management**: PyInstaller-compatible resource loading

## Key Components

1. **ChessApp Class**: Main application class handling:
   - UI construction and rendering
   - Game state management
   - User input handling
   - AI move generation

2. **Board Representation**:
   - 8×8 grid with alternating light/dark squares
   - Visual highlights for selected pieces and legal moves
   - Piece images for all chess pieces

3. **AI Implementation**:
   - Multi-threaded AI thinking to prevent UI freezing
   - Fallback to negamax algorithm if Stockfish unavailable
   - Depth-limited search based on difficulty setting

## Usage Flow

1. Application starts with option to continue saved game or start new
2. Human player makes moves by clicking pieces and destination squares
3. AI automatically moves when it's computer's turn (if enabled)
4. Game state is automatically saved when closing
5. Game over conditions are detected and displayed

## Additional Features

- Promotion handling (automatically to queen)
- All standard chess rules enforcement
- Visual feedback for game state (check, checkmate, draws)
- Responsive UI with game state indicators




The application provides a complete chess experience with a competent AI opponent, persistent game saving, and an intuitive graphical interface.

# Demo video
https://github.com/user-attachments/assets/0e0c877d-e411-4cb9-9104-c70763e19df7

