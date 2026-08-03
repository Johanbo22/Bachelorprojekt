from manim import *
import numpy

class GridPlusBuildingIcon(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        grid = self.make_grid()
        grid.move_to(LEFT * 3.6)
        
        plus = self.make_plus()
        plus.move_to(ORIGIN)
        
        building = self.make_building()
        building.move_to(RIGHT * 3.6)
        
        self.add(grid, plus, building)
    
    def make_grid(self, n_lines=6, size=4.0, stroke_w=5):
        group = VGroup()
        spacing = size / (n_lines - 1)
        
        for i in range(n_lines):
            y = -size / 2 + i * spacing
            h_line = Line(
                LEFT * size / 2,
                RIGHT * size / 2,
                stroke_width=stroke_w, color=BLACK, cap_style=CapStyleType.ROUND
            )
            h_line.move_to([0, y, 0])
            group.add(h_line)
            
        for i in range(n_lines):
            x = -size / 2 + i * spacing
            v_line = Line(
                DOWN * size / 2, 
                UP * size / 2,
                stroke_width=stroke_w, color=BLACK,
                cap_style=CapStyleType.ROUND
            )
            v_line.move_to([x, 0, 0])
            group.add(v_line)
        
        iso_matrix = numpy.array([
            [1.0, -0.5],
            [0.0, 0.6]
        ])
        group.apply_matrix(iso_matrix)
        
        return group
    
    def make_plus(self, size=1.0, thickness=0.28):
        h = Rectangle(
            width=size, height=thickness,
            color=RED, fill_color=RED, fill_opacity=1,
            stroke_width=0
        )
        v = Rectangle(
            width=thickness, height=size,
            color=RED, fill_color=RED, fill_opacity=1,
            stroke_width=0
        )
        return VGroup(h, v)

    def make_buildings(self):
        group = VGroup()
        stroke_w = 8
        
        tall = Rectangle(
            width=2.0,
            height=3.4,
            color=BLACK,
            stroke_width=stroke_w,
            fill_opacity=0
        )
        tall.move_to(LEFT * 0.35 + UP * 0.0)
        
        short = Rectangle(
            width=1.3,
            height=2.2,
            color=BLACK,
            stroke_width=stroke_w,
            fll_opacity=0
        )
        short.move_to([tall.get_right()[0] + short.width / 2, 0, 0])
        short.align_to(tall, DOWN)
        
        group.add(tall, short)
        
        win_size = 0.34
        cols_tall = [tall.get_left()[0] + 0.5, tall.get_left()[0] + 1.15]
        rows_tall_y = numpy.linspace(tall.get_top()[1] - 0.55, tall.get_bottom()[1] + 0.55, 4)
        
        for y in rows_tall_y:
            for x in cols_tall:
                win = Square(
                    side_length=win_size,
                    color=BLACK,
                    stroke_width=stroke_w * 0.8,
                    fill_opacity=0
                )
                win.move_to([x, y, 0])
                group.add(win)
        
        col_short = short.get_center()[0]
        rows_short_y = numpy.linspace(short.get_top()[1] - 0.45, short.get_bottom()[1] + 0.45, 3)
        
        for y in rows_short_y:
            win = Square(
                side_length=win_size,
                color=BLACK,
                stroke_width=stroke_w * 0.8,
                fill_opacity=0
            )
            win.move_to([col_short, y, 0])
            group.add(win)

        return group
