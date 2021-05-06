import sys
from types import GeneratorType
from functools import reduce

MAX_DAY = 23 # WOOD 2 => 0 / WOOD 1 => 5
ALLOWED = [
    "GROW",  # WOOD 1
    "SEED",  # BRONZE
]

def debug(*values, name = None, end = '\n'):
    values = [tuple(v) if isinstance(v, GeneratorType) else v for v in values]
    if name is not None:
        print(f"{name} =", *values, file=sys.stderr, end=end, flush=True)
    else:
        print(*values, file=sys.stderr, end=end, flush=True)
    if len(values) == 1:
        return values[0]
    return tuple(values)

# CLASSES

class Cell:
    def __init__(self, *args):
        # index: 0 is the center cell, the next cells spiral outwards
        # richness: 0 if the cell is unusable, 1-3 for usable cells
        # neigh_0: the index of the neighbouring cell for each direction
        self.id = int(args[0])
        self.richness = int(args[1])
        self.neighbors_raw = map(int, args[2:])
        self.neighbors = [None for _ in range(6)]
        self.tree = None
        self.shadow = 0
    
    def __repr__(self):
        return f"@{self.id}({self.richness},{self.shadow})"
    
    def init(self, cells):
        self.neighbors = [cells[i] if i >= 0 else None for i in self.neighbors_raw]
    
    def reset(self):
        self.tree = None
        self.shadow = 0
    
    def update(self, sun_dir, tree):
        self.tree = tree
        remaining = tree.size
        target = self.neighbors[sun_dir]
        while target is not None and remaining > 0:
            target.shadow = max(target.shadow, tree.size)
            target = target.neighbors[sun_dir]
            remaining -= 1


class Tree:
    count = {i:0 for i in range(4)}
    nutrients = 20

    def reset_count():
        Tree.count = {i:0 for i in range(4)}

    def __init__(self, cells, sun_dir, *args):
        self.id = int(args[0])
        self.cell = cells[self.id] # location of this tree
        self.size = int(args[1]) # size of this tree: 0-3
        self.is_mine = args[2] == "1" # 1 if this is your tree
        self.is_dormant = args[3] == "1" # 1 if this tree is dormant
        if self.is_mine:
            Tree.count[self.size] += 1
        self.cell.update(sun_dir, self)
        
    
    def __repr__(self):
        if self.size == 3:
            return f"T{self.cell}=>{self.size}/{self.score}"
        else:
            return f"T{self.cell}=>{self.size}/{self.score}/{self.price}/{self.gscore}"

    @property
    def score(self):
        return Tree.nutrients + 2 * (self.cell.richness - 1)
    
    @property
    def price(self):
        return pow(2, self.size + 1) - 1 + Tree.count[self.size + 1]

    @property
    def gscore(self):
        return self.cell.richness * (self.size + 1)
    
    @property
    def days(self):
        return self.history.count(self.size)



# INIT

cells = [Cell(*input().split()) for _ in range(int(input()))]

for cell in cells:
    cell.init(cells)

day = -1

# GAME LOOP
while True:
    last_day = day
    day = int(input())  # the game lasts 24 days: 0-23
    turn_start = day != last_day

    sun_dir = day % 6

    Tree.reset_count()
    Tree.nutrients = int(input())  # the base score you gain from the next COMPLETE action

    debug("nutrients:", Tree.nutrients)

    # sun: your sun points
    # score: your current score
    sun, score = [int(i) for i in input().split()]
    inputs = input().split()
    opp_sun = int(inputs[0])  # opponent's sun points
    opp_score = int(inputs[1])  # opponent's score
    opp_is_waiting = inputs[2] != "0"  # whether your opponent is asleep until the next day

    for cell in cells:
        cell.reset()

    trees = [Tree(cells, sun_dir, *input().split()) for _ in range(int(input()))]

    for cell in cells:
        if cell.shadow > 0:
            debug(cell)

    [input() for _ in range(int(input()))]

    mine = [tree for tree in trees if tree.is_mine]
    available = [tree for tree in mine if not tree.is_dormant]
    dormant = [tree for tree in mine if tree.is_dormant]

    debug("mine", mine)

    completable = [tree for tree in available if tree.size == 3]
    completable.sort(key=lambda tree:tree.score, reverse=True)

    growable = [tree for tree in available if tree.size != 3 and sun >= tree.price]
    growable.sort(key=lambda tree:tree.size, reverse=True)

    debug("growable", growable)

    next_sun = sun + sum([tree.size for tree in mine])

    growable_next = [tree for tree in mine if tree.size != 3 and next_sun >= tree.price]
    growable_next.sort(key=lambda tree:tree.gscore, reverse=True)

    debug("growable_next", next_sun, growable_next)

    should_not_grow = (
        len(growable_next) > 0 and len(growable) > 0 and
        growable_next[0].gscore > growable[0].gscore
    )

    if len(completable) > 0 and sun >= 4:
        print("COMPLETE", completable[0].id)
    elif "GROW" in ALLOWED and day != MAX_DAY and len(growable) > 0 and len(dormant) == 0 and not should_not_grow:
        print("GROW", growable[0].id)
    else:
        # GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>
        print("WAIT", "würst")
