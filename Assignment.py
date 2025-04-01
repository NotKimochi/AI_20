"""
What we need to do :

Additional software requirements 

At the beginning of the game, the human player indicates the length of the string of numbers to be used in the game,
which may be in the range of 15 to 25 numbers. The game software randomly generates a string of numbers according to the 
specified length, including numbers from 1 to 6. 

Game description 

At the beginning of the game, the generated string of numbers is given. Players take turns. 
The total number of points is 0 (points are not counted for each player individually).
A game bank is used and initially it is equal to 0. During a turn, a player may:  

add a pair of numbers (first with second, third with fourth, fifth with sixth, etc.) and write the sum in the
place of the pair of numbers added 
(if the sum is greater than 6, substitutions are made: 7 = 1, 8 = 2, 9 = 3, 10 = 4, 11 = 5, 12 = 6),
and add 1 point to the total score, or  

delete a number left unpaired and subtract one point from the total score.  

The game ends when one number remains in the number string. At the end of the game, the bank is 
added to the total number of points. If both the number left in the number string and the total number of points
are even numbers, the player who started the game wins. If both the number in the number string and the total 
number of points is an odd number, the second player wins. In all other cases, the result is a draw. 
"""

import pygame
import random
import json
from datetime import datetime
from copy import deepcopy
import math
import os
import time
from collections import defaultdict

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 600
BUTTON_SIZE = 60
PADDING = 10
COLORS = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (200, 50, 50),
    'green': (50, 200, 50),
    'blue': (50, 50, 200),
    'orange': (255, 165, 0),
    'purple': (128, 0, 128)
}

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Number Merging Game")

# Font setup
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

ai_mode = 'minimax'  # Default AI mode

class GameNode:
    """Class to represent nodes in the game tree"""
    def __init__(self, move=None, state=None, parent=None):
        self.move = move  # (action, index)
        self.state = state  # GameState snapshot
        self.parent = parent
        self.children = []
        self.depth = parent.depth + 1 if parent else 0
        self.heuristic = 0

    def to_dict(self):
        """Convert node to dictionary for storage"""
        return {
            'move': self.move,
            'state': {
                'numbers': self.state.numbers_list if self.state else [],
                'points': self.state.total_points if self.state else 0,
                'winner': self.state.winner if self.state else None
            },
            'heuristic': self.heuristic,
            'depth': self.depth,
            'children_count': len(self.children)
        }

class GameTree:
    """Class to manage the game tree storage"""
    def __init__(self):
        self.root = None
        self.current_node = None
        self.game_id = None
        self.initial_state_hash = None
    
    def start_new_game(self, initial_state):
        """Initialize tree with starting state"""
        # Create hash of initial state for filename
        self.initial_state_hash = hash(tuple(initial_state.numbers_list))
        self.game_id = f"game_{self.initial_state_hash}"
        
        # Try to load existing tree
        filename = f"{self.game_id}.json"
        try:
            with open(filename, 'r') as f:
                tree_data = json.load(f)
                self.root = self._dict_to_node(tree_data)
                self.current_node = self.root
                print(f"Loaded existing game tree from {filename}")
        except (FileNotFoundError, json.JSONDecodeError):
            self.root = GameNode(state=initial_state.clone())
            self.current_node = self.root
            print(f"Created new game tree {filename}")

    def _dict_to_node(self, node_dict):
        """Recursively convert dictionary to node"""
        if not node_dict:
            return None
            
        node = GameNode(
            move=node_dict['move'],
            state=GameState(
                node_dict['state']['points'],
                node_dict['state']['numbers']
            ),
            parent=None
        )
        node.heuristic = node_dict['heuristic']
        node.depth = node_dict['depth']
        
        # Rebuild children recursively
        node.children = [self._dict_to_node(child) for child in node_dict['children']]
        for child in node.children:
            child.parent = node
            
        return node

    def add_node(self, move, state):
        """Add a new node to the tree"""
        if not self.current_node:
            return
        
        new_node = GameNode(move=move, state=state.clone(), parent=self.current_node)
        self.current_node.children.append(new_node)
        self.current_node = new_node
    
    def save_tree(self):
        """Save the game tree to a JSON file"""
        if not self.root:
            return
        
        filename = f"{self.game_id}.json"
        tree_dict = self._node_to_dict(self.root)
        
        with open(filename, 'w') as f:
            json.dump(tree_dict, f, indent=2)
        print(f"Game tree saved to {filename}")
    
    def _node_to_dict(self, node):
        """Recursively convert tree to dictionary"""
        if not node:
            return None
        
        node_dict = node.to_dict()
        node_dict['children'] = [self._node_to_dict(child) for child in node.children]
        return node_dict

class GameState:
    def __init__(self, total_points, numbers_list):
        self.total_points = total_points
        self.numbers_list = numbers_list
        self.last_ai_move = None
        self.winner = None
        self.last_move_details = []
        self.ai_thoughts = []
        self.starting_player = 1  # 1 for human, 2 for AI

    def clone(self):
        """Create a deep copy of the current state."""
        new_state = GameState(self.total_points, self.numbers_list.copy())
        new_state.winner = self.winner
        new_state.starting_player = self.starting_player
        return new_state

    def make_move(self, index, move_type):
        """Execute a move and return a description."""
        if self.winner:
            return None

        description = ""
        details = []
        if move_type == "merge" and index < len(self.numbers_list) - 1:
            num1, num2 = self.numbers_list[index], self.numbers_list[index + 1]
            new_sum = (num1 + num2) % 6 or 6  # Handles wrap-around (7=1, 8=2, etc.)
            self.numbers_list[index] = new_sum
            del self.numbers_list[index + 1]
            self.total_points += 1
            description = f"Merged {num1}+{num2}→{new_sum} at {index}"
            details = [
                f"Position: {index}",
                f"Numbers: {num1} and {num2}",
                f"New value: {new_sum}",
                f"Points gained: +1",
                f"Total points: {self.total_points}"
            ]
        
        elif move_type == "remove" and index < len(self.numbers_list):
            removed = self.numbers_list.pop(index)
            self.total_points -= 1
            description = f"Removed {removed} at {index}"
            details = [
                f"Position: {index}",
                f"Number removed: {removed}",
                f"Points lost: -1",
                f"Total points: {self.total_points}"
            ]
        
        self.check_winner()
        self.last_move_details = details
        return description

    def check_winner(self):
        """Determine the winner when one number remains."""
        if len(self.numbers_list) == 1:
            final_num = self.numbers_list[0]
            if (final_num % 2 == self.total_points % 2):
                if (final_num % 2 == 0 and self.starting_player == 1) or \
                   (final_num % 2 == 1 and self.starting_player == 2):
                    self.winner = "Player Wins!"
                else:
                    self.winner = "AI Wins!"
            else:
                self.winner = "It's a Draw!"

    def get_possible_moves(self):
        """Return all valid moves as (move_type, index) pairs."""
        if self.winner:
            return []
        
        moves = []
        # All possible merges (can only merge adjacent pairs)
        for i in range(len(self.numbers_list) - 1):
            moves.append(("merge", i))
        
        # All possible removes
        for i in range(len(self.numbers_list)):
            # Prevent removing the last number (game would end)
            if len(self.numbers_list) > 1:
                moves.append(("remove", i))
        
        return moves

    def evaluate_heuristic(self):
        """Heuristic evaluation of the board state"""
        self.ai_thoughts = []
        score = 0
        
        # Terminal state evaluation
        if len(self.numbers_list) == 1:
            final_num = self.numbers_list[0]
            if (final_num % 2 == self.total_points % 2):
                if (final_num % 2 == 0 and self.starting_player == 1) or \
                   (final_num % 2 == 1 and self.starting_player == 2):
                    score += 1000  # AI wins
                    self.ai_thoughts.append("Terminal state: AI wins!")
                else:
                    score -= 1000  # Player wins
                    self.ai_thoughts.append("Terminal state: Player wins!")
            else:
                score = 0  # Draw
                self.ai_thoughts.append("Terminal state: Draw")
            return score
        
        # Points score (positive is good for AI)
        score += 2 * self.total_points
        self.ai_thoughts.append(f"Points score: {2 * self.total_points}")
        
        # Number of possible moves (more options is better)
        possible_moves = len(self.get_possible_moves())
        score += 0.5 * possible_moves
        self.ai_thoughts.append(f"Move options: {0.5 * possible_moves}")
        
        # Parity strategy
        current_parity = self.total_points % 2
        matching_numbers = sum(1 for num in self.numbers_list if num % 2 == current_parity)
        parity_score = 1.5 * matching_numbers
        score += parity_score
        self.ai_thoughts.append(f"Parity score: {parity_score} ({matching_numbers} matching)")
        
        self.ai_thoughts.append(f"Total heuristic score: {score}")
        return score

    def minimax(self, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or self.winner:
            return self.evaluate_heuristic(), None
        
        best_move = None
        if maximizing_player:
            max_eval = -math.inf
            for move in self.get_possible_moves():
                new_state = self.clone()
                new_state.make_move(move[1], move[0])
                evaluation, _ = new_state.minimax(depth-1, alpha, beta, False)
                
                if evaluation > max_eval:
                    max_eval = evaluation
                    best_move = move
                
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in self.get_possible_moves():
                new_state = self.clone()
                new_state.make_move(move[1], move[0])
                evaluation, _ = new_state.minimax(depth-1, alpha, beta, True)
                
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_move = move
                
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            
            return min_eval, best_move

    def ai_move(self):
        """AI makes a move using the current strategy."""
        if self.winner:
            return
        
        self.ai_thoughts = ["AI is thinking..."]
        
        if ai_mode == 'minimax':
            # Use iterative deepening for better move selection
            best_move = None
            for depth in range(1, 5):  # Search up to depth 4
                _, current_move = self.minimax(depth, -math.inf, math.inf, True)
                if current_move:
                    best_move = current_move
                    self.ai_thoughts.append(f"Depth {depth}: Best move {best_move}")

        
        if best_move:
            move_type, index = best_move
            self.ai_thoughts.append(f"Selected move: {move_type} at {index}")
            self.make_move(index, move_type)
            self.last_ai_move = f"AI did: {move_type} at position {index}"

def draw_game():
    """Draw the game state on the screen (without tree visualization)"""
    screen.fill(COLORS['white'])
    
    # Draw numbers board
    num_count = len(game_state.numbers_list)
    available_width = screen.get_width() - (2 * PADDING)
    button_spacing = min(BUTTON_SIZE, available_width // max(1, num_count))

    for i, num in enumerate(game_state.numbers_list):
        x = PADDING + i * button_spacing
        y = HEIGHT // 2
        color = COLORS['green'] if i == selected_index else COLORS['blue']
        pygame.draw.rect(screen, color, (x, y, BUTTON_SIZE, BUTTON_SIZE))
        text = font.render(str(num), True, COLORS['white'])
        screen.blit(text, (x + BUTTON_SIZE // 3, y + BUTTON_SIZE // 3))

    # Game info panel
    pygame.draw.rect(screen, COLORS['black'], (0, 0, WIDTH, 150), 2)
    
    # Score and turn info
    score_text = font.render(f"Points: {game_state.total_points}", True, COLORS['black'])
    screen.blit(score_text, (20, 20))

    if game_state.winner:
        turn_text = font.render(game_state.winner, True, COLORS['red'])
    else:
        turn_text = font.render("Your Turn" if player_turn else "AI Thinking...", 
                              True, COLORS['green'] if player_turn else COLORS['red'])
    screen.blit(turn_text, (WIDTH - 200, 20))

    # Last AI move
    if game_state.last_ai_move:
        move_text = font.render(f"Last AI Move: {game_state.last_ai_move}", True, COLORS['orange'])
        screen.blit(move_text, (20, 60))
        
        # Detailed move info
        for i, detail in enumerate(game_state.last_move_details):
            detail_text = small_font.render(detail, True, COLORS['purple'])
            screen.blit(detail_text, (20, 90 + i * 20))

    # Action buttons
    pygame.draw.rect(screen, COLORS['red'], (WIDTH // 2 - 100, HEIGHT - 100, 80, 40))
    pygame.draw.rect(screen, COLORS['green'], (WIDTH // 2 + 20, HEIGHT - 100, 80, 40))
    screen.blit(font.render("Remove", True, COLORS['white']), (WIDTH // 2 - 90, HEIGHT - 90))
    screen.blit(font.render("Merge", True, COLORS['white']), (WIDTH // 2 + 30, HEIGHT - 90))

    # Restart button (visible when game ends)
    if game_state.winner:
        pygame.draw.rect(screen, COLORS['purple'], (WIDTH // 2 - 60, HEIGHT - 50, 120, 40))
        screen.blit(font.render("Restart", True, COLORS['white']), (WIDTH // 2 - 50, HEIGHT - 40))

    # AI mode toggle button
    pygame.draw.rect(screen, COLORS['orange'], (WIDTH - 150, HEIGHT - 50, 140, 40))
    mode_text = font.render(f"AI: {ai_mode}", True, COLORS['white'])
    screen.blit(mode_text, (WIDTH - 140, HEIGHT - 40))

    pygame.display.flip()

def initialize_game():
    """Initialize a new game"""
    global game_state, player_turn, selected_index, game_tree
    
    initial_length = random.randint(15, 25)
    starting_numbers = [random.randint(1, 6) for _ in range(initial_length)]
    game_state = GameState(total_points=0, numbers_list=starting_numbers)
    player_turn = True  # Player goes first
    selected_index = None
    
    # Initialize game tree
    game_tree.start_new_game(game_state)

# Initialize the game and tree
game_tree = GameTree()
initialize_game()

running = True
while running:
    draw_game()
    
    # AI's turn
    if not player_turn and not game_state.winner:
        pygame.time.delay(500)  # Small delay so player can see AI's move
        game_state.ai_move()
        
        # Record AI move in game tree
        if game_state.last_ai_move:
            last_action = game_state.last_move_details[0].split(":")[0].lower()
            last_index = int(game_state.last_move_details[0].split(":")[1].strip())
            game_tree.add_node((last_action, last_index), game_state)
        
        player_turn = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_tree.save_tree()  # Save tree before quitting
            running = False
        
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            
            # Handle restart button click
            if game_state.winner and \
               WIDTH // 2 - 60 <= x <= WIDTH // 2 + 60 and \
               HEIGHT - 50 <= y <= HEIGHT - 10:
                game_tree.save_tree()  # Save current tree
                initialize_game()  # Start new game
                continue
            
            if player_turn and not game_state.winner:
                # Select a number
                button_spacing = min(BUTTON_SIZE, (screen.get_width() - 2*PADDING) // max(1, len(game_state.numbers_list)))
                for i in range(len(game_state.numbers_list)):
                    btn_x = PADDING + i * button_spacing
                    btn_y = HEIGHT // 2
                    if btn_x <= x <= btn_x + BUTTON_SIZE and btn_y <= y <= btn_y + BUTTON_SIZE:
                        selected_index = i

                # Check action buttons
                if selected_index is not None:
                    # Remove action
                    if WIDTH // 2 - 100 <= x <= WIDTH // 2 - 20 and HEIGHT - 100 <= y <= HEIGHT - 60:
                        if len(game_state.numbers_list) > 1:  # Prevent removing last number
                            prev_state = game_state.clone()
                            game_state.make_move(selected_index, "remove")
                            player_turn = False
                            # Record move in game tree
                            game_tree.add_node(("remove", selected_index), prev_state)
                            selected_index = None

                    # Merge action
                    elif WIDTH // 2 + 20 <= x <= WIDTH // 2 + 100 and HEIGHT - 100 <= y <= HEIGHT - 60:
                        if selected_index < len(game_state.numbers_list) - 1:  # Must have pair
                            prev_state = game_state.clone()
                            game_state.make_move(selected_index, "merge")
                            player_turn = False
                            # Record move in game tree
                            game_tree.add_node(("merge", selected_index), prev_state)
                            selected_index = None

pygame.quit()