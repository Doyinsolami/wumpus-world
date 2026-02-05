from base_agent import Agent
import random

class Agent(Agent):
    def __init__(self):
        super().__init__()

    def get_action(self, state, agent_id):
        # Identify self and opponent
        if agent_id == 1:
            my_pos = tuple(state['agent1_pos'])
        else:
            my_pos = tuple(state['agent2_pos'])

        # Fallback to random move if search is exhausted
        return random.choice(['up', 'down', 'left', 'right','stay'])
