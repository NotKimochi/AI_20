import pygame
import random
import time
from copy import deepcopy

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

# Pygame setup
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Number Merging Game")

font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

class GameState:
    def __init__(self, total_points, numbers_list):
        self.total_points = total_points
        self.numbers_list = numbers_list
        self.last_ai_move = None
        self.winner = None
        self.last_move_details = []
        self.ai_thoughts = []

    def clone(self):
        """Create a deep copy of the current state."""
        return GameState(self.total_points, self.numbers_list.copy())

    def evaluate_heuristic(self):
        """Improved heuristic that values both merges and strategic removals"""
        self.ai_thoughts = []
        score = 0
        
        # Base score from points
        points_score = 2 * self.total_points
        score += points_score
        self.ai_thoughts.append(f"Base points: {points_score}")
        
        # Value having options
        possible_moves = len(self.get_possible_moves())
        options_score = 1 * possible_moves
        score += options_score
        self.ai_thoughts.append(f"Move options: {options_score} ({possible_moves} moves available)")
        
        # Parity strategy
        parity_importance = 1 + (10 / len(self.numbers_list))
        parity_match = sum(1 for num in self.numbers_list 
                         if num % 2 == self.total_points % 2)
        parity_score = parity_importance * parity_match
        score += parity_score
        self.ai_thoughts.append(f"Parity match: {parity_score:.1f} ({parity_match} numbers match current parity)")
        
        # Removal bonus calculation
        removal_bonus = 0
        for i in range(len(self.numbers_list)):
            temp_state = self.clone()
            temp_state.make_move(i, "remove")
            new_parity = sum(1 for num in temp_state.numbers_list
                           if num % 2 == temp_state.total_points % 2)
            if new_parity > parity_match:
                removal_bonus += 2
                self.ai_thoughts.append(f"Good removal at {i} would improve parity")
        score += removal_bonus
        
        # Terminal state evaluation
        if len(self.numbers_list) == 1:
            final_num = self.numbers_list[0]
            if (final_num % 2) == (self.total_points % 2):
                term_score = 100 if (final_num % 2 == 0) else 80
                score += term_score
                self.ai_thoughts.append(f"Terminal win score: +{term_score}")
            else:
                score -= 100
                self.ai_thoughts.append("Terminal lose score: -100")
        
        # Progress penalty
        progress_penalty = 0.5 * len(self.numbers_list)
        score -= progress_penalty
        self.ai_thoughts.append(f"Progress penalty: -{progress_penalty:.1f} ({len(self.numbers_list)} numbers)")
        
        self.ai_thoughts.append(f"TOTAL SCORE: {score:.1f}")
        return score

    def make_move(self, index, move_type):
        """Execute a move and return a description."""
        if self.winner:
            return None

        description = ""
        details = []
        if move_type == "merge" and index < len(self.numbers_list) - 1:
            num1, num2 = self.numbers_list[index], self.numbers_list[index + 1]
            new_sum = (num1 + num2) if (num1 + num2) <= 6 else (num1 + num2 - 6)
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
        self.last_ai_move = description
        self.last_move_details = details
        return description

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
            moves.append(("remove", i))
        
        return moves

    def minimax(self, depth, maximizing_player, alpha=float('-inf'), beta=float('inf')):
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or self.winner:
            return self.evaluate_heuristic(), None
        
        best_move = None
        if maximizing_player:
            max_eval = float('-inf')
            for move in self.get_possible_moves():
                new_state = self.clone()
                new_state.make_move(move[1], move[0])
                evaluation, _ = new_state.minimax(depth-1, False, alpha, beta)
                
                if evaluation > max_eval:
                    max_eval = evaluation
                    best_move = move
                
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in self.get_possible_moves():
                new_state = self.clone()
                new_state.make_move(move[1], move[0])
                evaluation, _ = new_state.minimax(depth-1, True, alpha, beta)
                
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_move = move
                
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            
            return min_eval, best_move

    def ai_move(self):
        """Improved AI that considers both merges and removes strategically."""
        if self.winner:
            return
        
        self.ai_thoughts = ["AI is thinking..."]
        
        # First check if any remove would immediately win the game
        for i in range(len(self.numbers_list)):
            temp_state = self.clone()
            temp_state.make_move(i, "remove")
            if temp_state.winner and "AI Wins" in temp_state.winner:
                self.ai_thoughts.append(f"Found winning removal at position {i}!")
                self.make_move(i, "remove")
                return
        
        # Otherwise use minimax with depth 3
        self.ai_thoughts.append("Evaluating possible moves...")
        _, best_move = self.minimax(3, True)
        
        if best_move:
            move_type, index = best_move
            self.ai_thoughts.append(f"Best move: {move_type} at {index}")
            self.make_move(index, move_type)

    def check_winner(self):
        """Determine the winner when one number remains."""
        if len(self.numbers_list) == 1:
            final_num = self.numbers_list[0]
            if final_num % 2 == self.total_points % 2:
                self.winner = "Player Wins!" if final_num % 2 == 0 else "AI Wins!"
            else:
                self.winner = "It's a Draw!"

# Initialize the game
initial_length = random.randint(15, 25)
starting_numbers = [random.randint(1, 6) for _ in range(initial_length)]
game_state = GameState(total_points=0, numbers_list=starting_numbers)
player_turn = True
selected_index = None

def draw_game():
    """Draw the game state on the screen."""
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

    # AI thinking process
    if not player_turn and game_state.ai_thoughts:
        pygame.draw.rect(screen, COLORS['black'], (WIDTH - 300, 60, 290, 80), 1)
        for i, thought in enumerate(game_state.ai_thoughts[-3:]):  # Show last 3 thoughts
            thought_text = small_font.render(thought, True, COLORS['blue'])
            screen.blit(thought_text, (WIDTH - 290, 70 + i * 20))

    # Action buttons
    pygame.draw.rect(screen, COLORS['red'], (WIDTH // 2 - 100, HEIGHT - 100, 80, 40))
    pygame.draw.rect(screen, COLORS['green'], (WIDTH // 2 + 20, HEIGHT - 100, 80, 40))
    screen.blit(font.render("Remove", True, COLORS['white']), (WIDTH // 2 - 90, HEIGHT - 90))
    screen.blit(font.render("Merge", True, COLORS['white']), (WIDTH // 2 + 30, HEIGHT - 90))

    pygame.display.flip()

running = True
while running:
    draw_game()
    
    # AI's turn
    if not player_turn and not game_state.winner:
        pygame.time.delay(500)  # Small delay so player can see AI's move
        game_state.ai_move()
        player_turn = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

        if event.type == pygame.MOUSEBUTTONDOWN and player_turn and not game_state.winner:
            x, y = pygame.mouse.get_pos()

            # Select a number
            button_spacing = min(BUTTON_SIZE, (screen.get_width() - 2*PADDING) // max(1, len(game_state.numbers_list)))
            for i in range(len(game_state.numbers_list)):
                btn_x = PADDING + i * button_spacing
                btn_y = HEIGHT // 2
                if btn_x <= x <= btn_x + BUTTON_SIZE and btn_y <= y <= btn_y + BUTTON_SIZE:
                    selected_index = i

            # Check action buttons
            if selected_index is not None:
                if WIDTH // 2 - 100 <= x <= WIDTH // 2 - 20 and HEIGHT - 100 <= y <= HEIGHT - 60:
                    game_state.make_move(selected_index, "remove")
                    player_turn = False
                    selected_index = None

                elif WIDTH // 2 + 20 <= x <= WIDTH // 2 + 100 and HEIGHT - 100 <= y <= HEIGHT - 60:
                    game_state.make_move(selected_index, "merge")
                    player_turn = False
                    selected_index = None

pygame.quit()