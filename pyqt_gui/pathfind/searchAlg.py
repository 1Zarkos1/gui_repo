import queue
import heapq

# class defining minimum heap structure
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


# main search class
class SearchClass():
    
    def __init__(self, maze, algor, cols, start=(0, 0, 0, 0), end=(0, 0, 0, 0)):
        # make incoming 1d array maze into 2d
        self.maze = [
            maze[i: i+cols]
            for i in range(0, len(maze), cols)
        ]
        # set start and end points with movement cost and heuristic values
        self.start = start[:2] + (0, abs(start[0]-end[0])+abs(start[1]-end[1]))
        self.end = end[:2] + (0, 0)
        # set dictionaries for storing nodes coordinates and values for 
        # movement cost and heuristic values
        self.came_from = {self.start[:2]: None}
        self.values = {}
        # save algorithm name and choose according data structure based on it
        self.algor = algor
        if algor == 'BFS':
            self.frontier = queue.Queue()
            self.frontier.put(start[:2])
        else:
            self.frontier = MyHeap(lambda x: x[3], [self.start])


    # returns cells directy adjacent to the current cell
    def get_adjacent_cells(self, coord):
        cells = [(coord[0]-1, coord[1]) if coord[0] > 0 else None,
                (coord[0], coord[1]+1) if coord[1] < len(self.maze[0])-1 else None,
                (coord[0]+1, coord[1]) if coord[0] < len(self.maze)-1 else None,
                (coord[0], coord[1]-1) if coord[1] > 0 else None]
    
        return [cell for cell in cells if cell != None]

    # main search function
    def do_search(self):
        # loop through while there is still cells in the queue
        while not self.frontier.empty():
            current = self.frontier.get()
            # if end cell is found break the loop
            if current[:2] == self.end[:2]:
                break

            for adj_cell in self.get_adjacent_cells(current):
                if (adj_cell != None and self.maze[adj_cell[0]][adj_cell[1]] != 1):
                    # store adjaceent cells in queue and node from which they 
                    # have been found
                    if self.algor == 'BFS' and adj_cell[:2] not in self.came_from:
                        self.frontier.put(adj_cell)
                        self.came_from[adj_cell[:2]] = current[:2]
                    # if algorithm requires additional values like movement cost 
                    # and heuristic values add them to a coordinate tuple
                    elif self.algor in ['Dijkstra', 'A*', 'Best-first']:
                        # for dijkstra add movement cost
                        if self.algor == 'Dijkstra':
                            full_cell = adj_cell + (0, current[3]+1)
                        # for A* add movement cost and heuristic value
                        elif self.algor == 'A*':
                            full_cell = adj_cell + (current[2]+1, abs(
                                        self.end[0]-adj_cell[0]) + abs(self.end[1]
                                        -adj_cell[1])+current[2]+1)
                        # for best-first search add heuristic value
                        else:
                            full_cell = adj_cell + (0, abs(
                                        self.end[0]-adj_cell[0]) + abs(self.end[1]
                                        -adj_cell[1]))
                        # if certain node does not have hearictic value for 
                        # (best-first and others) or if cost of travel to node
                        # lesser than it was stored already (for dijkstra and 
                        # A*) store new value in related strucures
                        if adj_cell not in self.values or (self.algor in 
                                ['A*', 'Dijkstra'] and self.values[adj_cell][1] 
                                > full_cell[-1]):
                            self.frontier.put(full_cell)
                            self.came_from[adj_cell] = current[:2]
                            self.values[adj_cell] = full_cell[2:]
    
    # return found path by analizing nodes (keys) and their parents (related 
    # values) in came_from dictionary, return full path based on it
    def get_final_path(self):
        path = [self.end[:2]]

        while True:
            where_from = self.came_from[path[-1]]
            path.append(where_from)
            if where_from == self.start[:2]:
                break

        return path