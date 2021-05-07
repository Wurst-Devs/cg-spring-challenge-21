using System;
using System.Linq;
using System.IO;
using System.Text;
using System.Collections;
using System.Collections.Generic;


class Player
{
    public const int MAX_DAY = 23;
    public const int CELL_COUNT = 37;

    static void Main(string[] args)
    {
        string[] inputs;
        int numberOfCells = int.Parse(Console.ReadLine());

        Cell[] cells = new Cell[CELL_COUNT];

        for (int i = 0; i < numberOfCells; i++)
        {
            inputs = Console.ReadLine().Split(' ');
            int index = int.Parse(inputs[0]); // 0 is the center cell, the next cells spiral outwards
            int richness = int.Parse(inputs[1]); // 0 if the cell is unusable, 1-3 for usable cells
            int neigh0 = int.Parse(inputs[2]); // the index of the neighbouring cell for each direction
            int neigh1 = int.Parse(inputs[3]);
            int neigh2 = int.Parse(inputs[4]);
            int neigh3 = int.Parse(inputs[5]);
            int neigh4 = int.Parse(inputs[6]);
            int neigh5 = int.Parse(inputs[7]);

            int[] neighbors = {neigh0, neigh1, neigh2, neigh3, neigh4, neigh5};
            cells[i] = new Cell(index, richness, neighbors);
        }

        foreach (Cell cell in cells)
        {
            cell.Init(cells);
        }

        List<Tree> trees = new List<Tree>();
        int day = -1;

        while (true)
        {
            int lastDay = day;
            day = int.Parse(Console.ReadLine()); // the game lasts 24 days: 0-23
            int sunDir = day % 6;
            bool turnStart = day != lastDay;
            int nutrients = int.Parse(Console.ReadLine()); // the base score you gain from the next COMPLETE action
            inputs = Console.ReadLine().Split(' ');
            int sun = int.Parse(inputs[0]); // your sun points
            int score = int.Parse(inputs[1]); // your current score
            inputs = Console.ReadLine().Split(' ');
            int oppSun = int.Parse(inputs[0]); // opponent's sun points
            int oppScore = int.Parse(inputs[1]); // opponent's score
            bool oppIsWaiting = inputs[2] != "0"; // whether your opponent is asleep until the next day
            int numberOfTrees = int.Parse(Console.ReadLine()); // the current amount of trees

            List<Tree> lastTrees = trees;
            trees = new List<Tree>();
            List<Tree> available = new List<Tree>();
            List<Tree> myTrees = new List<Tree>();
            List<Tree> oppTrees = new List<Tree>();
            List<Tree> completable = new List<Tree>();
            List<Tree> growable = new List<Tree>();
            List<Tree> seeding = new List<Tree>();

            int next_sun = sun;
            int[] myCount = new int[4];
            int[] oppCount = new int[4];

            for (int i = 0; i < numberOfTrees; i++)
            {
                inputs = Console.ReadLine().Split(' ');
                int cellIndex = int.Parse(inputs[0]); // location of this tree
                int size = int.Parse(inputs[1]); // size of this tree: 0-3
                bool isMine = inputs[2] != "0"; // 1 if this is your tree
                bool isDormant = inputs[3] != "0"; // 1 if this tree is dormant

                Tree tree = new Tree(cells[cellIndex], size, isMine, isDormant, lastTrees, turnStart, sunDir);
                trees.Add(tree);

                if (tree.isMine)
                {
                    myTrees.Add(tree);
                    next_sun += tree.size;

                    if (!tree.isDormant) { available.Add(tree); }
                } else { oppTrees.Add(tree); }
            }

            Spirit me = new Spirit(sun, score, myTrees, false);
            Spirit opp = new Spirit(oppSun, oppScore, oppTrees, oppIsWaiting);
            GameState state = new GameState(day, nutrients, numberOfTrees, cells, trees, me, opp);

            foreach (Tree tree in available)
            {
                if (tree.size == 3 && (tree.GetDays() > tree.GetMaxDays() || day == MAX_DAY))
                { 
                    completable.Add(tree); 
                }
                else 
                {
                    if (sun >= tree.GetPrice(state))    { growable.Add(tree); }
                    if (tree.CanSeed())                 { seeding.Add(tree); }
                }
            }

            completable = completable.OrderBy(o=>o.GetROI(state)).ToList();
            growable = growable.OrderBy(o=>o.GetROI(state)).ToList();
            seeding = seeding.OrderBy(o=>o.seedable[0].richness).ToList();

            completable.Reverse();
            growable.Reverse();
            seeding.Reverse();

            int numberOfPossibleMoves = int.Parse(Console.ReadLine());
            for (int i = 0; i < numberOfPossibleMoves; i++)
            {
                string possibleMove = Console.ReadLine();
            }

            // To debug: Console.Error.WriteLine("Debug messages...");

            // GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>
            if (completable.Count > 0 && sun >= 4)
            {
                Console.WriteLine("COMPLETE {0}", completable[0].cell.index);
            } 
            else if (day != MAX_DAY && growable.Count > 0)
            {
                Console.WriteLine("GROW {0}", growable[0].cell.index);
            }
            else if (seeding.Count > 0 && sun >= state.me.treeCount[0])
            {
                Console.WriteLine("SEED {0} {1}", seeding[0].cell.index, seeding[0].seedable[0].index);
            }
            else
            {
                Console.WriteLine("WAIT");
            }
        }
    }
}


class GameState 
{
    public int day;
    public int nutrients;
    public int numberOfTrees;
    public Cell[] map;
    public List<Tree> trees;
    public Spirit me;
    public Spirit opp;

    public GameState(int day, int nutrients, int numberOfTrees, Cell[] map, List<Tree> trees, Spirit me, Spirit opp)
    {
        this.day = day;
        this.nutrients = nutrients;
        this.numberOfTrees = numberOfTrees;
        this.map = map;
        this.trees = trees;
        this.me = me;
        this.opp = opp;
    }

    public List<Action> PossibleMoves()
    {
        return new List<Action>();
    }
}

class Cell
{
    public int index;
    public int richness;
    public int[] neighborIDs;
    public List<Cell> neighbors;
    public Tree tree;
    public int shadow;
    public int nextShadow;

    public Cell(int index, int richness, int[] neighborIDs)
    {
        this.index = index;
        this.richness = richness;
        this.neighborIDs = neighborIDs;

        tree = null;
        shadow = 0;
        nextShadow = 0;
    }

    public void Init(Cell[] cells)
    {
        neighbors = new List<Cell>();

        foreach (int i in neighborIDs) 
        {
            if (i >= 0) { neighbors.Add(cells[i]); }
            else { neighbors.Add(null); }
        }
    }

    public bool HasTree()
    {
        return !(tree is null);
    }

    public void reset()
    {
        tree = null;
        shadow = 0;
        nextShadow = 0;
    }

    public void update(int sunDir, Tree tree)
    {
        this.tree = tree;
        int remaining = tree.size;
        Cell target = neighbors[sunDir];

        while (!(target is null) && (remaining > 0))
        {
            target.shadow = Math.Max(target.shadow, tree.size);
            target = target.neighbors[sunDir];
            remaining--;
        }

        remaining = tree.size;
        target = neighbors[(sunDir + 1) % 6];

        while (!(target is null) && (remaining > 0))
        {
            target.nextShadow = Math.Max(target.nextShadow, tree.size);
            target = target.neighbors[(sunDir + 1) % 6];
            remaining--;
        }
    }

    public List<Cell> area(int size, List<Cell> included)
    {
        if (size < 0) { return new List<Cell>(); }

        List<Cell> output = new List<Cell>();
        foreach (Cell neighbor in neighbors)
        {
            if (!(neighbor is null) && !included.Contains(neighbor))
            {
                included.Add(neighbor);
                output.Add(neighbor);
                output = output.Concat(neighbor.area(size - 1, included)).ToList();
            }
        }
        return output;
    }
}

class Tree
{
    public Cell cell;
    public int size;
    public bool isMine;
    public bool isDormant;
    public List<Cell> seedable;
    public List<int> history;

    public Tree(Cell cell, int size, bool isMine, bool isDormant, List<Tree> lastTrees, bool turnStart, int sunDir)
    {
        this.cell = cell;
        this.size = size;
        this.isMine = isMine;
        this.isDormant = isDormant;

        this.cell.update(sunDir, this);
        seedable = null;

        history = new List<int>();
        List<Tree> oldSelf = new List<Tree>();
        foreach (Tree tree in lastTrees) { if (tree.cell.index == this.cell.index) { oldSelf.Add(tree); }}

        if (oldSelf.Count == 0) 
        { 
            history.Add(this.size); 
        }
        else if (turnStart) 
        {
            history.Concat(oldSelf[0].history);
            history.Add(this.size);
        }
        else
        {
            history.Concat(oldSelf[0].history);
        }

    }

    public int GetScore(int nutrients)
    {
        return size == 3 ? nutrients + (2 * (cell.richness - 1)) : 0;
    }

    public int GetPrice(GameState state)
    {
        if (size == 1) {
            return 3 + state.me.treeCount[2];
        } else if (size == 2) {
            return 7 + state.me.treeCount[3];
        } else {
            return 0;
        }
    }

    public int GetGScore()
    {
        return cell.richness + (size + 1) * 10;
    }

    public int GetDays()
    {
        return history.Count(o => o == size);
    }

    public int GetMaxDays()
    {
        return (3 - cell.richness) * 4 + 1;
    }

    public int GetNextSun()
    {
        return cell.nextShadow < size ? size : 0;
    }

    public double GetROI(GameState state)
    {
        return Math.Pow(cell.richness + 1, 2) / GetPrice(state);
    }

    public List<Cell> GetSeedable()
    {
        if (!(seedable is null))
        {
            if (size == 0)
            {
                seedable = new List<Cell>();
            }
            else
            {
                List<Cell> area = cell.area(size, new List<Cell>());
                seedable = new List<Cell>();

                foreach (Cell cell in area)
                {
                    if (!cell.HasTree() && cell.richness > 0) { seedable.Add(cell); }
                }

                seedable = seedable.OrderBy(c=>c.richness).ToList();
                seedable.Reverse();
            }
        }
        return seedable;
    }

    public bool CanSeed()
    {
        return size > 0 && GetSeedable().Count > 0;
    }
}

class Spirit
{
    public int sun;
    public int score;
    public bool isWaiting;
    public List<Tree> trees;
    public int[] treeCount;

    public Spirit(int sun, int score, List<Tree> trees, bool isWaiting)
    {
        this.sun = sun;
        this.score = score;
        this.trees = trees;
        this.isWaiting = isWaiting;

        treeCount = new int[4];
        foreach (Tree tree in this.trees)
        {
            treeCount[tree.size] += 1;
        }
    }
}

class Action
{
    const string WAIT = "WAIT";
    const string SEED = "SEED";
    const string GROW = "GROW";
    const string COMPLETE = "COMPLETE";

    public static Action Parse(string action)
    {
        string[] parts = action.Split(" ");
        switch (parts[0])
        {
            case WAIT:
                return new Action(WAIT);
            case SEED:
                return new Action(SEED, int.Parse(parts[1]), int.Parse(parts[2]));
            case GROW:
            case COMPLETE:
            default:
                return new Action(parts[0], int.Parse(parts[1]));
        }
    }

    string type;
    int targetCellIdx;
    int sourceCellIdx;

    public Action(string type, int sourceCellIdx, int targetCellIdx)
    {
        this.type = type;
        this.targetCellIdx = targetCellIdx;
        this.sourceCellIdx = sourceCellIdx;
    }

    public Action(string type, int targetCellIdx)
        : this(type, 0, targetCellIdx)
    {
    }

    public Action(string type)
        : this(type, 0, 0)
    {
    }

    public override string ToString()
    {
        if (type == WAIT)
        {
            return Action.WAIT;
        }
        if (type == SEED)
        {
            return string.Format("{0} {1} {2}", SEED, sourceCellIdx, targetCellIdx);
        }
        return string.Format("{0} {1}", type, targetCellIdx);
    }
}
