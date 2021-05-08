import sys
from types import GeneratorType
from typing import List
from collections import defaultdict

MAX_DAY = 23

MAX_TREE_DAYS = {1:MAX_DAY, 2:10, 3:1}

# UTILS

def debug(*values, end = '\n'):
    print(*values, file=sys.stderr, end=end, flush=True)

# CLASSES

class Cell:
    def __init__(self, *args: str):
        self.id = int(args[0])
        self.richness = int(args[1])
        self.neighbors_raw = map(int, args[2:])
        self.neighbors = [None for _ in range(6)]
        self.tree = None
        self.shadow = 0
        self.next_shadow = 0
    
    def __repr__(self) -> str:
        return f"@{self.id}({self.richness},{self.shadow})"
    
    def init(self, cells: List["Cell"]):
        self.neighbors = [cells[i] if i >= 0 else None for i in self.neighbors_raw]
    
    @property
    def has_tree(self) -> bool:
        return self.tree is not None

    def reset(self):
        self.tree = None
        self.shadow = 0
        self.next_shadow = 0
    
    def update(self, sun_dir: int, tree: "Tree"):
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
    
    def area(self, size: int, included: List["Cell"]) -> List["Cell"]:
        if size == 0:
            return []
        output = []
        for neighbor in self.neighbors:
            if neighbor is not None and neighbor not in included:
                included += [neighbor]
                output += [neighbor] + neighbor.area(size - 1, included)
        return output


class Tree:
    def __init__(self, cells: List[Cell], last_trees: List["Tree"], turn_start: bool, sun_dir: int, *args: str):
        self.id = int(args[0])
        self.cell = cells[self.id]
        self.size = int(args[1])
        self.is_mine = args[2] == "1"
        self.is_dormant = args[3] == "1"
        self.cell.update(sun_dir, self)
        self.__seedable = None
        old_self = [tree for tree in last_trees if tree.id == self.id]
        if len(old_self) == 0:
            self.history = [self.size]
        elif turn_start:
            self.history = old_self[0].history + [self.size]
        else:
            self.history = old_self[0].history
            
        
    def __repr__(self) -> str:
        if self.size == 3:
            return f"T{self.cell}=>{self.size}"
        else:
            return f"T{self.cell}=>{self.size}/{self.gscore}"

    @property
    def gscore(self) -> int:
        return self.cell.richness + (self.size + 1) * 10
    
    @property
    def grown(self) -> bool:
        return self.size == 3

    @property
    def days(self) -> int:
        return self.history.count(self.size)
    
    @property
    def max_days(self) -> int:
        return (3 - self.cell.richness) * 4 + 1 #MAX_TREE_DAYS[self.cell.richness]

    @property
    def next_sun(self) -> int:
        return self.size if self.cell.next_shadow < self.size else 0
    
    @property
    def seedable(self) -> List[Cell]:
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
    def can_seed(self) -> bool:
        return self.size > 0 and len(self.seedable) > 0


class Game:
    def __init__(self):
        self.day = -1
        self.trees = []
    
    def input_cells(self, raw_cells: List[List[str]]):
        self.cells = [Cell(*line) for line in raw_cells]
        for cell in self.cells:
            cell.init(self.cells)
    
    def input_turn_start(self, day: int, nutrients: int):
        self.turn_start = day != self.day
        self.day = day
        self.sun_dir = day % 6
        self.nutrients = nutrients
        debug("nutrients", nutrients)
    
    def input_player(self, *args: List[str]):
        self.sun, self.score = map(int, args)
    
    def input_opponent(self, *args: List[str]):
        self.opp_sun, self.opp_score, self.opp_is_waiting = map(int, args)
        self.opp_is_waiting = self.opp_is_waiting == 1

    def input_trees(self, raw_trees: List[List[str]]):
        for cell in self.cells:
            cell.reset()
        last_trees = self.trees
        self.trees = [Tree(self.cells, last_trees, self.turn_start, self.sun_dir, *line) for line in raw_trees]
        self.tree_count = defaultdict(lambda:0)
        for tree in self.trees:
            self.tree_count[tree.size] += 1
    
    def price(self, tree: Tree):
        return pow(2, tree.size + 1) - 1 + self.tree_count[tree.size + 1]

    def output_move(self):
        if self.turn_start:
            self.grow_count = 0
            self.seed_count = 0

        mine = [tree for tree in self.trees if tree.is_mine]
        available = [tree for tree in mine if not tree.is_dormant]

        # complete

        completable = [tree for tree in available if tree.grown and (tree.days > tree.max_days or self.day == MAX_DAY)]
        completable.sort(key=lambda tree:tree.cell.richness, reverse=True)

        debug("completable", completable)

        if len(completable) > 0 and self.sun >= 4:
            return "COMPLETE", completable[0].id

        if self.day != MAX_DAY:
            if self.grow_count < 5:
                # grow

                growable = [tree for tree in available if not tree.grown and self.sun >= self.price(tree)]
                growable.sort(key=lambda tree:tree.gscore, reverse=True)

                debug("growable", growable)

                if len(growable) > 0:
                    self.grow_count += 1
                    return "GROW", growable[0].id

            if self.seed_count < 3 and self.day > 0:
                # seed

                seeding = [tree for tree in available if tree.can_seed]
                seeding.sort(key=lambda tree:tree.seedable[0].richness, reverse=True)

                debug("seeding", seeding)

                if len(seeding) > 0 and self.sun >= self.tree_count[0]:
                    self.seed_count += 1
                    return "SEED", seeding[0].id, seeding[0].seedable[0].id

        return "WAIT", "würst"



# INIT

game = Game()

game.input_cells(input().split() for _ in range(int(input())))

# GAME LOOP
while True:
    game.input_turn_start(int(input()), int(input()))
    game.input_player(*input().split())
    game.input_opponent(*input().split())
    game.input_trees(input().split() for _ in range(int(input())))
    [input() for _ in range(int(input()))]  # possible actions ignored
    print(*game.output_move())
