###############################
# DESCRIPTION
###############################
## Construct patterns for a fabrication process with PMMA.
## Author: Ryan Thy Huynh
## Last updated: 4/3/2024
###############################


###############################
# IMPORT PACKAGES
###############################

# Import packages
import gdspy
import os
# Directory
os.chdir('/Users/thuynh/Documents/ross-group/gdspy/hexagonal_patterns')

###############################
# FUNCTIONS
###############################

def hexagon(x_center, y_center, radius, pattern):
    """
    x_center, y_center: coordinates of the center
    radius: the radius of an outermost hexagon
    pattern: the current hexagonal pattern

    Return: the pattern that overllaped pattern between the new hexagon and the current pattern
    """
    h1 = gdspy.Round((x_center,y_center), radius, number_of_points=6)
    pattern_temp = gdspy.boolean(h1, pattern, 'xor')
    return pattern_temp

def hexagon_pattern(x_center, y_center, num_of_hexagon, radius, trench_width, pattern):
    """
    center_x_coor, center_y_coor: 
    number_of_loops: the number of loops
        + Even: the middle part will be red --> PMMA will be exposed
        + Odd: the middle part will be white --> PMMA will not be exposed
    radius: intial radius
    trench_width: the spacing between two hexagons
    pattern: the current pattern

    Return: the pattern with multiple hexagons
    """
    if num_of_hexagon == 0:
        return hexagon(x_center, y_center, radius, pattern)
    else:
        pattern = hexagon(x_center, y_center, radius, pattern)
        return hexagon_pattern(x_center, y_center, num_of_hexagon - 1, radius + trench_width, trench_width, pattern)
    
def rectangle_horizontal_array(x_top, y_top, length, width, dx, num_horizontal_patterns, main_cell):
    "Return a horizontal array of rectangle pattern (length x width) with the spacing of dx between each pattern"
    # Determine the coordinates of a bottom right corner of the rectangle
    x_bot = x_top + length
    y_bot = y_top + width
    # Create a rectangle pattern
    rectangle = gdspy.Rectangle((x_top, y_top), (x_bot, y_bot))
    # Add the pattern into the cell
    main_cell.add(rectangle)
    if num_horizontal_patterns == 1:
        return main_cell
    else:
        return rectangle_horizontal_array(x_top + length + dx, y_top, length, width, dx, num_horizontal_patterns - 1, main_cell)

def rectangle_pattern(x_top, y_top, length, width, dx, dy, num_horizontal_patterns, num_vertical_array, main_cell):
    " Return a matrix of patterns (num_horizontal x num_vertical) of rectangular patterns (length x width) with the horizontal spacing of dx and vertical spacing of dy."
    if num_vertical_array == 1:
        return rectangle_horizontal_array(x_top, y_top, length, width, dx, num_horizontal_patterns, main_cell)
    else:
        pattern = rectangle_horizontal_array(x_top, y_top, length, width, dx, num_horizontal_patterns, main_cell)
        return rectangle_pattern(x_top, y_top + width + dy, length, width, dx, dy, num_horizontal_patterns, num_vertical_array - 1, pattern)
    
def rotate_pattern(main_cell, pattern_cell, x_coor, y_coor, magnification_value, rotation_angle):
    "Rotate the cell in specific angle with optional enlargement"
    # Create a reference for the pattern cell
    ref = gdspy.CellReference(pattern_cell, origin = (x_coor, y_coor), magnification = magnification_value, rotation = rotation_angle)
    return main_cell.add(ref)
    
def horizontal_rotated_copy(main_cell, pattern_cell, x_coor, y_coor, magnification_value, rotation_angle, dx, num_of_horizontal_copies):
    "Copy the sample with different angles"
    # Rotate a pattern
    rotate_pattern(main_cell, pattern_cell, x_coor, y_coor, magnification_value, rotation_angle)
    if num_of_horizontal_copies == 1:
        return main_cell
    else:
        return horizontal_rotated_copy(main_cell, pattern_cell, x_coor + dx , y_coor, magnification_value, rotation_angle, dx, num_of_horizontal_copies - 1)

def rotation_matrix(main_cell, pattern_cell, x_coor, y_coor, magnification_value, start_angle, final_angle, rotation_angle_increment, dx, dy, num_of_horizontal_copies):
    "Create a matrix of rotated patterns in different angles vertically."
    horizontal_rotated_copy(main_cell, pattern_cell, x_coor, y_coor, magnification_value, start_angle, dx, num_of_horizontal_copies)
    if start_angle >= final_angle:
        return main_cell
    else:
        return rotation_matrix(main_cell, pattern_cell, x_coor, y_coor + dy, magnification_value, start_angle + rotation_angle_increment, final_angle, rotation_angle_increment, dx, dy, num_of_horizontal_copies)

def dot_pattern(x_coor, y_coor, radius, tolerance, substrate_pattern):
    """Add a dot pattern at (x_coor, y_coor) with a radius of 'radius' into a substrate pattern"""
    # Create a dot pattern
    dot = gdspy.Round((x_coor, y_coor), radius, tolerance)
    # Add the dot pattern to the substrate pattern
    new_substrate_pattern = gdspy.boolean(substrate_pattern, dot, 'xor')
    return new_substrate_pattern

def horizontal_dot_pattern(x_coor, y_coor, radius, tolerance, dx, number_of_horizontal_copies, substrate_pattern):
    """Add a horizontal dot pattern into a substrate pattern"""
    # Add a dot pattern into the substrate pattern
    new_substrate_pattern = dot_pattern(x_coor, y_coor, radius, tolerance, substrate_pattern)
    if number_of_horizontal_copies == 1:
        return new_substrate_pattern
    else:
        new_x_coor = x_coor + radius + dx + radius
        return horizontal_dot_pattern(new_x_coor, y_coor, radius, tolerance, dx, number_of_horizontal_copies - 1, new_substrate_pattern)
    
def horizontal_dot_matrix(x_coor, y_coor, radius, tolerance, dx, dy, number_of_horizontal_copies, number_of_vertical_copies, substrate_pattern):
    """Add a matrix of dot patterns into substrate pattern"""
    # Add a horizontal dot array into a substrate pattern
    new_substrate_pattern = horizontal_dot_pattern(x_coor, y_coor, radius, tolerance, dx, number_of_horizontal_copies, substrate_pattern)
    if number_of_vertical_copies == 1:
        return new_substrate_pattern
    else:
        new_y_coor = y_coor + radius + dy + radius
        return horizontal_dot_matrix(x_coor, new_y_coor, radius, tolerance, dx, dy, number_of_horizontal_copies, number_of_vertical_copies - 1, new_substrate_pattern)
    
###############################
# ADDITIONAL FUNCTIONS
###############################

    
def hexagon_array(center_x_coor, center_y_coor, number_of_loops, radius, trench_width, trench_width_increment, 
                                                 dx, dy, number_of_patterns_x, pattern, cell):
    """
    Add new patterns into the cell with the increasing trench width.
    trench_width_increment: differece in size between each pattern. The second hexagon has larger width than the first one.
    dx: distance to move in the x-direction
    dy: distance to move in the y_direction
    number_of_patterns: number of patterns in one horizontal cell
    
    Return a cell with horizonal_cell_array
    """
    current_pattern = hexagon_pattern(center_x_coor, center_y_coor, number_of_loops, radius, trench_width, pattern)
    if number_of_patterns_x == 1:      
        return cell.add(current_pattern)
    else:
        new_x_coor = center_x_coor + dx
        new_y_coor = center_y_coor + dy
        new_trench_width = trench_width + trench_width_increment
        new_cell = cell.add(current_pattern)
        return hexagon_array(new_x_coor, new_y_coor, number_of_loops, radius, new_trench_width, trench_width_increment, dx, dy, number_of_patterns_x - 1, pattern, new_cell)

def quadrant_cell_array(center_x_coor, center_y_coor, number_of_loops, radius, trench_width, trench_width_increment, 
                                                 dx, dy, number_of_patterns_x, number_of_patterns_y, pattern, cell):
    if number_of_patterns_y == 1:
        return hexagon_array(center_x_coor, center_y_coor, number_of_loops, radius, trench_width, trench_width_increment, 
                                                 dx, 0, number_of_patterns_x, pattern, cell)
    else:
        # Make a line of copies
        current_cell = hexagon_array(center_x_coor, center_y_coor, number_of_loops, radius, trench_width, trench_width_increment, 
                                                 dx, 0, number_of_patterns_x, pattern, cell)
        # Move y down dy to create another line of copies
        new_y_coor = center_y_coor + dy
        return quadrant_cell_array(center_x_coor, new_y_coor, number_of_loops, radius, trench_width, trench_width_increment, 
                                                 dx, dy, number_of_patterns_x, number_of_patterns_y - 1, pattern, current_cell)


###############################
# MAIN CODES
###############################

# The GDSII file is called a library, which contains multiple cells.
lib = gdspy.GdsLibrary()
# Define a main cell
main = lib.new_cell('main')

# Define pattern cells
hexagon_cell = lib.new_cell('hexagon')

# CFO = 0.05 um, BFO = 0.05 um
rect_1 = lib.new_cell('rect_1')
rect_mat_1 = lib.new_cell('rect_mat_1')
rect_mat_1a = lib.new_cell('rect_mat_1a')

# CFO = 0.05 um, BFO = 0.1 um
rect_2 = lib.new_cell('rect_2')
rect_mat_2 = lib.new_cell('rect_mat_2')
rect_mat_2a = lib.new_cell('rect_mat_2a')

# CFO = 0.05 um, BFO = 0.15 um 
rect_3 = lib.new_cell('rect_3')
rect_mat_3 = lib.new_cell('rect_mat_3')
rect_mat_3a = lib.new_cell('rect_mat_3a')

# CFO = 0.1 um, BFO = 0.1 um
rect_4 = lib.new_cell('rect_4')
rect_mat_4 = lib.new_cell('rect_mat_4')
rect_mat_4a = lib.new_cell('rect_mat_4a')

# CFO = 0.1 um, BFO = 0.15 um
rect_5 = lib.new_cell('rect_5')
rect_mat_5 = lib.new_cell('rect_mat_5')
rect_mat_5a = lib.new_cell('rect_mat_5a')

# CFO = 0.1 um, BFO = 0.2 um
rect_6 = lib.new_cell('rect_6')
rect_mat_6 = lib.new_cell('rect_mat_6')
rect_mat_6a = lib.new_cell('rect_mat_6a')

# CFO = 0.1 um, BFO = 0.25 um
rect_7 = lib.new_cell('rect_7')
rect_mat_7 = lib.new_cell('rect_mat_7')
rect_mat_7a = lib.new_cell('rect_mat_7a')

###############################
# CREATE PATTERNS
###############################
# A hexagonal pattern
pattern_temp = None
hexagon_array(center_x_coor = 0, center_y_coor = -60, 
              number_of_loops = 40, 
              radius = 0.5, trench_width = 0.05, trench_width_increment = 0.02, 
              dx = 40, dy = 0, 
              number_of_patterns_x = 12, 
              pattern = pattern_temp, 
              cell = hexagon_cell)
hexagon_ref = gdspy.CellReference(hexagon_cell, (0, 0))

### CFO = 0.05 um, BFO = 0.05 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.05, 
                  dx = 0, dy = 0.05, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_1)
rect_mat_cell_1 = rotation_matrix(main_cell = rect_mat_1, pattern_cell = rect_1, 
                       x_coor = 0, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_1_35p27 = horizontal_rotated_copy(main_cell = rect_mat_1a, pattern_cell = rect_1, 
                                                    x_coor = 0, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_1_54p74 = horizontal_rotated_copy(main_cell = rect_mat_1a, pattern_cell = rect_1, 
                                                    x_coor = 0, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.05 um, BFO = 0.1 um ###

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.1, 
                  dx = 0, dy = 0.05, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_2)
rect_mat_cell_2 = rotation_matrix(main_cell = rect_mat_2, pattern_cell = rect_2, 
                       x_coor = 70, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_2_35p27 = horizontal_rotated_copy(main_cell = rect_mat_2a, pattern_cell = rect_2, 
                                                    x_coor = 70, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_2_54p74 = horizontal_rotated_copy(main_cell = rect_mat_2a, pattern_cell = rect_2, 
                                                    x_coor = 70, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.05 um, BFO = 0.15 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.15, 
                  dx = 0, dy = 0.05, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_3)
rect_mat_cell_3 = rotation_matrix(main_cell = rect_mat_3, pattern_cell = rect_3, 
                       x_coor = 140, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_3_35p27 = horizontal_rotated_copy(main_cell = rect_mat_3a, pattern_cell = rect_3, 
                                                    x_coor = 140, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_3_54p74 = horizontal_rotated_copy(main_cell = rect_mat_3a, pattern_cell = rect_3, 
                                                    x_coor = 140, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.1 um, BFO = 0.1 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.1, 
                  dx = 0, dy = 0.1, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_4)
rect_mat_cell_4 = rotation_matrix(main_cell = rect_mat_4, pattern_cell = rect_4, 
                       x_coor = 210, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_4_35p27 = horizontal_rotated_copy(main_cell = rect_mat_4a, pattern_cell = rect_4, 
                                                    x_coor = 210, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_4_54p74 = horizontal_rotated_copy(main_cell = rect_mat_4a, pattern_cell = rect_4, 
                                                    x_coor = 210, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.1 um, BFO = 0.15 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.15, 
                  dx = 0, dy = 0.1, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_5)
rect_mat_cell_5 = rotation_matrix(main_cell = rect_mat_5, pattern_cell = rect_5, 
                       x_coor = 280, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_5_35p27 = horizontal_rotated_copy(main_cell = rect_mat_5a, pattern_cell = rect_5, 
                                                    x_coor = 280, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_5_54p74 = horizontal_rotated_copy(main_cell = rect_mat_5a, pattern_cell = rect_5, 
                                                    x_coor = 280, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.1 um, BFO = 0.2 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.2, 
                  dx = 0, dy = 0.1, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_6)
rect_mat_cell_6 = rotation_matrix(main_cell = rect_mat_6, pattern_cell = rect_6, 
                       x_coor = 350, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_6_35p27 = horizontal_rotated_copy(main_cell = rect_mat_6a, pattern_cell = rect_6, 
                                                    x_coor = 350, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_6_54p74 = horizontal_rotated_copy(main_cell = rect_mat_6a, pattern_cell = rect_6, 
                                                    x_coor = 350, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)

### CFO = 0.1 um, BFO = 0.25 um ###

# Rectangular pattern matrix, rotation angles from 0 to 90 degree with 15 degree increment

rectangle_pattern(x_top = 0, y_top = 0, 
                  length = 15, width = 0.25, 
                  dx = 0, dy = 0.1, 
                  num_horizontal_patterns = 1, num_vertical_array = 20, 
                  main_cell = rect_7)
rect_mat_cell_7 = rotation_matrix(main_cell = rect_mat_7, pattern_cell = rect_7, 
                       x_coor = 420, y_coor = 0, 
                       magnification_value = 1, 
                       start_angle = 0, 
                       final_angle = 90, 
                       rotation_angle_increment = 15, 
                       dx = 20, 
                       dy = 20, 
                       num_of_horizontal_copies = 2)

# Rectangular pattern with rotation angles 35.27 and 54.74

rect_mat_cell_7_35p27 = horizontal_rotated_copy(main_cell = rect_mat_7a, pattern_cell = rect_7, 
                                                    x_coor = 420, y_coor = -20, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 35.27, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)
rect_mat_cell_7_54p74 = horizontal_rotated_copy(main_cell = rect_mat_7a, pattern_cell = rect_7, 
                                                    x_coor = 420, y_coor = -40, 
                                                    magnification_value = 1, 
                                                    rotation_angle = 54.74, 
                                                    dx = 20, 
                                                    num_of_horizontal_copies = 2)



# Dot patterns with the spacing 0.05
rectangular_substrate_pattern = gdspy.Rectangle((160, -70), (170, -80))
new_dot_pattern = horizontal_dot_matrix(x_coor = 161, y_coor = -79, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.05, dy = 0.05, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = rectangular_substrate_pattern)
# Dot pattern with the spacing 0.0625
new_dot_pattern_1 = horizontal_dot_matrix(x_coor = 161, y_coor = -76, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.0625, dy = 0.0625, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern)

# Dot pattern with the spacing 0.075
new_dot_pattern_2 = horizontal_dot_matrix(x_coor = 161, y_coor = -73, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.075, dy = 0.075, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern_1)

# Dot pattern with the spacing 0.0875
new_dot_pattern_3 = horizontal_dot_matrix(x_coor = 164, y_coor = -79, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.0875, dy = 0.0875, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern_2)

# Dot pattern with the spacing 0.01
new_dot_pattern_4 = horizontal_dot_matrix(x_coor = 164, y_coor = -76, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.1, dy = 0.1, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern_3)

# Dot pattern with the spacing 0.0125
new_dot_pattern_5 = horizontal_dot_matrix(x_coor = 164, y_coor = -73, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.125, dy = 0.125, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern_4)

# Dot pattern with the spacing 0.015
new_dot_pattern_6 = horizontal_dot_matrix(x_coor = 167, y_coor = -79, 
                                        radius = 0.05, tolerance = 0.0001, 
                                        dx = 0.15, dy = 0.15, 
                                        number_of_horizontal_copies = 11, number_of_vertical_copies = 11, 
                                        substrate_pattern = new_dot_pattern_5)

###############################
# DISPLAY PATTERNS
###############################

# Add all patterns to main cell

# Hexagon
main.add(hexagon_ref)

### CFO = 0.05 um, BFO = 0.05 um ###
main.add(rect_mat_cell_1)
main.add(rect_mat_1a)

### CFO = 0.05 um, BFO = 0.1 um ###
main.add(rect_mat_cell_2)
main.add(rect_mat_2a)

### CFO = 0.05 um, BFO = 0.15 um ###
main.add(rect_mat_cell_3)
main.add(rect_mat_3a)

### CFO = 0.1 um, BFO = 0.1 um ###
main.add(rect_mat_cell_4)
main.add(rect_mat_4a)

### CFO = 0.1 um, BFO = 0.15 um ###
main.add(rect_mat_cell_5)
main.add(rect_mat_5a)

### CFO = 0.1 um, BFO = 0.2 um ###
main.add(rect_mat_cell_6)
main.add(rect_mat_6a)

### CFO = 0.1 um, BFO = 0.25 um ###
main.add(rect_mat_cell_7)
main.add(rect_mat_7a)

# Dot pattern
main.add(new_dot_pattern_6)

# Save the library in a file called 'first.gds'.
lib.write_gds("fab_pattern")

# Optionally, save an image of the cell as SVG.
main.write_svg('fab_pattern.svg')

# Display all cells using the internal viewer.
#gdspy.LayoutViewer()

os._exit(00)