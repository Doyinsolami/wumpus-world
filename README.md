🧠 Intelligent Wumpus World Agent

An interactive Wumpus World simulator implemented in Python using pygame.  
The project features an intelligent agent that reasons from percepts, plans safe paths, and attempts to retrieve gold while avoiding hazards.


🚀 Features
- Procedurally generated 4×4 Wumpus World with random pits, gold, and a Wumpus
- Full Wumpus World ruleset including breeze, stench, glitter, bump, and scream
- Scoring system based on classic Wumpus World performance measures
- Intelligent agent that:
  - Maintains internal state of visited, safe, and risky cells
  - Infers pit and Wumpus locations from percepts
  - Plans movement using Breadth-First Search (BFS) over safe tiles
  - Balances exploration with risk when no guaranteed safe move exists
  - Shoots the Wumpus when there is a clear and justified line of sight
- Live pygame visualization with:
  - Colored and labeled cells
  - Animated agent movement
  - HUD showing score, arrow status, gold possession, and terminal state

🎨 Visual Legend
- Green triangle: Agent (direction shows where it is facing)
- Yellow circle: Gold
- Red: Wumpus
- Gray: Pit
- Blue dot: Breeze (adjacent to a pit)
- Purple dot: Stench (adjacent to the Wumpus)


🧩 Controls
| Key | Action |
|----|-------|
| R | Reset world |
| N | Step agent once |
| A | Run agent automatically |
| Q | Quit |

## ⚙️ How to Run

Install dependencies:
```bash
pip install pygame
```
Run the simulator:
```bash
python wumpus.py
```
#### Acknowledgements
Developed by Doyinsola Oduwole

AI debugging and algorithm refinement assisted by ChatGPT


