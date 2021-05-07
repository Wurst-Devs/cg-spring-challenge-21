import sys
from types import GeneratorType

MAX_DAY = 23 # WOOD 2 => 0 / WOOD 1 => 5 / ONWARD => 23
ALLOWED = [
    "GROW",  # WOOD 1
    "SEED",  # BRONZE
]

def debug(*values, end = '\n'):
    values = [tuple(v) if isinstance(v, GeneratorType) else v for v in values]
    print(*values, file=sys.stderr, end=end, flush=True)

# CLASSES

class Cell:
    def __init__(self, *args):
        self.id = int(args[0])
        self.richness = int(args[1])
        self.neighbors_raw = map(int, args[2:])
        self.neighbors = [None for _ in range(6)]
        self.tree = None
        self.shadow = 0
        self.next_shadow = 0
    
    def __repr__(self):
        return f"@{self.id}({self.richness},{self.shadow})"
    
    def init(self, cells):
        self.neighbors = [cells[i] if i >= 0 else None for i in self.neighbors_raw]
    
    @property
    def has_tree(self):
        return self.tree is not None

    def reset(self):
        self.tree = None
        self.shadow = 0
        self.next_shadow = 0
    
    def update(self, sun_dir, tree):
        self.tree = tree
        remaining = tree.size
        target = self.neighbors[sun_dir]
        while target is not None and remaining > 0:
            target.shadow = max(target.shadow, tree.size)
            target = target.neighbors[sun_dir]
            remaining -= 1
        remaining = tree.size
        target = self.neighbors[(sun_dir + 1) % 6]
        while target is not None and remaining > 0:
            target.next_shadow = max(target.next_shadow, tree.size)
            target = target.neighbors[(sun_dir + 1) % 6]
            remaining -= 1
    
    def area(self, size, included):
        if size < 0:
            return []
        output = []
        for neighbor in self.neighbors:
            if neighbor is not None and neighbor not in included:
                included += [neighbor]
                output += [neighbor] + neighbor.area(size - 1, included)
        return output


class Tree:
    count = {i:0 for i in range(4)}
    nutrients = 20

    def reset_count():
        Tree.count = {i:0 for i in range(4)}

    def __init__(self, cells, last_trees, turn_start, sun_dir, *args):
        self.id = int(args[0])
        self.cell = cells[self.id]
        self.size = int(args[1])
        self.is_mine = args[2] == "1"
        self.is_dormant = args[3] == "1"
        if self.is_mine:
            Tree.count[self.size] += 1
        self.cell.update(sun_dir, self)
        self.__seedable = None
        old_self = [tree for tree in last_trees if tree.id == self.id]
        if len(old_self) == 0:
            self.history = [self.size]
        elif turn_start:
            self.history = old_self[0].history + [self.size]
        else:
            self.history = old_self[0].history
            
        
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
        return self.cell.richness + (self.size + 1) * 10
    
    @property
    def days(self):
        return self.history.count(self.size)
    
    @property
    def max_days(self):
        return (3 - self.cell.richness) * 4 + 1

    @property
    def next_sun(self):
        return self.size if self.cell.next_shadow < self.size else 0
    
    @property
    def seedable(self):
        if self.__seedable is None:
            if self.size == 0:
                self.__seedable = []
            else:
                area = self.cell.area(self.size, [])
                self.__seedable = sorted(
                    (cell for cell in area if not cell.has_tree and cell.richness > 0),
                    key=lambda cell:cell.richness,
                    reverse=True
                )
        return self.__seedable
    
    @property
    def can_seed(self):
        return self.size > 0 and len(self.seedable) > 0



# INIT

cells = [Cell(*input().split()) for _ in range(int(input()))]

for cell in cells:
    cell.init(cells)

day = -1
trees = []

# GAME LOOP
while True:
    last_day = day
    day = int(input())
    turn_start = day != last_day

    sun_dir = day % 6

    Tree.reset_count()
    Tree.nutrients = int(input())

    debug("nutrients:", Tree.nutrients)

    sun, score = [int(i) for i in input().split()]
    opp_sun, opp_score, opp_is_waiting = map(int, input().split())

    for cell in cells:
        cell.reset()
    
    last_trees = trees
    trees = [Tree(cells, last_trees, turn_start, sun_dir, *input().split()) for _ in range(int(input()))]

    [input() for _ in range(int(input()))]  # possible actions ignored

    mine = [tree for tree in trees if tree.is_mine]
    available = [tree for tree in mine if not tree.is_dormant]
    dormant = [tree for tree in mine if tree.is_dormant]

    debug("mine", mine)

    # complete

    completable = [tree for tree in available if tree.size == 3 and (tree.days > tree.max_days or day == MAX_DAY)]
    completable.sort(key=lambda tree:tree.score, reverse=True)

    debug("completable", completable)

    # grow

    growable = [tree for tree in available if tree.size != 3 and sun >= tree.price]
    growable.sort(key=lambda tree:tree.gscore, reverse=True)

    debug("growable", growable)

    # seed

    seeding = [tree for tree in available if tree.can_seed]
    seeding.sort(key=lambda tree:tree.seedable[0].richness, reverse=True)

    debug("seeding", seeding)

    if len(completable) > 0 and sun >= 4:
        print("COMPLETE", completable[0].id)
    elif "GROW" in ALLOWED and day != MAX_DAY and len(growable) > 0:
        print("GROW", growable[0].id)
    elif "SEED" in ALLOWED and day != MAX_DAY and len(seeding) > 0 and sun >= Tree.count[0]:
        print("SEED", seeding[0].id, seeding[0].seedable[0].id)
    else:
        # GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>
        print("WAIT", "würst")
