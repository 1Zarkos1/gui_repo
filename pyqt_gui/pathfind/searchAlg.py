import queue
import heapq

class MyHeap(object):
    def __init__(self, key, data=()):
        self.key = key
        self.heap = [(self.key(d), d) for d in data]
        heapq.heapify(self.heap)

    def put(self, item):
        decorated = self.key(item), item
        heapq.heappush(self.heap, decorated)

    def get(self):
        decorated = heapq.heappop(self.heap)
        return decorated[1]

    def pushpop(self, item):
        decorated = self.key(item), item
        dd = heapq.heappushpop(self.heap, decorated)
        return dd[1]

    def replace(self, item):
        decorated = self.key(item), item
        dd = heapq.heapreplace(self.heap, decorated)
        return dd[1]

    def empty(self):
        if self.heap:
            return False
        else:
            return True

    def __len__(self):
        return len(self.heap)


class SearchClass():
    
    def __init__(self, maze, algor, cols, start=(0, 0), end=(9, 9)):
        self.maze = [
            maze[i: i+cols]
            for i in range(0, len(maze), cols)
        ]
        self.start = start
        self.end = end
        self.came_from = {self.start: None}
        self.values = {}
        if algor == 'BFS':
            self.frontier = queue.Queue()
            self.frontier.put(start)
        elif algor == 'A*':
            self.frontier = MyHeap(lambda x: x[3], [start])
        else:
            self.frontier = MyHeap(lambda x: x[2], [start])

    def get_adjacent_cells(self, coord):
        cells = [(coord[0]-1, coord[1]) if coord[0] > 0 else None,
                (coord[0], coord[1]+1) if coord[1] < len(self.maze[0])-1 else None,
                (coord[0]+1, coord[1]) if coord[0] < len(self.maze)-1 else None,
                (coord[0], coord[1]-1) if coord[1] > 0 else None]
    
        return [cell for cell in cells if cell != None]

    def bfs_search(self):
        while not self.frontier.empty():
            current = self.frontier.get()
            if current == self.end[:2]:
                break
            for adj_cell in self.get_adjacent_cells(current):
                if (adj_cell != None and self.maze[adj_cell[0]][adj_cell[1]] != 1 
                        and adj_cell not in self.came_from):
                    self.frontier.put(adj_cell)
                    self.came_from[adj_cell] = current

    def dkstr_search(self):
        pass

    def astar_search(self):
        pass

    def bestfst_search(self):
        pass
    
    def get_final_path(self):
        path = [self.end[:2]]

        while True:
            where_from = self.came_from[path[-1]]
            path.append(where_from)
            if where_from == self.start[:2]:
                break

        return path


maze = [
    1, 1, 0, 1, 0, 0,
    0, 0, 0, 0, 1, 0,
    0, 0, 1, 0, 0, 0,
    0, 0, 0, 1, 0, 0,
    0, 1, 0, 1, 1, 1,
    0, 1, 0, 0, 0, 0
]

bs = SearchClass(maze, 'BFS', 6, (1,0), (5,5))