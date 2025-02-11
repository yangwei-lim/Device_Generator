from Module.DB import *
from Device_Generator.Topo import MOSFET_Node
import math

class MOSFET:
    """
    MOSFET Group Instance: Layout Generation
    """
    def __init__(self, tech: Tech, circuit: Circuit, group: Group):
        self.circuit = circuit
        self.group = group
        
        self.get_design_rules(tech)
        self.initialize_shape()
        self.generate_layout()


    def get_design_rules(self, tech: Tech) -> None:
        """
        Get the design rules from the technology
        """
        # minimum manufacturing grid
        self.grid = tech.unit["grid"]

        # different layers for nmos and pmos
        if self.group.type == "nmos":
            self.df = "ndiffusion"
            self.im = "nimplant"
            self.ga = "ngate"
            self.tdf = "pdiffusion"
            self.tim = "pimplant"
        elif self.group.type == "pmos":
            self.df = "pdiffusion"
            self.im = "pimplant"
            self.ga = "pgate"
            self.tdf = "ndiffusion"
            self.tim = "nimplant"

        # common layers for both nmos and pmos
        self.po = "poly"
        self.co = "contact"
        self.m1 = "metal1"
        self.nw = "nwell"
        self.pw = "pwell"

        # design rule alias
        self.co_sz     = tech.min_size_rule["contact"]
        self.ga_spc_ga = tech.min_spacing_rule[(self.ga,self.ga)]
        self.po_spc_co = tech.min_spacing_rule[("poly","contact")]
        self.co_spc_co = tech.min_spacing_rule[("contact","contact")]

        self.df_enc_co = tech.min_enclosure_rule[(self.df,"contact")]
        self.df_spc_po = tech.min_spacing_rule[(self.df,"poly")]
        self.df_spc_df = tech.min_spacing_rule[(self.df,self.df)]
        self.po_ext_df = tech.min_extension_rule[("poly",self.df)]
        self.df_ext_po = tech.min_extension_rule[(self.df,"poly")]
        self.df_wid    = tech.min_width_rule[self.df]
        
        self.im_enc_df = tech.min_enclosure_rule[(self.im,self.df)]
        self.im_enc_ga = tech.min_enclosure_rule[(self.im,self.ga)]
        self.im_spc_im = tech.min_spacing_rule[(self.im,self.im)]
        self.im_wid    = tech.min_width_rule[self.im]
        self.im_area   = tech.min_area_rule[self.im]

        self.nw_enc_pdf = tech.min_enclosure_rule[("nwell","pdiffusion")]
        self.nw_area    = tech.min_area_rule["nwell"]

        self.m1_wid     = tech.min_width_rule["metal1"]
        self.m1_spc_m1  = tech.min_spacing_rule[("metal1","metal1")]
        self.m1_enc_co  = tech.min_enclosure_rule[("metal1","contact")]
        self.m1_enc_coe = tech.min_enclosure_rule[("metal1","contact","end")]

        # self.tdf_spc_df  = tech.min_spacing_rule[(self.tdf,self.df,"tap")]
        self.tim_enc_tdf = tech.min_enclosure_rule[(self.tim,self.tdf,"tap")]
        self.tdf_enc_tco = tech.min_enclosure_rule[(self.tdf,"contact","tap")]

        if (self.tim,self.df,"tap") in tech.min_spacing_rule:
            self.tim_spc_df  = tech.min_spacing_rule[(self.tim,self.df,"tap")]
        else:
            self.tim_spc_df  = 0

        if (self.im,self.tdf,"tap") in tech.min_spacing_rule:
            self.im_spc_tdf  = tech.min_spacing_rule[(self.im,self.tdf,"tap")]
        else:
            self.im_spc_tdf  = 0

        self.tim_wid     = tech.min_width_rule[self.tim]
        self.tdf_wid     = tech.min_width_rule[self.tdf]
        self.tim_area    = tech.min_area_rule[self.tim]
        self.tdf_area    = tech.min_area_rule[self.tdf]

        # user defined (hardcoded) design rules
        self.tap_space = 0.2


    def initialize_shape(self) -> None:
        """
        Initialize the shape of the group
        """
        # update the shape of the group
        if self.group.type == "nmos":
            self.group.shape = {"ndiffusion": [], "nimplant": [], "poly": [], "contact": [], "metal1": [], "pdiffusion": [], "pimplant": []}
        elif self.group.type == "pmos":
            self.group.shape = {"pdiffusion": [], "pimplant": [], "poly": [], "contact": [], "metal1": [], "ndiffusion": [], "nimplant": [], "nwell": []}


    def generate_layout(self) -> None:
        """
        Layout Generation based on MOSFET topology
        """
        # get each row topology of the group
        for row in self.group.topology:
            # get each node in the row
            for i in range(len(row)):
                # get the current, previous and next node 
                curr_node = row[i]
                prev_node = row[i-1] if i > 0 else None
                next_node = row[i+1] if i < len(row)-1 else None

                # different node condition
                if curr_node.type == "diff" and prev_node == None:
                    self.generate_first_diff_layout(curr_node, next_node)
                    
                elif curr_node.type == "gate" and prev_node.type == "diff":
                    self.generate_diff_gate_layout(curr_node)

                elif curr_node.type == "diff" and prev_node.type == "gate":
                    self.generate_gate_diff_layout(prev_node, curr_node, next_node)

                elif curr_node.type == "diff" and prev_node.type == "diff":
                    self.generate_break_diff_layout(curr_node, next_node)

                elif curr_node.type == "gate" and prev_node.type == "gate":
                    self.generate_gate_gate_layout(curr_node)

                else:
                    print("Error: Invalid Node Type")


        # Add Implant and Nwell Shapes
        self.insert_implant_shape()
        
        # Create Device Body based on the constraint
        self.create_body(self.group.inst[0].node["bulk"].net)

        # Add Nwell Shapes
        self.insert_nwell_shape()

        # Add Boundary Box
        self.create_boundary()
        

    def generate_first_diff_layout(self, curr_node: MOSFET_Node, next_node: MOSFET_Node) -> None:
        """
        @brief: first diffusion node
        """
        df_shape = []
        co_shape = []
        m1_shape = []    

        # diffusion shape
        df_x0 = 0
        df_x1 = self.df_enc_co*2 + self.co_sz
        df_y0 = 0
        df_y1 = max(self.df_enc_co*2 + self.co_sz, next_node.width)

        df_shape.append(Box(self.df, [df_x0, df_y0], [df_x1, df_y1]))

        # contact array
        num_co = int(((df_y1 - df_y0) - self.df_enc_co * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1     # number of contact
        df_enc_co = ((df_y1 - df_y0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2               # diffusion enclosure contact based on the height

        co_x0 = df_x0 + self.df_enc_co
        co_x1 = co_x0 + self.co_sz

        for i in range(num_co):
            co_y0 = df_y0 + df_enc_co + i*(self.co_sz + self.co_spc_co)
            co_y1 = co_y0 + self.co_sz

            co_shape.append(Box(self.co, [co_x0, co_y0], [co_x1, co_y1]))

        # metal1 shape
        m1_x0 = co_x0 - self.m1_enc_co
        m1_x1 = co_x1 + self.m1_enc_co
        m1_y0 = co_shape[0].y[0] - self.m1_enc_coe
        m1_y1 = co_shape[-1].y[1] + self.m1_enc_coe

        m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

        # update the shape of the group
        self.group.shape[self.df] += df_shape
        self.group.shape[self.co] += co_shape
        self.group.shape[self.m1] += m1_shape
        self.group.pin.append(Pin(curr_node.net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))


    def generate_diff_gate_layout(self, curr_node: MOSFET_Node) -> None:
        """
        @brief: current gate node and previous diff node
        """
        df_shape = []
        po_shape = []

        # previous contact shape
        co_x1 = self.group.shape[self.co][-1].x[1]

        # diffusion shape
        df_x0 = co_x1 + self.po_spc_co - self.df_ext_po
        df_x1 = df_x0 + curr_node.length + self.df_ext_po*2
        df_y0 = 0
        df_y1 = curr_node.width

        df_shape.append(Box(self.df, [df_x0, df_y0], [df_x1, df_y1]))

        # poly shape
        po_x0 = df_x0 + self.df_ext_po
        po_x1 = po_x0 + curr_node.length
        po_y0 = df_y0 - self.po_ext_df
        po_y1 = df_y1 + self.po_ext_df

        po_shape.append(Box(self.po, [po_x0, po_y0], [po_x1, po_y1]))

        # update the shape of the group
        self.group.shape[self.df] += df_shape
        self.group.shape[self.po] += po_shape
        self.group.pin.append(Pin(curr_node.net, self.po, [po_x0, po_y0], [po_x1, po_y1]))


    def generate_gate_diff_layout(self, prev_node: MOSFET_Node, curr_node: MOSFET_Node, next_node: MOSFET_Node) -> None:
        """
        @brief: current diff node and prev gate node
        """
        df_shape = []
        co_shape = []
        m1_shape = []    

        # previous poly shape
        po_x1 = self.group.shape[self.po][-1].x[1]

        # diffusion shape
        df_x0 = po_x1 + self.po_spc_co - self.df_enc_co
        df_x1 = df_x0 + self.df_enc_co*2 + self.co_sz
        df_y0 = 0
        if next_node and next_node.type == "gate":
            df_y1 = max(self.df_enc_co*2 + self.co_sz, prev_node.width, next_node.width)
        else:
            df_y1 = max(self.df_enc_co*2 + self.co_sz, prev_node.width)

        df_shape.append(Box(self.df, [df_x0, df_y0], [df_x1, df_y1]))

        # contact array
        num_co = int(((df_y1 - df_y0) - self.df_enc_co * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1     # number of contact
        df_enc_co = ((df_y1 - df_y0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2               # diffusion enclosure contact based on the height

        co_x0 = df_x0 + self.df_enc_co
        co_x1 = co_x0 + self.co_sz

        for i in range(num_co):
            co_y0 = df_y0 + df_enc_co + i*(self.co_sz + self.co_spc_co)
            co_y1 = co_y0 + self.co_sz

            co_shape.append(Box(self.co, [co_x0, co_y0], [co_x1, co_y1]))

        # metal1 shape
        m1_x0 = co_x0 - self.m1_enc_co
        m1_x1 = co_x1 + self.m1_enc_co
        m1_y0 = co_shape[0].y[0] - self.m1_enc_coe
        m1_y1 = co_shape[-1].y[1] + self.m1_enc_coe

        m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

        # update the shape of the group
        self.group.shape[self.df] += df_shape
        self.group.shape[self.co] += co_shape
        self.group.shape[self.m1] += m1_shape
        self.group.pin.append(Pin(curr_node.net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))


    def generate_gate_gate_layout(self, curr_node: MOSFET_Node) -> None:
        """
        @brief: continuous gate node
        """
        df_shape = []
        po_shape = []

        # previous poly shape
        po_x1 = self.group.shape[self.po][-1].x[1]

        # diffusion shape
        df_x0 = po_x1 + self.ga_spc_ga - self.df_ext_po
        df_x1 = df_x0 + curr_node.length + self.df_ext_po*2
        df_y0 = 0
        df_y1 = curr_node.width

        df_shape.append(Box(self.df, [df_x0, df_y0], [df_x1, df_y1]))

        # poly shape
        po_x0 = df_x0 + self.df_ext_po
        po_x1 = po_x0 + curr_node.length
        po_y0 = df_y0 - self.po_ext_df
        po_y1 = df_y1 + self.po_ext_df

        po_shape.append(Box(self.po, [po_x0, po_y0], [po_x1, po_y1]))

        # update the shape of the group
        self.group.shape[self.df] += df_shape
        self.group.shape[self.po] += po_shape
        self.group.pin.append(Pin(curr_node.net, self.po, [po_x0, po_y0], [po_x1, po_y1]))


    def generate_break_diff_layout(self, curr_node: MOSFET_Node, next_node: MOSFET_Node) -> None:
        """
        @brief: break diffusion node
        """
        df_shape = []
        co_shape = []
        m1_shape = []
        
        # previous diffusion shape
        df_x1 = self.group.shape[self.df][-1].x[1]

        # diffusion shape
        df_x0 = df_x1 + self.df_spc_df
        df_x1 = df_x0 + self.df_enc_co*2 + self.co_sz
        df_y0 = 0
        df_y1 = max(self.df_enc_co*2 + self.co_sz, next_node.width)

        df_shape.append(Box(self.df, [df_x0, df_y0], [df_x1, df_y1]))

        # contact array
        num_co = int(((df_y1 - df_y0) - self.df_enc_co * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1     # number of contact
        df_enc_co = ((df_y1 - df_y0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2               # diffusion enclosure contact based on the height

        co_x0 = df_x0 + self.df_enc_co
        co_x1 = co_x0 + self.co_sz

        for i in range(num_co):
            co_y0 = df_y0 + df_enc_co + i*(self.co_sz + self.co_spc_co)
            co_y1 = co_y0 + self.co_sz

            co_shape.append(Box(self.co, [co_x0, co_y0], [co_x1, co_y1]))

        # metal1 shape
        m1_x0 = co_x0 - self.m1_enc_co
        m1_x1 = co_x1 + self.m1_enc_co
        m1_y0 = co_shape[0].y[0] - self.m1_enc_coe
        m1_y1 = co_shape[-1].y[1] + self.m1_enc_coe

        m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

        # update the shape of the group
        self.group.shape[self.df] += df_shape
        self.group.shape[self.co] += co_shape
        self.group.shape[self.m1] += m1_shape
        self.group.pin.append(Pin(curr_node.net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))


    def merge_shape(self, shape: list) -> list:
        """
        @brief: merge the shape based on the layer
        @param: shape -> list of shape
        """
        x = []
        y = []
        for shp in shape:
            x.append(shp.x[0])
            x.append(shp.x[1])
            y.append(shp.y[0])
            y.append(shp.y[1])
        
        if x and y:
            return min(x), max(x), min(y), max(y)
        
        else:
            return None, None, None, None


    def insert_implant_shape(self) -> None:
        # Get each diffusion shape
        for shape in self.group.shape[self.df]:
            # Add Implant Layer
            im_x0 = shape.x[0] - self.im_enc_df
            im_x1 = shape.x[1] + self.im_enc_df
            im_y0 = shape.y[0] - max(self.im_enc_df, self.im_enc_ga)
            im_y1 = shape.y[1] + max(self.im_enc_df, self.im_enc_ga)

            self.group.shape[self.im].append(Box(self.im, [im_x0, im_y0], [im_x1, im_y1]))

        # Merge Implant layer
        im_x0, im_x1, im_y0, im_y1 = self.merge_shape(self.group.shape[self.im])

        if im_x0 and im_x1 and im_y0 and im_y1:
            # Minimum Implant Area Rule
            if (im_x1 - im_x0) * (im_y1 - im_y0) < self.im_area:
                scale = math.sqrt(self.im_area / ((im_x1 - im_x0) * (im_y1 - im_y0)))
                im_x0 = im_x0 - (im_x1 - im_x0) * scale / 2
                im_x1 = im_x1 + (im_x1 - im_x0) * scale / 2
                im_y0 = im_y0 - (im_y1 - im_y0) * scale / 2
                im_y1 = im_y1 + (im_y1 - im_y0) * scale / 2

                # round the shape of the group
                im_x0 = round(im_x0/self.grid) * self.grid
                im_x1 = round(im_x1/self.grid) * self.grid
                im_y0 = round(im_y0/self.grid) * self.grid
                im_y1 = round(im_y1/self.grid) * self.grid

            # Update Implant Layer
            self.group.shape[self.im] = [Box(self.im, [im_x0, im_y0], [im_x1, im_y1])]


    def insert_nwell_shape(self) -> None:
        if self.group.type == "pmos":
            # Get each diffusion shape
            for shape in self.group.shape[self.df] + self.group.shape[self.tdf]:
                # Add Nwell Layer
                nw_x0 = shape.x[0] - self.nw_enc_pdf
                nw_x1 = shape.x[1] + self.nw_enc_pdf
                nw_y0 = shape.y[0] - self.nw_enc_pdf
                nw_y1 = shape.y[1] + self.nw_enc_pdf

                self.group.shape[self.nw].append(Box(self.nw, [nw_x0, nw_y0], [nw_x1, nw_y1]))

            # Merge Nwell layer
            nw_x0, nw_x1, nw_y0, nw_y1 = self.merge_shape(self.group.shape[self.nw])

            if nw_x0 and nw_x1 and nw_y0 and nw_y1:
                curr_area = (nw_x1 - nw_x0) * (nw_y1 - nw_y0)
                # Minimum Nwell Area Rule
                if curr_area < self.nw_area:

                    scale = math.sqrt(self.nw_area / curr_area)
                    width = (nw_x1 - nw_x0) * scale
                    height = (nw_y1 - nw_y0) * scale

                    center_x = (nw_x0 + nw_x1) / 2
                    center_y = (nw_y0 + nw_y1) / 2

                    nw_x0 = center_x - width / 2
                    nw_x1 = center_x + width / 2
                    nw_y0 = center_y - height / 2
                    nw_y1 = center_y + height / 2

                    # round the shape of the group
                    nw_x0 = round(nw_x0/self.grid) * self.grid
                    nw_x1 = round(nw_x1/self.grid) * self.grid
                    nw_y0 = round(nw_y0/self.grid) * self.grid
                    nw_y1 = round(nw_y1/self.grid) * self.grid

                # Update Nwell Layer
                self.group.shape[self.nw] = [Box(self.nw, [nw_x0, nw_y0], [nw_x1, nw_y1])]


    def create_body(self, body_net: str) -> None:
        if self.group.constraint["tap"]:
            tap_position = self.group.constraint["tap"].split(",")

            top_tim_shape, btm_tim_shape, rgt_tim_shape, lft_tim_shape = [], [], [], []
            top_tco_shape, btm_tco_shape, rgt_tco_shape, lft_tco_shape = [], [], [], []
            top_tdf_shape, btm_tdf_shape, rgt_tdf_shape, lft_tdf_shape = [], [], [], []
            top_m1_shape, btm_m1_shape, rgt_m1_shape, lft_m1_shape = [], [], [], []
            top_pin, btm_pin, rgt_pin, lft_pin = [], [], [], []
            
            if "t" in tap_position:
                dist = max(self.tim_spc_df, self.im_spc_tdf - self.tim_enc_tdf, self.tap_space)

                # implant shape
                tim_x0 = self.group.shape[self.df][0].x[0]  - self.tim_enc_tdf
                tim_x1 = self.group.shape[self.df][-1].x[1] + self.tim_enc_tdf
                tim_y0 = self.group.shape[self.im][0].y[1] + dist
                tim_y1 = tim_y0 + self.tim_enc_tdf*2 + self.tdf_enc_tco*2 + self.co_sz

                # minimum implant width rule
                if tim_y1 - tim_y0 < self.im_wid:
                    # scale tim_y1
                    tim_y1 = tim_y0 + self.im_wid
                    tim_y1 = round(tim_y1/self.grid) * self.grid

                # minimum implant area rule
                if not "r" in tap_position and not "l" in tap_position:
                    if (tim_y1 - tim_y0) * (tim_x1 - tim_x0) < self.tim_area:
                        # scale tim_y1 only
                        tim_y1 = tim_y0 + (self.tim_area / (tim_x1 - tim_x0))
                        tim_y1 = round(tim_y1/self.grid) * self.grid

                top_tim_shape.append(Box(self.tim, [tim_x0, tim_y0], [tim_x1, tim_y1]))

                # diffusion shape
                tdf_x0 = self.group.shape[self.df][0].x[0]
                tdf_x1 = self.group.shape[self.df][-1].x[1]
                tdf_y0 = tim_y0 + self.tim_enc_tdf
                tdf_y1 = tim_y1 - self.tim_enc_tdf

                top_tdf_shape.append(Box(self.tdf, [tdf_x0, tdf_y0], [tdf_x1, tdf_y1]))

                # contact array
                num_co = int(((tdf_x1 - tdf_x0) - self.tdf_enc_tco * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1
                tdf_enc_tco_x = ((tdf_x1 - tdf_x0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2
                tdf_enc_tco_y = ((tdf_y1 - tdf_y0) - self.co_sz) / 2

                tco_y0 = tdf_y0 + tdf_enc_tco_y
                tco_y1 = tdf_y1 - tdf_enc_tco_y
                for i in range(num_co):
                    tco_x0 = tdf_x0 + tdf_enc_tco_x + i*(self.co_sz + self.co_spc_co)
                    tco_x1 = tco_x0 + self.co_sz

                    top_tco_shape.append(Box(self.co, [tco_x0, tco_y0], [tco_x1, tco_y1]))
                
                # metal1 shape
                m1_x0 = top_tco_shape[0].x[0] - self.m1_enc_coe
                m1_x1 = top_tco_shape[-1].x[1] + self.m1_enc_coe
                m1_y0 = tco_y0 - self.m1_enc_co
                m1_y1 = tco_y1 + self.m1_enc_co

                top_m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))
                top_pin.append(Pin(body_net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))
                
            if "b" in tap_position:
                dist = max(self.tim_spc_df, self.im_spc_tdf - self.tim_enc_tdf, self.tap_space)

                # implant shape
                tim_x0 = self.group.shape[self.df][0].x[0]  - self.tim_enc_tdf
                tim_x1 = self.group.shape[self.df][-1].x[1] + self.tim_enc_tdf
                tim_y1 = self.group.shape[self.im][0].y[0] - dist
                tim_y0 = tim_y1 - self.tim_enc_tdf*2 - self.tdf_enc_tco*2 - self.co_sz

                # minimum implant width rule
                if tim_y1 - tim_y0 < self.im_wid:
                    # scale tim_y0
                    tim_y0 = tim_y1 - self.im_wid
                    tim_y0 = round(tim_y0/self.grid) * self.grid

                # minimum implant area rule
                if not "r" in tap_position and not "l" in tap_position:
                    if (tim_y1 - tim_y0) * (tim_x1 - tim_x0) < self.tim_area:
                        # scale tim_y0 only
                        tim_y0 = tim_y1 - (self.tim_area / (tim_x1 - tim_x0))
                        tim_y0 = round(tim_y0/self.grid) * self.grid
                
                btm_tim_shape.append(Box(self.tim, [tim_x0, tim_y0], [tim_x1, tim_y1]))

                # diffusion shape
                tdf_x0 = self.group.shape[self.df][0].x[0]
                tdf_x1 = self.group.shape[self.df][-1].x[1]
                tdf_y0 = tim_y0 + self.tim_enc_tdf
                tdf_y1 = tim_y1 - self.tim_enc_tdf

                btm_tdf_shape.append(Box(self.tdf, [tdf_x0, tdf_y0], [tdf_x1, tdf_y1]))

                # contact array
                num_co = int(((tdf_x1 - tdf_x0) - self.tdf_enc_tco * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1
                tdf_enc_tco_x = ((tdf_x1 - tdf_x0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2
                tdf_enc_tco_y = ((tdf_y1 - tdf_y0) - self.co_sz) / 2

                tco_y0 = tdf_y0 + tdf_enc_tco_y
                tco_y1 = tdf_y1 - tdf_enc_tco_y
                for i in range(num_co):
                    tco_x0 = tdf_x0 + tdf_enc_tco_x + i*(self.co_sz + self.co_spc_co)
                    tco_x1 = tco_x0 + self.co_sz

                    btm_tco_shape.append(Box(self.co, [tco_x0, tco_y0], [tco_x1, tco_y1]))
                
                # metal1 shape
                m1_x0 = btm_tco_shape[0].x[0] - self.m1_enc_coe
                m1_x1 = btm_tco_shape[-1].x[1] + self.m1_enc_coe
                m1_y0 = tco_y0 - self.m1_enc_co
                m1_y1 = tco_y1 + self.m1_enc_co

                btm_m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))
                btm_pin.append(Pin(body_net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

            if "r" in tap_position:
                dist = max(self.tim_spc_df, self.im_spc_tdf - self.tim_enc_tdf, self.tap_space)

                # implant shape
                tim_y0 = self.group.shape[self.df][0].y[0] - self.tim_enc_tdf
                tim_y1 = self.group.shape[self.df][-1].y[1] + self.tim_enc_tdf
                tim_x0 = self.group.shape[self.im][0].x[1] + dist
                tim_x1 = tim_x0 + self.tim_enc_tdf*2 + self.tdf_enc_tco*2 + self.co_sz

                # minimum implant width rule
                if tim_x1 - tim_x0 < self.im_wid:
                    # scale tim_x1
                    tim_x1 = tim_x0 + self.im_wid
                    tim_x1 = round(tim_x1/self.grid) * self.grid
                
                if "t" in tap_position or "b" in tap_position:
                    for shp in top_tim_shape + btm_tim_shape:
                        # update previous implant shape
                        shp.x[1] = tim_x1           # follow right tap

                        # update current implant shape
                        if shp.y[1] < tim_y0:       # follow bottom tap
                            tim_y0 = shp.y[1]

                        if shp.y[0] > tim_y1:       # follow top tap
                            tim_y1 = shp.y[0]
                else:
                    # minimum implant area rule
                    if (tim_y1 - tim_y0) * (tim_x1 - tim_x0) < self.tim_area:
                        # scale tim_x1 only
                        tim_x1 = tim_x0 + (self.tim_area / (tim_y1 - tim_y0))
                        tim_x1 = round(tim_x1/self.grid) * self.grid



                rgt_tim_shape.append(Box(self.tim, [tim_x0, tim_y0], [tim_x1, tim_y1]))

                # diffusion shape
                tdf_x0 = tim_x0 + self.tim_enc_tdf
                tdf_x1 = tim_x1 - self.tim_enc_tdf
                tdf_y0 = self.group.shape[self.df][0].y[0]
                tdf_y1 = self.group.shape[self.df][-1].y[1]

                if "t" in tap_position or "b" in tap_position:
                    for shp in top_tdf_shape + btm_tdf_shape:
                        # update previous diffusion shape
                        shp.x[1] = tdf_x1
            
                        # update current diffusion shape
                        if shp.y[1] < tdf_y0:
                            tdf_y0 = shp.y[1]
                        
                        if shp.y[0] > tdf_y1:
                            tdf_y1 = shp.y[0]

                rgt_tdf_shape.append(Box(self.tdf, [tdf_x0, tdf_y0], [tdf_x1, tdf_y1]))

                # contact array
                num_co = int(((tdf_y1 - tdf_y0) - self.tdf_enc_tco * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1
                tdf_enc_tco_x = ((tdf_x1 - tdf_x0) - self.co_sz) / 2
                tdf_enc_tco_y = ((tdf_y1 - tdf_y0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2

                tco_x0 = tdf_x0 + tdf_enc_tco_x
                tco_x1 = tdf_x1 - tdf_enc_tco_x
                for i in range(num_co):
                    tco_y0 = tdf_y0 + tdf_enc_tco_y + i*(self.co_sz + self.co_spc_co)
                    tco_y1 = tco_y0 + self.co_sz

                    rgt_tco_shape.append(Box(self.co, [tco_x0, tco_y0], [tco_x1, tco_y1]))

                # metal1 shape
                m1_x0 = tco_x0 - self.m1_enc_co
                m1_x1 = tco_x1 + self.m1_enc_co
                m1_y0 = rgt_tco_shape[0].y[0] - self.m1_enc_coe
                m1_y1 = rgt_tco_shape[-1].y[1] + self.m1_enc_coe

                if "t" in tap_position or "b" in tap_position:
                    for shp in top_m1_shape + btm_m1_shape:
                        # update previous metal1 shape
                        shp.x[1] = m1_x1

                        # update current metal1 shape
                        if shp.y[1] < m1_y0:
                            m1_y0 = shp.y[1]

                        if shp.y[0] > m1_y1:
                            m1_y1 = shp.y[0]

                    for pin in top_pin + btm_pin:
                        pin.pt2[0] = m1_x1

                rgt_m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))
                rgt_pin.append(Pin(body_net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

            if "l" in tap_position:
                dist = max(self.tim_spc_df, self.im_spc_tdf - self.tim_enc_tdf, self.tap_space)

                # implant shape
                tim_y0 = self.group.shape[self.df][0].y[0] - self.tim_enc_tdf
                tim_y1 = self.group.shape[self.df][-1].y[1] + self.tim_enc_tdf
                tim_x1 = self.group.shape[self.im][0].x[0] - dist
                tim_x0 = tim_x1 - self.tim_enc_tdf*2 - self.tdf_enc_tco*2 - self.co_sz

                # minimum implant width rule
                if tim_x1 - tim_x0 < self.im_wid:
                    # scale tim_x0
                    tim_x0 = tim_x1 - self.im_wid
                    tim_x0 = round(tim_x0/self.grid) * self.grid

                if "t" in tap_position or "b" in tap_position:
                    for shp in top_tim_shape + btm_tim_shape:
                        # update previous implant shape
                        shp.x[0] = tim_x0           # follow left tap
                    
                        # update current implant shape
                        if shp.y[1] < tim_y0:
                            tim_y0 = shp.y[1]
                        
                        if shp.y[0] > tim_y1:
                            tim_y1 = shp.y[0]
                else:
                    # minimum implant area rule
                    if (tim_y1 - tim_y0) * (tim_x1 - tim_x0) < self.tim_area:
                        # scale tim_x0 only
                        tim_x0 = tim_x1 - (self.tim_area / (tim_y1 - tim_y0))
                        tim_x0 = round(tim_x0/self.grid) * self.grid

                lft_tim_shape.append(Box(self.tim, [tim_x0, tim_y0], [tim_x1, tim_y1]))

                # diffusion shape
                tdf_x0 = tim_x0 + self.tim_enc_tdf
                tdf_x1 = tim_x1 - self.tim_enc_tdf
                tdf_y0 = self.group.shape[self.df][0].y[0]
                tdf_y1 = self.group.shape[self.df][-1].y[1]

                if "t" in tap_position or "b" in tap_position:
                    for shp in top_tdf_shape + btm_tdf_shape:
                        # update previous diffusion shape
                        shp.x[0] = tdf_x0
            
                        # update current diffusion shape
                        if shp.y[1] < tdf_y0:
                            tdf_y0 = shp.y[1]
                        
                        if shp.y[0] > tdf_y1:
                            tdf_y1 = shp.y[0]

                lft_tdf_shape.append(Box(self.tdf, [tdf_x0, tdf_y0], [tdf_x1, tdf_y1]))

                # contact array
                num_co = int(((tdf_y1 - tdf_y0) - self.tdf_enc_tco * 2 - self.co_sz)/(self.co_sz + self.co_spc_co)) + 1
                tdf_enc_tco_x = ((tdf_x1 - tdf_x0) - self.co_sz) / 2
                tdf_enc_tco_y = ((tdf_y1 - tdf_y0) - (num_co * self.co_sz) - ((num_co-1) * self.co_spc_co)) / 2

                tco_x0 = tdf_x0 + tdf_enc_tco_x
                tco_x1 = tdf_x1 - tdf_enc_tco_x

                for i in range(num_co):
                    tco_y0 = tdf_y0 + tdf_enc_tco_y + i*(self.co_sz + self.co_spc_co)
                    tco_y1 = tco_y0 + self.co_sz

                    lft_tco_shape.append(Box(self.co, [tco_x0, tco_y0], [tco_x1, tco_y1]))

                # metal1 shape
                m1_x0 = tco_x0 - self.m1_enc_co
                m1_x1 = tco_x1 + self.m1_enc_co
                m1_y0 = lft_tco_shape[0].y[0] - self.m1_enc_coe
                m1_y1 = lft_tco_shape[-1].y[1] + self.m1_enc_coe

                if "t" in tap_position or "b" in tap_position:
                    for shp in top_m1_shape + btm_m1_shape:
                        # update previous metal1 shape
                        shp.x[0] = m1_x0

                        # update current metal1 shape
                        if shp.y[1] < m1_y0:
                            m1_y0 = shp.y[1]

                        if shp.y[0] > m1_y1:
                            m1_y1 = shp.y[0]

                    for pin in top_pin + btm_pin:
                        # update previous pin
                        pin.pt1[0] = m1_x0

                lft_m1_shape.append(Box(self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))
                lft_pin.append(Pin(body_net, self.m1, [m1_x0, m1_y0], [m1_x1, m1_y1]))

            # update the shape of the group
            self.group.shape[self.tim] += top_tim_shape + btm_tim_shape + rgt_tim_shape + lft_tim_shape
            self.group.shape[self.tdf] += top_tdf_shape + btm_tdf_shape + rgt_tdf_shape + lft_tdf_shape
            self.group.shape[self.co] += top_tco_shape + btm_tco_shape + rgt_tco_shape + lft_tco_shape
            self.group.shape[self.m1] += top_m1_shape + btm_m1_shape + rgt_m1_shape + lft_m1_shape
            self.group.pin += top_pin + btm_pin + rgt_pin + lft_pin


    def create_boundary(self) -> None:
        # get the boundary based on the implant layer
        br_x0, br_x1, br_y0, br_y1 = self.merge_shape(self.group.shape[self.im] + self.group.shape[self.tim])

        # increase the boundary size
        size_incr = 0.5
        br_x0 -= size_incr
        br_x1 += size_incr
        br_y0 -= size_incr
        br_y1 += size_incr

        # shift all the shape to the origin
        for layer in self.group.shape:
            for shape in self.group.shape[layer]:
                shape.x[0] -= br_x0
                shape.x[1] -= br_x0
                shape.y[0] -= br_y0
                shape.y[1] -= br_y0
    
        # shift all the pin to the origin
        for pin in self.group.pin:
            pin.pt1[0] -= br_x0
            pin.pt2[0] -= br_x0
            pin.pt1[1] -= br_y0
            pin.pt2[1] -= br_y0
        
        # shift the boundary to the origin
        br_x1 -= br_x0
        br_y1 -= br_y0
        br_x0 = 0
        br_y0 = 0

        self.group.shape["boundary"] = [Box("boundary", [br_x0, br_y0], [br_x1, br_y1])]
        self.group.boundary = self.group.shape["boundary"][0]


class SUBCKT:
    """
    Sub-circuit: Layout Generation
    """
    def __init__(self, circuit: dict, name: str, group: Group) -> None:
        self.circuit = circuit
        self.name = name
        self.group = group

        self.generate_layout()


    def generate_layout(self) -> None:
        # find subcircuit (asssume only one instance) TODO: fix this
        for inst in self.group.inst:
            subckt = self.circuit[self.name].subckt[inst.id]
            break

        # get subckt name
        subckt_name = subckt.name

        # create boundary
        self.group.boundary = Box("boundary", [0, 0], [self.circuit[subckt_name].width, self.circuit[subckt_name].height])

        # create shape
        self.group.shape["inst"] = [SRef(subckt_name, [0, 0])]

        # create pin
        for pin in subckt.node:
            for layer in self.circuit[subckt_name].port[pin].shape:
                port_shapes = self.circuit[subckt_name].port[pin].shape[layer]

                for shape in port_shapes:
                    if isinstance(shape, Box):
                        net = subckt.node[pin].net
                        self.group.pin.append(Pin(net, layer, [shape.x[0], shape.y[0]], [shape.x[1], shape.y[1]]))

