import sys
from types import GeneratorType
from typing import List, Tuple
from collections import defaultdict

MAX_DAY = 23

MAX_SEEDS = 2
MAX_GROWN = 7
MIN_GROWN = 3
MAX_TREES = 9
MIN_UNSHADOWED = 2

# UTILS


def debug(*values, end='\n'):
    print(*values, file=sys.stderr, end=end, flush=True)


def tree_price(tree_count: List[int], size: int) -> int:
    return pow(2, size) - 1 + tree_count[size]

# CLASSES


class Cell:
    def __init__(self, *args: str):
        self.id = int(args[0])
        self.richness = int(args[1])
        self.neighbors_raw = map(int, args[2:])
        self.neighbors = [None for _ in range(6)]
        self.tree = None
        self.shadowable = [[None for _ in range(4)] for _ in range(6)]
        self.__seed_score_day = None
        self.__seed_score = None

    def __repr__(self) -> str:
        return f"@{self.id}({self.richness})"

    def init(self, cells: List["Cell"]):
        self.neighbors = [cells[i] if i >=
                          0 else None for i in self.neighbors_raw]
    
    def precompute(self):
        self.area = [self.compute_area(i, []) for i in range(4)]
        for sun_dir in range(6):
            remaining = 3
            target = self.neighbors[sun_dir]
            while target is not None and remaining > 0:
                self.shadowable[sun_dir][4-remaining] = target
                target = target.neighbors[sun_dir]
                remaining -= 1

    @property
    def has_tree(self) -> bool:
        return self.tree is not None

    def reset(self):
        self.tree = None

    def compute_area(self, size: int, included: List["Cell"]) -> List["Cell"]:
        if size == 0:
            return []
        output = []
        for neighbor in self.neighbors:
            if neighbor is not None and neighbor not in included:
                included += [neighbor]
                output += [neighbor] + \
                    neighbor.compute_area(size - 1, included)
        return output

    def shadowed_trees(self, sun_dir: int, size: int) -> List["Tree"]:
        return [
            cell.tree for cell in self.shadowable[sun_dir][:size + 1]
            if cell is not None and
            cell.has_tree and
            cell.tree.size <= size
        ]

    def shadow_source_trees(self, sun_dir: int, size: int) -> List["Tree"]:
        return [
            cell.tree for i, cell in enumerate(self.shadowable[(sun_dir + 3) % 6])
            if cell is not None and
            cell.has_tree and
            cell.tree.size >= i and
            cell.tree.size >= size
        ]

    def shadow_score(self, sun_dir: int, size: int = None, *, offset_own: int = 0, actors_impact: bool = False) -> Tuple[float, float]:
        if size == 0:
            return 0, 0
        own_score = 0
        opp_score = 0
        for tree in self.shadowed_trees(sun_dir, size):
            actors = tree.shadow_sources(sun_dir)
            if not self.has_tree or self.tree not in actors:
                actors += [self]
            impact_ratio = 1
            if actors_impact and len(actors) > 1:
                impact_ratio = 2  # len(actors)
            if tree.is_mine:
                own_score -= (tree.size + offset_own) / impact_ratio
            else:
                opp_score -= tree.size / impact_ratio
        return own_score, opp_score

    def seed_score(self, day: int, prefer_unshadowed: bool) -> float:
        # from kalioz code : _case_get_seed_value
        if self.__seed_score is None or self.__seed_score_day != day:
            score = self.richness

            shadow_score = 0
            for delta in range(2, 5):  # direct future
                own_score, opp_score = self.shadow_score(
                    (day + delta) % 6, delta - 1, offset_own=1)
                shadow_score += (own_score - opp_score) / (4 * delta)
            for delta in range(6):  # full turn
                own_score, opp_score = self.shadow_score(
                    delta, 3, offset_own=1)
                shadow_score += (own_score - opp_score) / (4 * 9)

            shadowed_score = 0
            for delta in range(2, 5):
                if len(self.shadow_source_trees((day + delta) % 6, 0)) > 0:  # shadowed
                    shadowed_score += 1 / delta

            bonus = 0
            if shadow_score == 0 and shadowed_score == 0:
                bonus = 3 if prefer_unshadowed else 1

            neighbors_score = 0
            for cell in self.neighbors:
                if cell is not None:
                    neighbors_score += max(cell.richness - 1, 0) / 12
                    if cell.has_tree:
                        if cell.tree.is_mine:
                            neighbors_score -= cell.tree.size * cell.richness
                        else:
                            neighbors_score += cell.tree.size * cell.richness

            score = self.richness + shadow_score / 2 - \
                shadowed_score + bonus + neighbors_score

            debug(self, "seed_score", score)

            self.__seed_score = self.richness + shadow_score / 2 - \
                shadowed_score + bonus + neighbors_score
            self.__seed_score_day = day
        return self.__seed_score


class Tree:
    def __init__(self, cells: List[Cell], last_trees: List["Tree"], turn_start: bool, sun_dir: int, *args: str):
        self.id = int(args[0])
        self.cell = cells[self.id]
        self.size = int(args[1])
        self.is_mine = args[2] == "1"
        self.is_dormant = args[3] == "1"
        self.cell.tree = self
        old_self = [tree for tree in last_trees if tree.id == self.id]
        if len(old_self) == 0:
            self.history = [self.size]
        elif turn_start:
            self.history = old_self[0].history + [self.size]
        else:
            self.history = old_self[0].history

    def __repr__(self) -> str:
        return f"T{self.cell}=>{'M' if self.is_mine else 'O'}{'D' if self.is_dormant else 'A'}{self.size}"

    @ property
    def grown(self) -> bool:
        return self.size == 3

    @ property
    def days(self) -> int:
        return self.history.count(self.size)

    def tree_points(self, nutrients: int) -> int:
        return nutrients + 2 * (self.cell.richness - 1)

    def seedable(self, size: int = None) -> List[Cell]:
        size = size if size is not None else self.size
        seeds = [
            cell for cell in self.cell.area[size]
            if not cell.has_tree and
            cell.richness > 0
        ]
        return seeds

    def sorted_seedable(self, day: int, prefer_unshadowed: bool) -> List[Cell]:
        seeds = self.seedable()
        return sorted(seeds, key=lambda cell: cell.seed_score(day,
                                                              prefer_unshadowed), reverse=True)

    @ property
    def can_seed(self):
        return self.size > 0 and len(self.seedable()) > 0

    def shadow_sources(self, sun_dir: int, size: int = None) -> List["Tree"]:
        size = size if size is not None else self.size
        return self.cell.shadow_source_trees(sun_dir, size)

    def shadowed(self, sun_dir: int, size: int = None) -> bool:
        size = size if size is not None else self.size
        return len(self.shadow_sources(sun_dir, size)) > 0

    def sun(self, sun_dir: int, size: int = None) -> int:
        size = size if size is not None else self.size
        return size if not self.shadowed(sun_dir, size) else 0

    def shadow_score(self, sun_dir: int, size: int = None) -> Tuple[float, float]:
        size = size if size is not None else self.size
        if size == 0:
            return 0, 0
        own_score, opp_score = self.cell.shadow_score(
            sun_dir, size, actors_impact=True)
        return (own_score + self.sun(sun_dir, size)), opp_score

    def range_shadow_score(self, start_day: int, delta_days: int, size: int = None) -> Tuple[float, float]:
        size = size if size is not None else self.size
        own_score, opp_score = 0, 0
        for day in range(start_day + 1, min(start_day + delta_days + 1, MAX_DAY + 1)):
            own_score_day, opp_score_day = self.shadow_score(day % 6, size)
            own_score += own_score_day
            opp_score += opp_score_day
        return own_score, opp_score

    def range_shadow_score_diff(self, start_day: int, delta_days: int) -> Tuple[float, float]:
        own_score0, opp_score0 = self.range_shadow_score(
            start_day, delta_days, self.size)
        own_score1, opp_score1 = self.range_shadow_score(
            start_day, delta_days, self.size + 1)
        return own_score1 - own_score0, opp_score1 - opp_score0

    def growth_seed_impact(self) -> float:
        # from kalioz code : impact_growth_tree_on_seedable_surfaces
        seedable0 = self.seedable()
        seedable1 = self.seedable(self.size + 1)
        richnesses = [
            cell.richness for cell in seedable1 if cell not in seedable0]
        if len(richnesses) == 0:
            return 0
        return sum(richnesses) / (3 * len(richnesses))

    def grow_score(self, day: int, tree_count: List[int]) -> float:
        # from kalioz code : find_tree_to_grow
        grow_cost = tree_price(tree_count, self.size + 1)

        own_diff, opp_diff = self.range_shadow_score_diff(day, 3)
        sun_score = own_diff - opp_diff - grow_cost

        debug(self, "sun_score", sun_score)

        impact = self.growth_seed_impact()

        debug(self, "impact", impact)

        score = sun_score + 2 * impact

        if day < 3:
            score += self.cell.richness
        elif tree_count[3] < MAX_GROWN:
            score += self.cell.richness * (self.size + 1) ** 2
        else:
            score += self.cell.richness * (self.size + 1)

        if self.shadowed((day + 1) % 6):
            score -= 2 * grow_cost

        debug(self, "grow_score", score)

        return score

    def complete_score(self, day: int, tree_count: List[int], nutrients: int, complete_shadowed: bool) -> float:
        # from kalioz code : find_tree_to_complete
        score = self.tree_points(nutrients)

        forecast = [None] + \
            [self.shadowed((day + delta) % 6) for delta in range(1, 4)]

        bonus = {1: 10, 2: 5, 3: 1}
        score += sum(bonus[delta] if forecast[delta]
                     else 0 for delta in range(1, 4))

        shadow_condition = False
        if tree_count[3] <= MIN_GROWN + 1:
            shadow_condition = all(forecast[1:])
        elif tree_count[3] >= MAX_GROWN - 1:
            shadow_condition = forecast[1]
        else:
            shadow_condition = forecast[1] + any(forecast[2:])

        debug(self, "complete_score", score)

        if not complete_shadowed or shadow_condition:
            return score
        else:
            return 0


class Game:
    def __init__(self):
        self.day = -1
        self.trees = []

    def input_cells(self, raw_cells: List[List[str]]):
        self.cells = [Cell(*line) for line in raw_cells]
        for cell in self.cells:
            cell.init(self.cells)
        for cell in self.cells:
            cell.precompute() 

    def input_turn_start(self, day: int, nutrients: int):
        self.turn_start = day != self.day
        self.day = day
        self.sun_dir = day % 6
        self.nutrients = nutrients
        debug("day", day)
        debug("nutrients", nutrients)

    def input_player(self, *args: List[str]):
        self.sun, self.score = map(int, args)
        debug("sun", self.sun)

    def input_opponent(self, *args: List[str]):
        self.opp_sun, self.opp_score, self.opp_is_waiting = map(int, args)
        self.opp_is_waiting = self.opp_is_waiting == 1

    def input_trees(self, raw_trees: List[List[str]]):
        for cell in self.cells:
            cell.reset()
        last_trees = self.trees
        self.trees = [Tree(self.cells, last_trees, self.turn_start,
                           self.sun_dir, *line) for line in raw_trees]
        self.tree_count = defaultdict(lambda: 0)
        for tree in self.trees:
            if tree.is_mine:
                self.tree_count[tree.size] += 1

    def best_complete(self, complete_shadowed: bool) -> Tree:
        if self.day < MAX_DAY and (
            # prevent cutting the last 3 tree
            len(self.mine) - self.tree_count[0] < 3 or
            # keep at least some fully grown trees
            self.tree_count[3] <= MIN_GROWN
        ):
            return None
        completable = [
            tree for tree in self.available
            if tree.grown
        ]
        completable.sort(key=lambda tree: tree.complete_score(
            self.day, self.tree_count, self.nutrients, complete_shadowed), reverse=True)
        debug("completable", completable)
        return completable[0] if len(completable) > 0 and completable[0].complete_score(
            self.day, self.tree_count, self.nutrients, complete_shadowed) > 0 else None

    def best_grow(self, min_size=0) -> Tree:
        growable = [
            tree for tree in self.available
            if not tree.grown and
            tree.size >= min_size and
            self.sun >= tree_price(self.tree_count, tree.size + 1)
        ]
        growable.sort(key=lambda tree: tree.grow_score(
            self.day, self.tree_count), reverse=True)
        debug("growable", growable)
        return growable[0] if len(growable) > 0 else None

    def best_seed(self, prefer_unshadowed: bool) -> Tuple[Tree, Cell]:
        # from kalioz code : find_case_to_seed
        seeders = [tree for tree in self.available if tree.can_seed]

        targets = [(tree, tree.sorted_seedable(self.day, prefer_unshadowed)[0])
                   for tree in seeders]

        targets.sort(key=lambda t: t[1].seed_score(
            self.day, prefer_unshadowed), reverse=True)

        return targets[0] if len(targets) > 0 and targets[0][1].seed_score(
            self.day, prefer_unshadowed) > 1.5 else None

    def output_move(self):
        if self.turn_start:
            self.grow_count = 0
            self.seed_count = 0

        self.mine = [tree for tree in self.trees if tree.is_mine]
        self.available = [tree for tree in self.mine if not tree.is_dormant]

        debug("available", self.available)

        allow_complete = (
            self.sun >= 4 and self.day > 10 and
            (
                self.score <= self.opp_score or
                self.tree_count[3] > MIN_GROWN or
                self.day >= MAX_DAY
            )
        )
        
        complete_shadowed = self.day < MAX_DAY

        allow_grow = self.day > 0
        min_grow = max(0, 3 + self.day - MAX_DAY)
        

        allow_seed = (
            self.day > 0 and
            self.day < MAX_DAY - 1 and
            len(self.mine) < MAX_TREES and
            self.tree_count[0] < MAX_SEEDS and
            tree_price(self.tree_count, 0) <= self.sun
        )
        
        unshadowed = [
            tree for tree in self.mine if not tree.shadowed(self.day % 6)]
        prefer_unshadowed = (
            self.day < MAX_DAY - 5 and
            len(unshadowed) < MIN_UNSHADOWED
        )

        debug("allow_complete", allow_complete)
        debug("min_grow", min_grow)
        debug("allow_seed", allow_seed)
        debug("prefer_unshadowed", prefer_unshadowed)

        # TODO, precompute actions and sort to promote seed

        if allow_complete:
            if target := self.best_complete(complete_shadowed):
                return "COMPLETE", target.id

        if allow_seed and self.tree_count[0] == 0:
            if target := self.best_seed(prefer_unshadowed):
                return "SEED", target[0].id, target[1].id

        if allow_grow:
            if target := self.best_grow(min_grow):
                return "GROW", target.id

        if allow_seed:
            if target := self.best_seed(prefer_unshadowed):
                return "SEED", target[0].id, target[1].id

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
