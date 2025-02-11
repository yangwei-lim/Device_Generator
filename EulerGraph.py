from collections import defaultdict
from Module.DB import Node

class EulerEdge:
    """
    @brief: class for Edge in EulerGraph
    """
    def __init__(self, u: Node, v: Node, e: list): 
        self.u = u
        self.v = v
        self.e = e

class EulerGraph:
    """
    @brief: class for Graph that contains Eulerian Path
    """
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, u: Node, v: Node, e: list, index: int = -1) -> None:
        """
        @brief: add edge to the graph
        @param u: starting node (diff)
        @param v: ending node (diff)
        @param e: edge (gate)
        """
        if index == -1:
            self.graph[u.net].append(EulerEdge(u, v, e))
            self.graph[v.net].append(EulerEdge(v, u, e[::-1]))
        else:
            self.graph[u.net].insert(index, EulerEdge(u, v, e))
            self.graph[v.net].insert(index, EulerEdge(v, u, e[::-1]))

    def remove_edge(self, u: str, v: str, e: list=None) -> int:
        """
        @brief: remove edge from the graph
        @param u: starting node
        @param v: ending node
        @param e: edge
        @return i: index of the edge
        """
        for i, edge in enumerate(self.graph[u]):
            adj = edge.v.net if edge.u.net == u else edge.u.net     # get the adjacent node
            if adj == v and edge.e == e:
                del self.graph[u][i]
                break

        for i, edge in enumerate(self.graph[v]):
            adj = edge.u.net if edge.v.net == v else edge.v.net     # get the adjacent node
            if adj == u and edge.e[::-1] == e:
                del self.graph[v][i]
                break

        return i
    
def print_graph(graph: EulerGraph) -> None:
    """
    @brief: print the graph
    @param graph: EulerGraph object
    """
    for node in graph.graph:
        print(node, end=": ")
        for edge in graph.graph[node]:
            if edge.u.net == node:
                edge_info = [x.net for x in edge.e]
                print(edge.v.net+"("+str(*edge_info)+")", end=" ")
            else:
                edge_info = [x.net for x in edge.e]
                print(edge.u.net+"("+str(*edge_info)+")", end=" ")
        print()