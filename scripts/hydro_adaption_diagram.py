from manim import *
import numpy as np


class DTMHydrologicAdaptation(Scene):
    def construct(self):
        
        self.camera.background_color = WHITE
        
        
        # placeringen af raster cellerne
        bottom_left = [-2.5, -1.5, 0]  
        bottom_right = [2.5, -1.5, 0]  
        top_left = [-1.6, 1.3, 0]    
        top_right = [1.6, 1.3, 0]    # 
        
        # linjerne i rasteren (horisontale)
        h_lines = VGroup()
        for i in range(5):  
            ratio = i / 4
            start = [bottom_left[0] * (1 - ratio) + top_left[0] * ratio,
                     bottom_left[1] * (1 - ratio) + top_left[1] * ratio, 0]
            end = [bottom_right[0] * (1 - ratio) + top_right[0] * ratio,
                   bottom_right[1] * (1 - ratio) + top_right[1] * ratio, 0]
            
            
            h_line = Line(start=start, end=end, stroke_width=1.5)
            h_lines.add(h_line)
        
        # vertikale linjer i raster cellerne
        v_lines = VGroup()
        for j in range(5):  

            ratio = j / 4
            start = [bottom_left[0] * (1 - ratio) + bottom_right[0] * ratio,
                     bottom_left[1] * (1 - ratio) + bottom_right[1] * ratio, 0]
            end = [top_left[0] * (1 - ratio) + top_right[0] * ratio,
                   top_left[1] * (1 - ratio) + top_right[1] * ratio, 0]
            
            # 
            v_line = Line(start=start, end=end, stroke_width=1.5)
            v_lines.add(v_line)
        
        grid = VGroup(h_lines, v_lines).set_color(BLACK)
        
        # 
        line_start = np.array([top_left[0] + 0.2, top_left[1] + 0.7, 0])
        line_end = np.array([top_right[0] - 0.2, top_right[1] + 0.5, 0])
        
        # splitter linjen for at kunne lave den striplede linje
        line_third = (line_end - line_start) / 3
        
        # 
        left_line = Line(
            start=line_start,
            end=line_start + line_third,
            stroke_width=2,
            color=ORANGE
        )
        
        right_line = Line(
            start=line_end - line_third,
            end=line_end,
            stroke_width=2,
            color=ORANGE
        )
        
        # D
        middle_line = DashedLine(
            start=line_start + line_third,
            end=line_end - line_third,
            stroke_width=2,
            color=ORANGE,
            dash_length=0.1,
            dashed_ratio=0.5
        )
        
        hydrologic_line = VGroup(left_line, middle_line, right_line)

        # tekst og ornamentering ({})
        deltaz = Text("ΔZ", font_size=16, color=BLACK).next_to(middle_line, DOWN * 1.4)
        brace = BraceBetweenPoints(line_start, line_end, color=BLACK, sharpness=1, buff=0.2).next_to(middle_line, DOWN * 0.02)
        brace.scale([0.95, 0.8, 1])
        
        # finder centrum af cellerne 
        grid_points = []
        for i in range(5):  
            row_points = []
            for j in range(5):  
                ratio_v = i / 4  # 
                ratio_h = j / 4  
                
                #
                bottom_edge = [
                    bottom_left[0] * (1 - ratio_h) + bottom_right[0] * ratio_h,
                    bottom_left[1] * (1 - ratio_h) + bottom_right[1] * ratio_h,
                    0
                ]
                
                top_edge = [
                    top_left[0] * (1 - ratio_h) + top_right[0] * ratio_h,
                    top_left[1] * (1 - ratio_h) + top_right[1] * ratio_h,
                    0
                ]
                
                
                point = [
                    bottom_edge[0] * (1 - ratio_v) + top_edge[0] * ratio_v,
                    bottom_edge[1] * (1 - ratio_v) + top_edge[1] * ratio_v,
                    0
                ]
                
                row_points.append(point)
            grid_points.append(row_points)
        

        # laver kassen i toppen af diagrammet
        base_left = line_start + line_third
        base_right = line_end - line_third

        box_height = 0.5
        top_left = base_left + np.array([0, box_height, 0])
        top_right = base_right + np.array([0, box_height + 0.07, 0])

        left_side = Line(base_left, top_left, color=BLACK, stroke_width=2)
        right_side = Line(base_right, top_right, color=BLACK, stroke_width=2)
        top_side = Line(top_left, top_right, color=BLACK, stroke_width=2)


        
        # interpolation af cellernes midtpunkt
        cell_corners_z0 = [
            grid_points[2][0],
            grid_points[2][1],
            grid_points[3][0],
            grid_points[3][1],
        ]

        z0_cell_center = [
            sum([p[0] for p in cell_corners_z0]) / 4,
            sum([p[1] for p in cell_corners_z0]) / 4,
            0
        ]
        
        cell_corners_z1 = [
            grid_points[2][3],
            grid_points[2][4],
            grid_points[3][3],
            grid_points[3][4],
        ]

        z1_cell_center = [
            sum([p[0] for p in cell_corners_z1]) / 4,
            sum([p[1] for p in cell_corners_z1]) / 4,
            0
        ]

        
        # definering af pile fra celle midtpunkt til linje ende
        z0_arrow = Arrow(
            start=z0_cell_center,
            end=line_start,
            stroke_width=1.5,
            color=BLACK,
            buff=0,
            max_tip_length_to_length_ratio=0.05
        )
        
        
        z0_text = Text("Z₀", font_size=18, color=BLACK).next_to(
            z0_arrow.get_end(), LEFT, buff=0.2
        )
        
        
        z1_arrow = Arrow(
            start=z1_cell_center,
            end=line_end,
            stroke_width=1.5,
            color=BLACK,
            buff=0,
            max_tip_length_to_length_ratio=0.05
        )
        
        
        z1_text = Text("Z₁", font_size=18, color=BLACK).next_to(
            z1_arrow.get_end(), RIGHT, buff=0.2
        )
        
        box_text = Text("Hindring", font_size=12, color=BLACK).next_to(
            top_side.get_center(), UP, buff=0.05 
        )
        
        # updatering af scenen, fortælle rendereren hvad der skal tegnes. 
        self.add(grid)
        self.add(hydrologic_line)
        self.add(z0_arrow, z0_text, z1_arrow, z1_text)
        self.add(left_side, right_side, top_side, middle_line, box_text)
        self.add(deltaz, brace)
        
        # kør scriptet med renderer:  manim -s -r 4800,3600 manim.py DTMHydrologicAdaptation
        # kør scriptet uden renderer: manim -s -p manim.py DTMHydrologicAdaptation
