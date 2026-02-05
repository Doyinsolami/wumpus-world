import importlib.util
import time
import sys
import pygame
from envs.gridworld import GridWorld
import os

# Define colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
BLACK = (0, 0, 0)

CELL_SIZE = 50  # pixels
MARGIN = 2      # pixels between cells


def load_agent_from_file(filepath):
    """Dynamically import the Agent class from a .py file"""
    agent_dir = os.path.dirname(os.path.abspath(filepath))
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)

    spec = importlib.util.spec_from_file_location("student_agent", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Agent()


def draw_grid(screen, game,font):
    screen.fill(BLACK)
    rows, cols = game.grid_size
    #font = pygame.font.SysFont(None, 24)

    for row in range(rows):
        for col in range(cols):
            color = GRAY  # Default cell
            text = ""

            if [row, col] == game.flag_pos:
                color = RED
                text = "F"
            elif [row, col] == game.agent1_pos:
                color = GREEN
                text = "A1"
            elif [row, col] == game.agent2_pos:
                color = BLUE
                text = "A2"
            elif (row, col) in game.walls:
                color = BLACK

            rect = pygame.Rect(
                col * (CELL_SIZE + MARGIN),
                row * (CELL_SIZE + MARGIN),
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, color, rect)
            
            # Draw text if needed
            if text:
                text_surface = font.render(text, True, BLACK)  # Text color
                text_rect = text_surface.get_rect(center=rect.center)
                screen.blit(text_surface, text_rect)
            
            # --- Draw Score and Turn Info ---
            info_text = f"Turn: {game.turns} | Score A1: {game.scores[1]} | Score A2: {game.scores[2]}"
            text_surface = font.render(info_text, True, WHITE)
            screen.blit(text_surface, (10, rows * (CELL_SIZE + MARGIN) + 10))


def run_match(agent1_path, agent2_path, visualize):
    agent1 = load_agent_from_file(agent1_path)
    agent2 = load_agent_from_file(agent2_path)

    game = GridWorld()
    state = game.get_state()

    if visualize:
        pygame.init()
        pygame.font.init()
        font = pygame.font.SysFont("Arial", 24)
        rows, cols = game.grid_size
        screen_width = cols * (CELL_SIZE + MARGIN)
        #screen_height = rows * (CELL_SIZE + MARGIN)
        screen_height = rows * (CELL_SIZE + MARGIN) + 60  # extra space for text
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("GridWorld Visualization")

        # Try to give focus to the Pygame window
        try:
            import pygetwindow as gw
            import pyautogui
            time.sleep(0.3)  # Give time for window to initialize
            win = gw.getWindowsWithTitle("GridWorld Visualization")[0]
            win.activate()
            win.restore()
            pyautogui.click(win.left + 10, win.top + 10)  # Click to focus
        except Exception as e:
            print("Could not focus window:", e)

        clock = pygame.time.Clock()
        draw_grid(screen, game,font)
        pygame.display.flip()
        clock.tick(5)

    while not game.is_game_over():
        state = game.get_state()

        if game.turn == 0:
            state['adjacent_info'] = game.get_adjacent_info(game.agent1_pos, 1)
        else:
            state['adjacent_info'] = game.get_adjacent_info(game.agent2_pos, 2)
        
        if game.turn == 0:
            state['agent2_pos'] = [-1, -1]
            state['flag_pos'] = [-1, -1]
            action = agent1.get_action(state, 1)
            if visualize:
                print(f"Agent 1 Action: {action}")
            game.apply_action(1, action)
        else:
            state['agent1_pos'] = [-1, -1]
            state['flag_pos'] = [-1, -1]
            action = agent2.get_action(state, 2)
            if visualize:
                print(f"Agent 2 Action: {action}")
            game.apply_action(2, action)

        if visualize:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            draw_grid(screen, game,font)
            pygame.display.flip()
            clock.tick(5)

        game.switch_turn()
    print(game.game_end_reason)
    
    if visualize:
        time.sleep(5)
        pygame.quit()

    #if game.agent1_pos == game.flag_pos:
    #    print("Agent 1 wins!")
    #elif game.agent2_pos == game.flag_pos:
    #    print("Agent 2 wins!")
    #else:
    #    print("Max Turns!")

    print(f"Final Scores: Agent 1: {game.scores[1]}, Agent 2: {game.scores[2]}, Turns: {game.turns}")
    return game.scores


def main(agent1path, agent2path, visualize, battles):
    if battles == 1:
        run_match(agent1path, agent2path, visualize)
    else:
        agent1score = 0
        agent2score = 0
        for i in range(battles):
            scores = run_match(agent1path, agent2path, visualize)
            agent1score += scores[1]
            agent2score += scores[2]
        print(f"Average Scores: Agent 1: {agent1score / battles}, Agent 2: {agent2score / battles}")
        print(f"Total Scores: Agent 1: {agent1score}, Agent 2: {agent2score}")


if __name__ == "__main__":
    agent1path = "./agents/random_agent.py"
    #agent1path = "./agents/student_agent.py"
    agent2path = "./agents/random_agent.py"
    #agent2path = "./agents/student_agent_BFS.py"
    
    visualize = True
    battles = 1
    main(agent1path, agent2path, visualize, battles)











