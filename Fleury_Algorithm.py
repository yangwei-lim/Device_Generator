from Device_Generator.EulerGraph import *
from Module.DB import Node

class Fleury_Algorithm:
    def __init__(self, graph: EulerGraph, verbose: bool=False):
        self.graph = graph
        self.verbose = verbose

    def initial_node(self) -> str:
        """
        @brief: choose the starting node for the circuit
        @return: the starting node
        """ 
        # find the node with odd degree
        for node in self.graph.graph:
            if len(self.graph.graph[node]) % 2 == 1:
                # get the node from the graph
                init_node = self.graph.graph[node][0].u if self.graph.graph[node][0].u.net == node else self.graph.graph[node][0].v

                return init_node
            
        # if there is no node with odd degree, choose the first node
        node = list(self.graph.graph.keys())[0]
        init_node = self.graph.graph[node][0].u if self.graph.graph[node][0].u.net == node else self.graph.graph[node][0].v
        return init_node
    
    def is_bridge(self, edge: EulerEdge) -> bool:
        """
        @brief: check if the edge is a bridge
        @param from_node: the starting node
        @param to_node: the ending node
        @return: True if the edge is a bridge, False otherwise
        """
        from_node = edge.u.net
        to_node   = edge.v.net
        edge_info = edge.e

        # remove the edge
        index = self.graph.remove_edge(from_node, to_node, edge_info)

        # run depth first search to check if the edge is a bridge
        visited = []
        self.dfs_visit(from_node, visited)

        # add the edge back
        self.graph.add_edge(edge.u, edge.v, edge.e, index)

        # if the edge is a bridge, the visited list will not contain the to_node
        return False if to_node in visited else True
    

    def dfs_visit(self, from_node: str, visited: list) -> None:
        """
        @brief: run depth first search to check if the graph is connected
        @param from_node: the starting node
        @param visited: the list of visited nodes
        """
        visited.append(from_node)
        for edge in self.graph.graph[from_node]:
            to_node = edge.v.net if edge.u.net == from_node else edge.u.net
            if to_node not in visited:
                self.dfs_visit(to_node, visited)


    def dfs_order(self, from_node: str, circuit: list, finger: bool=True) -> None:
        """
        @brief: run depth first search to find the circuit order
        @param from_node: the starting node
        @param circuit: the circuit order
        @param finger: True if the circuit is a finger, False otherwise
        """
        for edge in self.graph.graph[from_node]:
            to_node = edge.v if edge.u.net == from_node else edge.u
            fr_node = edge.u if edge.u.net == from_node else edge.v

            # if there is only one edge for the node, remove the edge
            if len(self.graph.graph[from_node]) == 1:

                # finger and non-finger circuit
                if finger:
                    circuit.extend([*edge.e, to_node])
                else:
                    circuit.extend([fr_node, *edge.e, to_node])

                self.graph.remove_edge(from_node, to_node.net, edge.e)
                self.dfs_order(to_node.net, circuit, finger)

            # if there is multiple edges for the node
            else:
                # remove the edge if it is not a bridge
                if not self.is_bridge(edge):
                    if finger:
                        circuit.extend([*edge.e, to_node])
                    else:
                        circuit.extend([fr_node, *edge.e, to_node])

                    self.graph.remove_edge(from_node, to_node.net, edge.e)
                    self.dfs_order(to_node.net, circuit, finger)

                # if it is a bridge, skip the edge
                else:
                    continue

    def fleury_algorithm(self, finger: bool=True) -> list:
        """
        @brief: run Fleury's algorithm to find the circuit order
        @param finger: True if the circuit is a finger, False otherwise
        @return: the circuit order
        """
        full_order = []
        while True:
            # choose a starting node
            start_node = self.initial_node()

            # create a list to store the circuit order
            order = [start_node] if finger else []

            # run depth first search
            self.dfs_order(start_node.net, order, finger)

            # extend the circuit order
            full_order.extend(order)

            # check if there is any edge left
            unconnected = False
            for node in self.graph.graph:
                if len(self.graph.graph[node]) > 0:
                    unconnected = True

            # if there is no edge left, run the algorithm again
            if unconnected:
                continue
            else:
                return full_order