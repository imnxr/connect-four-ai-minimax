# Connect Four AI

A polished Connect Four game built with Python and Pygame, featuring an AI opponent powered by the Minimax algorithm with Alpha-Beta pruning and heuristic evaluation.

This project was created as an Artificial Intelligence course project to demonstrate game search, decision-making, and interactive game development in a clean and playable desktop application.

## Author

**M. Mansoor Ur Rehman**

## Features

- Human vs AI Connect Four gameplay
- AI move selection using Minimax
- Alpha-Beta pruning for faster search
- Heuristic board evaluation for strategic play
- Three difficulty levels: Easy, Medium, and Hard
- Clean minimalist Pygame-based interface
- Sound toggle with move, win, loss, and draw effects
- Session scoreboard for wins, losses, and draws
- Win, loss, and draw detection
- Public-shareable desktop project structure

## Technologies Used

- Python 3
- Pygame Community Edition (`pygame-ce`)
- Minimax Algorithm
- Alpha-Beta Pruning
- Heuristic Evaluation Function

## Project Structure

```text
Connect Four/
+-- connect_four.py
+-- requirements.txt
+-- run_game.bat
+-- LICENSE
+-- README.md
+-- .gitignore
```

## Installation

### Option 1: Quick Run

Double-click `run_game.bat`

### Option 2: Run From Terminal

```powershell
python -m pip install -r requirements.txt
python connect_four.py
```

## How to Play

1. Run the game.
2. Click a column on the board to drop your piece.
3. Try to connect four pieces in a row horizontally, vertically, or diagonally.
4. The AI will automatically play its move after your turn.
5. Use the difficulty buttons on the right panel to switch between Easy, Medium, and Hard.
6. Use `New Match` to start a fresh round at any time.
7. Track your performance with the scoreboard on the right side.

## Controls

- Mouse click: Drop a piece in a column
- `N`: Start a new match
- `1`: Easy difficulty
- `2`: Medium difficulty
- `3`: Hard difficulty
- `Sound: On/Off`: Enable or disable game sounds

## AI Overview

The AI uses:

- **Minimax** to search possible future game states
- **Alpha-Beta pruning** to skip branches that cannot improve the result
- **Heuristic evaluation** to score non-terminal positions based on board control, threats, and opportunities

Difficulty levels are created by adjusting the search depth and evaluation behavior.

## Why This Project

This project demonstrates practical AI concepts in a classic two-player strategy game. It combines algorithmic decision-making with game interface design to create a complete playable application that is simple to run and easy to understand.

## Open Source

This repository is public and available for anyone to explore, use, and learn from under the MIT License.

## License

This project is released under the MIT License, so it is free to use, share, and learn from.
