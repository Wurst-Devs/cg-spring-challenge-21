import sys
import math
import itertools

from dataclasses import dataclass

def debug(*args):
  print(*args, file=sys.stderr)

class Forest:
  def __init__(self):
    number_of_cells = int(input())  # 37
    self.cells = [Cell(input().split()) for i in range(number_of_cells)]
    self._calculate_cell_neighbors()

    self.day_max = 23
    self.day = 0

    self.nutrients = 0

    self.sun = 0
    self.score = 0

    self.opp_sun = 0
    self.opp_score = 0
    self.opp_is_waiting = False

    self.trees = []
    self.tree_by_cell_id = {}
    self.trees_mine = []
    self.trees_mine_active = []
    self.trees_opp = []
    self.trees_mine_by_size = {i:[] for i in range(0,4)}
    self.trees_opp_by_size = {i:[] for i in range(0,4)}

    self.max_seeds = 1 # maximum number of seeds
    self.max_level_3 = 5 # maximum number of size:3 tree
    self.min_level_3 = 3 # minimum number of size:3 tree (before the last day)

  def read_inputs_loop(self):
    self.day = int(input())  # the game lasts 24 days: 0-5
    self.nutrients = int(input())  # the base score you gain from the next COMPLETE action
    # sun: your sun points
    # score: your current score
    self.sun, self.score = [int(i) for i in input().split()]
    inputs = input().split()
    
    self.opp_sun = int(inputs[0])  # opponent's sun points
    self.opp_score = int(inputs[1])  # opponent's score
    self.opp_is_waiting = inputs[2] != "0"  # whether your opponent is asleep until the next day
    
    number_of_trees = int(input())  # the current amount of trees
    self.trees = [Tree(self.cells, input().split()) for i in range(number_of_trees)]

    number_of_possible_moves = int(input())
    possible_moves = [input() for i in range(number_of_possible_moves)]

    # post input treatment
    self._calculate_trees()
  
  def _calculate_trees(self):
    self.tree_by_cell_id = {}
    self.trees_mine = []
    self.trees_mine_active = []
    self.trees_opp = []
    self.trees_mine_by_size = {i:[] for i in range(0,4)}
    self.trees_opp_by_size = {i:[] for i in range(0,4)}
    for tree in self.trees: # single loop to improve performance
      self.tree_by_cell_id[tree.cell.index] = tree
      if tree.is_mine:
        self.trees_mine.append(tree)
        self.trees_mine_by_size[tree.size].append(tree)
        if not tree.is_dormant:
          self.trees_mine_active.append(tree)
      else:
        self.trees_opp.append(tree)
        self.trees_opp_by_size[tree.size].append(tree)

  def _calculate_cell_neighbors(self):
    # change cells id to cells pointer
    for cell in self.cells:
      cell.neighbors = [self.cells[i] if i != -1 else None for i in cell.neighbors_id ]
    
    # calculate cells distance
    for cell in self.cells:
      neighbors = self.__calculate_cell_neighbors_recursive(cell)
      cell.neighbors_by_size = {i:[self.cells[cell_j] for cell_j in neighbors if neighbors[cell_j] == i] for i in range(1,4)}
      if len(cell.neighbors_by_size[1])>6 or len(cell.neighbors_by_size[2])>12 or len(cell.neighbors_by_size[3])>18:
        debug("ERROR calculate cell neighbors", cell, cell.neighbors_by_size)

  def __calculate_cell_neighbors_recursive(self, cell, output = None, distance=1, max_distance=3):
    """recursively calculate the distance. return {case_id: distance}"""
    if max_distance - distance < 0:
      return output

    if output is None:
      output = {}
      output[cell.index] = 0

    for cell_n in cell.neighbors:
      if cell_n is None:
        continue
      if cell_n.index not in output or output[cell_n.index] > distance:
        output[cell_n.index] = distance
        if distance + 1 <= max_distance:
            self.__calculate_cell_neighbors_recursive(cell_n, output, distance +1, max_distance)
    
    return output

  def grow_cost(self, size):
    if size+1 not in self.trees_mine_by_size:
      debug("grow_cost", size+1, self.trees_mine_by_size)
    return size ** 2 + size + 1 + len(self.trees_mine_by_size[size+1])
  
  def seed_cost(self):
    return len(self.trees_mine_by_size[0])

  def get_cases_shadow(self, case, day, size=3, reverse=False):
    """Get the cases impacted by a shadow cast by the `case` at `day` if a tree of `size` where on it.
    reverse = calculate the cases that will cast a shadow on this case. 
    """
    output = []
    current_case = case
    day_mod = (day + 3 * reverse)%6
    for _ in range(size):
      if current_case.neighbors[day_mod] is None:
        break
      else:
        output.append(current_case.neighbors[day_mod])
        current_case = current_case.neighbors[day_mod]
    return output

  def is_shadowed(self, case, day):
    shadows = self.get_cases_shadow(case, day, size = 3, reverse = True)
    i = 0
    for case in shadows:
      i+=1
      if case.index in self.tree_by_cell_id:
        tree = self.tree_by_cell_id[case.index]
        if tree.size >= i:
          return True
    return False

  def impact_shadow(self, case, day, size=3):
    """return the impact of the shadow on a given day. positive number means it will impact more the ennemy than us."""
    output = 0
    cases_impacted = self.get_cases_shadow(case, day, size)
    for case in cases_impacted:
      if case.index in self.tree_by_cell_id:
        tree = self.tree_by_cell_id[case.index]
        output+= -2 if tree.is_mine else 1 # twice the impact if this is our tree as the shadow would go both ways
    
    return output
  
  def impact_shadow_seed(self, case, day):
    """return the impact of the expected shadow of a seed planted on a given day. positive number means it will impact more the ennemy than us"""
    output = 0
    # direct future
    for day_delta in range(2,2+3):# calculate first for when the tree will grow
      output+= self.impact_shadow(case, day + day_delta, size=day_delta-1) / day_delta # the more the result is in the future, the less it should be impactful
    
    # full turn
    for i in range(6):
      output+= self.impact_shadow(case, i, size=3) / 3
    
    return output


  def _case_get_seed_value(self, case):
    """get the value of the case"""
    # value : richness + shadow impact + is_shadowed + near higher cases
    # in current configuration, ombrage > richness > neighbors
    if case.richness == 0:
      return None
    value = case.richness # 1, 2, 3

    # calculate shadow impact
    value+=2 * self.impact_shadow_seed(case, self.day)
    
    # calculate ombrage for the next 3 days
    for i in range(2, 5):
      if self.is_shadowed(case, self.day+i):
        value-=1/i
    
    # check if the case is near a case with high richness
    for neigh in case.neighbors:
      if neigh != None:
        value+=max(neigh.richness-1, 0)/(2*6) # can add a max of +1, this is just to differentiate some cases

        if neigh.index in self.tree_by_cell_id: # calculate, for a 2nd time, if there are tree near this seed.
          tree = self.tree_by_cell_id[neigh.index]
          value+= tree.size if not tree.is_mine else - tree.size * neigh.richness

    return value

  def find_case_to_seed(self):
    """find the case and tree that can be seeded"""
    # calculate using this formula :
    # if a tree on a N richness cell can seed a N+1 richness cell, grant +2 interest by richness difference
    # if the seed can in the next 3 turns grow and cast shadow on opponents tree, grant +2 interest by impacted tree
    # if the seed can in the next 3 turns grow and cast shadow on my tree, grant +1 interest by tree (still useful to seed here as it would prevent the opponent from doing so)
    # if a tree on a N richness cell can seed a N-1 richness cell, grant -0.5 interest by reichness difference
    seed_to_plant = (None, None, 3) #(tree, cell_to_seed, interest) - interest starts at 3 to prevent bad placements
    for tree in self.trees_mine_active:
      neighbors = list(itertools.chain.from_iterable(tree.cell.neighbors_by_size[i] for i in range(1, tree.size+1)))
      for cell in neighbors:
        if cell.richness != 0 and cell.index not in self.tree_by_cell_id:
          cell_value = self._case_get_seed_value(cell)
          
          if cell_value > seed_to_plant[2]:
            seed_to_plant = (tree, cell, cell_value)
    debug("cell_to_plant", seed_to_plant)
    return seed_to_plant[0:2]
    
  def find_tree_to_grow(self, min_size = 0):
    """find the best tree to grow"""
    output = None
    best = -9999
    prioritize_3 = len(self.trees_mine_by_size[3]) < self.max_level_3
    for tree in self.trees_mine_active:
      # TODO calculate shadow impact
      if tree.size >= 3 or tree.size < min_size:
        continue
      
      grow_cost = self.grow_cost(tree.size)

      if grow_cost > self.sun:
        continue
      
      if self.day < 3: # first 3 day : grow and conquer
        opportunity = tree.cell.richness
      else:
        if prioritize_3:
          opportunity = tree.cell.richness * (tree.size + 1) ** 2 - grow_cost 
        else:
          opportunity = tree.cell.richness**1.5 * (tree.size + 1) - grow_cost 

      if self.is_shadowed(tree.cell, self.day+1):
        # don't grow a tree that won't render anything next turn
        opportunity -= 2 * grow_cost

      if opportunity > best:
        best = opportunity
        output = tree

    return output
  
  def find_tree_to_complete(self):
    if len(self.trees_mine_by_size[3]) == 0:
      return None
    
    only_cut_if_shadowed = False

    if self.day_max > self.day: # not the last turn
      if len(self.trees_mine) - len(self.trees_mine_by_size[0]) < 3: # prevent cutting the last 3 tree
        return None
    
      if len(self.trees_mine_by_size[3]) < self.min_level_3: # keep at least min_level_3 fully grown trees
        return None
      
      only_cut_if_shadowed = len(self.trees_mine_by_size[3]) > self.max_level_3

    output = None
    best = -9999
    for tree in self.trees_mine_by_size[3]:
      if not tree.is_dormant:
        score = tree.get_score(self.nutrients)
        is_shadowed_day_1 = self.is_shadowed(tree.cell, self.day+1)
        is_shadowed_day_2 = self.is_shadowed(tree.cell, self.day+2)
        is_shadowed_day_3 = self.is_shadowed(tree.cell, self.day+3)
        if len(self.trees_mine_by_size[3]) <= self.min_level_3 + 1:  # only cut if the tree will have a really bad future production
          only_cut_if_shadowed_condition = is_shadowed_day_1 and (is_shadowed_day_2 and is_shadowed_day_3)
        elif len(self.trees_mine_by_size[3]) >= self.max_level_3-1:
          only_cut_if_shadowed_condition = is_shadowed_day_1 # cut if it is menaced in the direct next day
        else: # only cut if the tree will have a somewhat bad rendement
          only_cut_if_shadowed_condition = is_shadowed_day_1 and (is_shadowed_day_2 or is_shadowed_day_3)

        if is_shadowed_day_1: # evacute ombraged tree first
          score+=10
        if is_shadowed_day_2:
          score+=5
        if is_shadowed_day_3:
          score+=1
        if score > best and ((not only_cut_if_shadowed) + only_cut_if_shadowed * is_shadowed_day_1 * is_shadowed_day_2):
          best = score
          output = tree

    return output


  def calculate_action(self):
    """determine what is the best action to take"""
    # if day < 5 : grow,  don't cut anything, try to plant seed
    # if day >= 5 : always keep an edge on the score, try to maintain self.max_size_3 fully grown trees
    # if max_days - day <= 3 : stop to plant seeds
    # if max_days - day <= 2 : stop to grow seeds
    # if max_days - day <= 1 : stop to grow level 1
    # if max_days - day == 0 : only complete trees

    day_delay = self.day_max - self.day
    minimum_size_grow = 3 - day_delay
    can_plant_seed = day_delay > 1 and len(self.trees_mine_by_size[0]) < self.max_seeds and self.seed_cost() <= self.sun

    if self.day == 0:
      return "WAIT first_day"

    if self.day < 8:
      # grow tree if possible
      tree_to_grow = self.find_tree_to_grow()
      if tree_to_grow is not None:
        debug(tree_to_grow)
        return f"GROW {tree_to_grow.cell.index}"

      # if not, plant a seed if there are less than self.max_seed presents
      if can_plant_seed:
        seed_to_plant = self.find_case_to_seed()
        if seed_to_plant[0] is not None:
          return f"SEED {seed_to_plant[0].cell.index} {seed_to_plant[1].index}"

      return "WAIT before"

    debug(self.day, day_delay)

    # if score <= opponent_score : try to gain score
    if self.score <= self.opp_score or len(self.trees_mine_by_size[3]) > self.min_level_3 or day_delay < 1:
      tree_to_complete = self.find_tree_to_complete()
      if tree_to_complete is not None:
        return f"COMPLETE {tree_to_complete.cell.index}"
    
    # grow tree if possible
    tree_to_grow = self.find_tree_to_grow(minimum_size_grow)
    if tree_to_grow is not None:
      return f"GROW {tree_to_grow.cell.index}"
    
    # plant seed if we don't have too much of them
    if can_plant_seed:
      seed_to_plant = self.find_case_to_seed()
      if seed_to_plant[0] is not None:
        return f"SEED {seed_to_plant[0].cell.index} {seed_to_plant[1].index}"
    
    return "WAIT after"

class Cell:
  def __init__(self, args):
    self.index = int(args[0])
    self.richness = int(args[1])
    self.neighbors_id = list(map(int, args[2:8]))
    self.neighbors = [None] * 6
    self.neighbors_by_size = {i:[] for i in range(3)} # used to have all neighbors in range(1->3)
  
  def __repr__(self):
    return f"Cell {self.index}"

class Tree:
  def __init__(self, cells, args):
    self.cell_index = int(args[0])
    self.cell = cells[self.cell_index]
    self.size = int(args[1])
    self.is_mine = args[2] != '0'
    self.is_dormant = args[3] != '0'
    
  def get_score(self, nutrients: int):
    return nutrients + 2 * (self.cell.richness - 1)
    
  def grow_cost(self, forest):
    return self.size ** 2 + self.size +1 + len(forest.trees_mine_by_size[self.size+1])
  
  def __repr__(self):
    return f"Tree - size {self.size} - is_mine : {self.is_mine} - dormant : {self.is_dormant} - cell_index : {self.cell_index} / {self.cell.index}]"



# ============================ main code ================================
FOREST = Forest()

# game loop
while True:
    # get all inputs
    FOREST.read_inputs_loop()
    
    action = FOREST.calculate_action()

    print(action)
