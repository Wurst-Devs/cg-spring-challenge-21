# CLASSES

class Cell:
    def __init__(self, *args):
        # index: 0 is the center cell, the next cells spiral outwards
        # richness: 0 if the cell is unusable, 1-3 for usable cells
        # neigh_0: the index of the neighbouring cell for each direction
        self.index = int(args[0])
        self.richness = int(args[1])
        self.neighbors_raw = map(int, args[2:])
        self.neighbors = []
    
    def init(self, cells):
        self.neighbors = [cells[i] for i in self.neighbors_raw]
    
    @property
    def has_tree(self):
        return self.tree is not None

class Tree:
    def __init__(self, cells, *args):
        self.cell = cells[int(args[0])] # location of this tree
        self.size = int(args[1]) # size of this tree: 0-3
        self.is_mine = args[2] == "1" # 1 if this is your tree
        self.is_dormant = args[3] == "1" # 1 if this tree is dormant
    
    def get_score(self, nutrients):
        return nutrients + 2 * (self.cell.richness - 1) if self.size == 3 else 0


# INIT

cells = [Cell(*input().split()) for _ in range(int(input()))]

for cell in cells:
    cell.init(cells)

# GAME LOOP
while True:
    day = int(input())  # the game lasts 24 days: 0-23
    nutrients = int(input())  # the base score you gain from the next COMPLETE action
    # sun: your sun points
    # score: your current score
    sun, score = [int(i) for i in input().split()]
    inputs = input().split()
    opp_sun = int(inputs[0])  # opponent's sun points
    opp_score = int(inputs[1])  # opponent's score
    opp_is_waiting = inputs[2] != "0"  # whether your opponent is asleep until the next day

    trees = [Tree(cells, *input().split()) for _ in range(int(input()))]

    [input() for _ in range(int(input()))] # possible_move ignored

    completable = [tree for tree in trees if tree.is_mine and tree.size == 3]
    completable.sort(key=lambda tree:tree.get_score(nutrients), reverse=True)

    if sun >= 4 and len(completable) > 0:
        print("COMPLETE", completable[0].cell.index)
    else:
        # GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>
        print("WAIT", "würst")
