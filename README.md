# ChessAI Game

A feature-rich chess application with AI opponent built using Python and Tkinter. This application offers both a fallback chess engine and Stockfish integration for advanced gameplay.

## Features

- **Dual AI System**: Uses Stockfish engine when available, with fallback to custom negamax algorithm
- **Game State Management**: Save and resume games automatically
- **Customizable Settings**: Adjust AI difficulty and choose which color to play
- **Visual Highlights**: Legal moves and selected pieces are clearly highlighted
- **Game History**: Complete move history displayed in sidebar
- **Responsive UI**: Clean interface with game state indicators
- **Game Over Screens**: Special screens for different game outcomes

## Requirements

- Python 3.7+
- Required packages: 
  - chess
  - pillow (PIL)
  - ttkbootstrap
  - configparser

## Installation

1. Clone or download the project files
2. Install required packages:
   ```
   pip install chess pillow ttkbootstrap configparser
   ```
3. (Optional) Install Stockfish for enhanced AI:
   - Windows: Download from [stockfishchess.org](https://stockfishchess.org/)
   - Linux: `sudo apt install stockfish`

## How to Use

1. Run `main.py` to start the application
2. Choose to continue a saved game or start a new one
3. Select your preferred color (white or black)
4. Adjust AI difficulty using the dropdown (1-3)
5. Click on pieces to move them (legal moves will be highlighted)
6. Use the toggle to enable/disable AI opponent

## File Structure

- `main.py` - Main application file
- `icons/` - Directory containing piece images and application icon
- `~/.FolderLock&Hide/config.ini` - Configuration and save file location

## Notes

- The application automatically saves your game state when closed
- If Stockfish is not found, the built-in negamax algorithm will be used
- Promotion moves are automatically set to Queen

## License

This project is created by SouRav Bhattacharya.

# Demo video
https://github.com/user-attachments/assets/0e0c877d-e411-4cb9-9104-c70763e19df7

