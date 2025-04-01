# AI_20

# Number String Game

## Description
This project implements a turn-based number string game where players manipulate a string of numbers according to specific rules until only one number remains. The outcome is determined by the final number and the total points accumulated during gameplay.

## Game Rules

### Setup
- At the beginning of the game, the human player specifies the length of the number string (between 15 and 25 numbers).
- The game software randomly generates a string of numbers (each between 1 and 6) of the specified length.
- Total points start at 0.
- A game bank is initialized at 0.

### Gameplay
Players take turns performing one of the following actions:

1. **Add Pair of Numbers**:
   - Select a pair of adjacent numbers (first with second, third with fourth, etc.)
   - Replace them with their sum (with special substitutions if sum > 6):
     - 7 = 1
     - 8 = 2
     - 9 = 3
     - 10 = 4
     - 11 = 5
     - 12 = 6
   - Add 1 point to the total score

2. **Delete Unpaired Number**:
   - Remove a number that remains unpaired
   - Subtract 1 point from the total score

### Game End
The game ends when only one number remains in the string. The final evaluation is:
1. The bank is added to the total points
2. The winner is determined by:
   - If both the final number AND total points are EVEN: First player wins
   - If both the final number AND total points are ODD: Second player wins
   - All other cases: Draw

## Requirements
- Python 3.x (recommended)
- Random number generation capability

## How to Run
1. Clone this repository
2. Run the main game script
3. Follow on-screen instructions to specify string length and play the game

## Contributors
NotKimochi - ZHANG Julien 250AEB054
