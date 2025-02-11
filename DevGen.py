from Module import *
from Device_Generator import Topo, Layout

def topology_generation(tech: Tech, circuit: Circuit) -> None:
    for group_id in circuit.group:
        curr_group = circuit.group[group_id]
        
        if curr_group.type == "nmos":
            print("NMOS", [inst.id for inst in curr_group.inst])
            Topo.MOSFET(tech, circuit, curr_group)
            print()

        elif curr_group.type == "pmos":
            print("PMOS", [inst.id for inst in curr_group.inst])
            Topo.MOSFET(tech, circuit, curr_group)
            print()


def layout_generation(tech: Tech, circuit: dict, name: str) -> None:
    for group_id in circuit[name].group:
        curr_group = circuit[name].group[group_id]
        
        if curr_group.type == "nmos":
            print("NMOS", [inst.id for inst in curr_group.inst])
            Layout.MOSFET(tech, circuit[name], curr_group)
            print()

        elif curr_group.type == "pmos":
            print("PMOS", [inst.id for inst in curr_group.inst])
            Layout.MOSFET(tech, circuit[name], curr_group)
            print()

        elif curr_group.type == "subckt":
            print("Subckt", [inst.id for inst in curr_group.inst])
            Layout.SUBCKT(circuit, name, curr_group)
            print()