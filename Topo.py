from Module.DB import *
from Device_Generator import Pattern
from Device_Generator.EulerGraph import *
from Device_Generator.Fleury_Algorithm import *
from engineering_notation import EngNumber as eng
import re


class MOSFET_Node:
    def __init__(self, type: str, net: str, length: float, width: float) -> None:
        self.type = type
        self.net = net
        self.length = length
        self.width = width

class MOSFET:
    """
    MOSFET Group Instance: Topology Generation
    """
    def __init__(self, tech: Tech, circuit: Circuit, group: Group) -> None:
        self.circuit = circuit
        self.group = group

        # Technology Unit
        self.db_unit = tech.unit["db"]

        # MOSFET Parameters
        self.all_finger = []
        self.all_multiplier  = []

        # MOSFET Topology generation
        self.update_info()
        self.generate_topology()
    

    def update_info(self) -> None:
        """
        Update MOSFET Group Instance Information
        """
        for inst in self.group.inst:
            # get the finger and multiplier value
            inst.param["finger"]     = int(inst.param["finger"])
            inst.param["multiplier"] = int(inst.param["multiplier"])

            # append to the list
            self.all_finger.append(inst.param["finger"])
            self.all_multiplier.append(inst.param["multiplier"])

            # update length and width 
            inst.param["length"] = eng(inst.param["length"])
            inst.param["width"] = eng(inst.param["width"])


    def generate_topology(self) -> None:
        """
        Generate MOSFET Topology
        """
        condition = self.get_topology_condition()

        if condition == 0:
            print("Multi-Finger Topology")
            nodelist = self.generate_multi_finger_topology()
        
        elif condition == 1:
            print("Multiplier Topology")
            nodelist = self.generate_multiplier_topology()

        elif condition == 2:
            print("Both Multi-Finger and Multiplier Topology")
            nodelist = self.generate_hybrid_topology()

        elif condition == 3:
            print("Error: Invalid Condition", condition)
            sys.exit()

        self.group.topology = nodelist
    

    def get_topology_condition(self) -> bool:
        """
        Check the MOSFET Group Condition
        return different conditions to determine different topology
             0 -> Multi-Finger Topology only
             1 -> Multiplier Topology only
             2 -> Both Multi-Finger and Multiplier Topology
             3 -> Error

        If All [m_1 .. m_n] == 1,
            find Euler Path for MF -> condition 0

        If Any [m_1 .. m_n] > 1
            If All [nf_1 .. nf_n] == 1
                find Euler Path for MP -> condition 1
            If Any [nf_1 .. nf_n] > 1 and [m_1 .. m_n] equal each other
                find Euler Path for MF & MP -> condition 2
            Else
                Error -> condition 3
        """
        # only one multiplier number (all same multiplier number)
        if len(set(self.all_multiplier)) == 1:
            # and the multiplier number is 1, mf topology only, no matter how many fingers
            if self.all_multiplier[0] == 1:
                return 0
            # and the multiplier number is greater than 1
            elif self.all_multiplier[0] > 1:
                # only one finger number (all same finger number)
                if (len(set(self.all_finger)) == 1):
                    # and the finger number is 1, mp topology only
                    if self.all_finger[0] == 1:
                        return 1
                    # and the finger number is greater than 1, mf & mp topology
                    elif self.all_finger[0] > 1:
                        return 2
                    # and the finger number is less than 1, error
                    elif self.all_finger[0] < 1:
                        return 3
            
                # more than one finger number
                elif len(set(self.all_finger)) > 1:
                    for i in set(self.all_finger):
                        # any finger number is greater than 1, mf & mp topology
                        if i > 1:
                            return 2
                        # any finger number is less than 1, error
                        elif i < 1:
                            return 3
            
            # and the multiplier number is less than 1, error
            elif self.all_multiplier[0] < 1:
                return 3
            
        # more than one multiplier number
        elif len(set(self.all_multiplier)) > 1:
            for i in set(self.all_multiplier):
                # any multiplier number is greater than 1
                if i > 1:
                    # only one finger number, and the finger number is 1, mp topology only
                    if len(set(self.all_finger)) == 1 and self.all_finger[0] == 1:
                        return 1
                
                elif i < 1:
                    return 3

            return 3
    

    def get_topology_order(self, topology: str) -> list:
        """
        Get the Topology Order Pattern
        """
        order = []
        if topology == "mf":
            if self.group.constraint["mf_sym"] == "None":
                order = Pattern.simple_1d_clustered_pattern(self.all_finger)
            
            elif self.group.constraint["mf_sym"] == "ID":
                order = Pattern.simple_1d_interdigitated_pattern(self.all_finger)

            elif self.group.constraint["mf_sym"] == "CC":
                order = Pattern.simple_1d_common_centroid_pattern(self.all_finger)

            elif re.match("\[.+\]",self.group.constraint["mf_sym"]) is not None:
                order = Pattern.custom_2d_pattern(self.group.constraint["mf_sym"])

            return order
        
        elif topology == "mp":
            if self.group.constraint["mp_sym"] == "None" and self.group.constraint["mp_row"] == 1:
                order.append(Pattern.simple_1d_clustered_pattern(self.all_multiplier))
            
            elif self.group.constraint["mp_sym"] == "ID":
                order.append(Pattern.simple_1d_interdigitated_pattern(self.all_multiplier))

            elif self.group.constraint["mp_sym"] == "CC":
                order.append(Pattern.simple_1d_common_centroid_pattern(self.all_multiplier))

            elif self.group.constraint["mp_sym"] == "None" and self.group.constraint["mp_row"] > 1:
                order = Pattern.simple_2d_clustered_pattern(self.all_multiplier, self.group.constraint["mp_row"])

            elif re.match("\[.+\]",self.group.constraint["mp_sym"]) is not None:
                order = Pattern.custom_2d_pattern(self.group.constraint["mp_sym"])

            return order


    def generate_multi_finger_topology(self) -> list:
        """
        Generate Multi-Finger Topology
        """
        # Get Multi-Finger Order
        mf_order = self.get_topology_order("mf")
        print("Order:", mf_order)

        # Create Eulerian Graph
        mf_euler = EulerGraph()

        # Add Edge for Multi-Finger Topology
        for i in mf_order:
            inst = self.group.inst[i]
            length = float(inst.param["length"]/self.db_unit)
            width = float(inst.param["width"]/self.db_unit) / inst.param["finger"]

            source = MOSFET_Node("diff", inst.node["source"].net, length, width)
            gate = MOSFET_Node("gate", inst.node["gate"].net, length, width)
            drain = MOSFET_Node("diff", inst.node["drain"].net, length, width)
            mf_euler.add_edge(source, drain, [gate])
     
        # Find Euler Path
        mf_euler_path = Fleury_Algorithm(mf_euler)
        nodelist = mf_euler_path.fleury_algorithm()

        return [nodelist]
    

    def generate_multiplier_topology(self) -> list:
        """
        Generate Multiplier Topology
        """
        nodelist = []
        # Get Multiplier Order
        mp_order = self.get_topology_order("mp")
        
        # Each Row in Multiplier Order
        for row in mp_order:
            print("Order:", row)

            # Create Eulerian Graph
            mp_euler = EulerGraph()

            # Add Edge for Multiplier Topology
            for i in row:
                inst = self.group.inst[i]
                length = float(inst.param["length"]/self.db_unit)
                width = float(inst.param["width"]/self.db_unit) / inst.param["finger"]

                source = MOSFET_Node("diff", inst.node["source"].net, length, width)
                gate = MOSFET_Node("gate", inst.node["gate"].net, length, width)
                drain = MOSFET_Node("diff", inst.node["drain"].net, length, width)
                mp_euler.add_edge(source, drain, [gate])

            # Find Euler Path
            mp_euler_path = Fleury_Algorithm(mp_euler)
            rowlist = mp_euler_path.fleury_algorithm(finger=False)

            nodelist.append(rowlist)

        return nodelist
    

    def generate_hybrid_topology(self) -> list:
        """
        Generate Multi-Finger and Multiplier Topology
        """
        nodelist = []

        # Generate Multi-Finger Topology
        mf_nodelist = self.generate_multi_finger_topology()

        # Create Eulerian Graph for multiplier order
        for _ in range(self.group.constraint["mp_row"]):
            # Create Eulerian Graph
            mp_euler = EulerGraph()     # NOTE: Change Different Edge adding can get different Initial node 

            # Add Edge for Multiplier Topology
            for _ in range(self.all_multiplier[0]//self.group.constraint["mp_row"]):
                fir = mf_nodelist[0][0]         # first node
                mid = mf_nodelist[0][1:-1]      # middle nodes
                lst = mf_nodelist[0][-1]        # last node
                mp_euler.add_edge(fir, lst, mid)

            # Find Euler Path
            mp_euler_path = Fleury_Algorithm(mp_euler)
            rowlist = mp_euler_path.fleury_algorithm(finger=False)

            nodelist.append(rowlist)

        return nodelist


    def add_dummy_node(self, nodelist: list, finger: bool = True) -> list:
        """
        Add Dummy Node to the nodelist
        """
        # Diffusion Connection
        pwr_gnd = "VDD" if self.group.type == "pmos" else "GND"

        # Create Left Dummy Node
        left_node = nodelist[1]
        left_dummy_diff = MOSFET_Node("diff", pwr_gnd, left_node.length, left_node.width)
        left_dummy_gate = MOSFET_Node("gate", "", left_node.length, left_node.width)

        # Create Right Dummy Node
        right_node = nodelist[-2]
        right_dummy_diff = MOSFET_Node("diff", pwr_gnd, right_node.length, right_node.width)
        right_dummy_gate = MOSFET_Node("gate", "", right_node.length, right_node.width)
        
        # Add Dummy Nodes
        if finger:
            nodelist = [left_dummy_diff, left_dummy_gate] + nodelist + [right_dummy_gate, right_dummy_diff]
        else:
            nodelist = [left_dummy_diff, left_dummy_gate, left_dummy_diff] + nodelist + [right_dummy_diff, right_dummy_gate, right_dummy_diff]
        
        return nodelist

