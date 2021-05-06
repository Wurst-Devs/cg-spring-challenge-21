using System;
using System.Linq;
using System.IO;
using System.Text;
using System.Collections;
using System.Collections.Generic;


class Player
{
    static void Main(string[] args)
    {
        string[] inputs;
        int numberOfCells = int.Parse(Console.ReadLine());

        Cell[] cells = new Cell[37];

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

        while (true)
        {
            int day = int.Parse(Console.ReadLine()); // the game lasts 24 days: 0-23
            int nutrients = int.Parse(Console.ReadLine()); // the base score you gain from the next COMPLETE action
            inputs = Console.ReadLine().Split(' ');
            int sun = int.Parse(inputs[0]); // your sun points
            int score = int.Parse(inputs[1]); // your current score
            inputs = Console.ReadLine().Split(' ');
            int oppSun = int.Parse(inputs[0]); // opponent's sun points
            int oppScore = int.Parse(inputs[1]); // opponent's score
            bool oppIsWaiting = inputs[2] != "0"; // whether your opponent is asleep until the next day
            int numberOfTrees = int.Parse(Console.ReadLine()); // the current amount of trees
            
            List<Tree> trees = new List<Tree>();
            List<Tree> sorted = new List<Tree>();

            for (int i = 0; i < numberOfTrees; i++)
            {
                inputs = Console.ReadLine().Split(' ');
                int cellIndex = int.Parse(inputs[0]); // location of this tree
                int size = int.Parse(inputs[1]); // size of this tree: 0-3
                bool isMine = inputs[2] != "0"; // 1 if this is your tree
                bool isDormant = inputs[3] != "0"; // 1 if this tree is dormant

                Tree tree = new Tree(cells[cellIndex], size, isMine, isDormant);
                trees.Add(tree);

                if (isMine) 
                {
                    int sort_index = 0;
                    for (int k = 0; k < sorted.Count; k++)
                    {
                        if (tree.size > sorted[k].size)
                        {
                            sort_index = k;
                            break;
                        }
                    }
                    sorted.Insert(sort_index, tree);
                }
            }

            int numberOfPossibleMoves = int.Parse(Console.ReadLine());
            for (int i = 0; i < numberOfPossibleMoves; i++)
            {
                string possibleMove = Console.ReadLine();
            }

            Spirit[] players = {new Spirit(sun, score, false), new Spirit(oppSun, oppScore, oppIsWaiting)};
            GameState state = new GameState(day, nutrients, numberOfTrees, cells, trees, players);

            // To debug: Console.Error.WriteLine("Debug messages...");

            // GROW cellIdx | SEED sourceIdx targetIdx | COMPLETE cellIdx | WAIT <message>

            Console.Error.WriteLine("Sun: {0} | My trees: {1}", sun, sorted.Count);

            if (sun > 4 && sorted.Count > 0)
            {
                Console.WriteLine("COMPLETE {0}", sorted[0].cell.index);
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
    public Spirit[] players;
    
    public GameState(int day, int nutrients, int numberOfTrees, Cell[] map, List<Tree> trees, Spirit[] players)
    {
        this.day = day;
        this.nutrients = nutrients;
        this.numberOfTrees = numberOfTrees;
        this.map = map;
        this.trees = trees;
        this.players = players;
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
    public int[] neighbors;

    public Cell(int index, int richness, int[] neighbors)
    {
        this.index = index;
        this.richness = richness;
        this.neighbors = neighbors;
    }
}

class Tree
{
    public Cell cell;
    public int size;
    public bool isMine;
    public bool isDormant;

    public Tree(Cell cell, int size, bool isMine, bool isDormant)
    {
        this.cell = cell;
        this.size = size;
        this.isMine = isMine;
        this.isDormant = isDormant;
    }

    public int GetScore(int nutrients)
    {
        return size == 3 ? nutrients + (2 * (cell.richness - 1)) : 0;
    }
}

class Spirit
{
    public int sun;
    public int score;
    public bool isWaiting;

    public Spirit(int sun, int score, bool isWaiting)
    {
        this.sun = sun;
        this.score = score;
        this.isWaiting = isWaiting;
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
