import sys
from types import GeneratorType
from functools import reduce

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
        self.neighbors = []
    
    def __repr__(self):
        return f"@{self.id}({self.richness})"
    
    def init(self, cells):
        self.neighbors = [cells[i] for i in self.neighbors_raw]

class Tree:
    count = {i:0 for i in range(4)}
    nutrients = 20

    def reset_count():
        Tree.count = {i:0 for i in range(4)}

    def __init__(self, cells, *args):
        self.id = int(args[0])
        self.cell = cells[self.id] # location of this tree
        #self.cell.tree = self
        self.size = int(args[1]) # size of this tree: 0-3
        self.is_mine = args[2] == "1" # 1 if this is your tree
        self.is_dormant = args[3] == "1" # 1 if this tree is dormant
        if self.is_mine:
            Tree.count[self.size] += 1
    
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
        if self.size == 1:
            return 3 + Tree.count[2]
        elif self.size == 2:
            return 7 + Tree.count[3]
        else:
            return 0
    
    @property
    def gscore(self):
        return self.cell.richness * (self.size + 1)

# INIT

cells = [Cell(*input().split()) for _ in range(int(input()))]

for cell in cells:
    cell.init(cells)

MAX_DAY = 5

# GAME LOOP
while True:
    day = int(input())  # the game lasts 24 days: 0-23
    
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

    trees = [Tree(cells, *input().split()) for _ in range(int(input()))]

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
    elif day != MAX_DAY and len(growable) > 0 and len(dormant) == 0 and not should_not_grow:
        print("GROW", growable[0].id)
    else:
        # GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>
        print("WAIT", "würst")
