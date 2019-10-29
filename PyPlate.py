from enum import Enum
from string import ascii_uppercase
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm

import numpy as np
import xlsxwriter

# constants
UPPERCASE_LETTERS = list(ascii_uppercase)

# helper methods
def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class ReagentType(Enum):
    SOLID = 1
    LIQUID = 2

class Reagent(object):
    # MW in g/mol, density in g/mL
    def __init__(self, name, molecular_weight, reagent_type, density):
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError("invalid reagent name")
        self.name = name
        if not isinstance(molecular_weight, (int,float)) or molecular_weight <= 0.0:
            raise ValueError("invalid molecular weight")
        self.molecular_weight = float(molecular_weight)
        if reagent_type is None:
            raise ValueError("invalid reagent type")
        self.reagent_type = reagent_type
        if reagent_type == ReagentType.LIQUID:
            if (not isinstance(density, (int,float))) or density <= 0.0:
                raise ValueError("invalid density")
            self.density = float(density)
        elif reagent_type == ReagentType.SOLID:
            if density is not None:
                raise ValueError("cannot have density for solid reagents")
            self.density = None
        else:
            raise ValueError("unknown reagent type")

    def __str__(self):
        if self.reagent_type == ReagentType.SOLID:
            return f"{self.name} ({self.molecular_weight:.2f} g/mol)"
        elif self.reagent_type == ReagentType.LIQUID:
            return f"{self.name} ({self.molecular_weight:.2f} g/mol, {self.density:.3f} g/mL)"

    @staticmethod
    def create_solid(name, molecular_weight):
        return Reagent(name, molecular_weight, ReagentType.SOLID, None)

    @staticmethod
    def create_liquid(name, molecular_weight, density):
        return Reagent(name, molecular_weight, ReagentType.LIQUID, density)

class StockSolution(object):
    # concentration in mol/L
    # volume in mL
    def __init__(self, reagent, concentration, solvent, volume):
        if not isinstance(reagent, Reagent):
            raise ValueError("invalid reagent")
        self.reagent = reagent
        if not isinstance(concentration, (int,float)) or concentration <= 0.0:
            raise ValueError("invalid concentration")
        self.concentration = float(concentration)
        if not isinstance(solvent, Reagent):
            raise ValueError("invalid solvent, must be Reagent")
        self.solvent = solvent
        if not isinstance(volume, (int,float)) or volume <= 0.0:
            raise ValueError("invalid volume")
        self.volume = float(volume)

    # return a string containing a recipe for this stock solution
    # volume in mL
    def get_instructions_string(self):
        # (concentration mol / L) * (volume mL * L / 1000 mL) * (molecular_weight g / mol) = weight in g
        weight = self.concentration * (self.volume / 1000) * (self.reagent.molecular_weight)

        if self.reagent.reagent_type == ReagentType.SOLID:
            if weight < 1.0:
                return f"Add {weight*1000:.1f} mg of {self.reagent.name} to {self.volume:.2f} mL of {self.solvent.name}."
            else:
                return f"Add {weight:.3f} g of {self.reagent.name} to {self.volume:.2f} mL of {self.solvent.name}."
        elif self.reagent.reagent_type == ReagentType.LIQUID:
            # weight in g / density in g/mL = reagent volume in mL
            reagent_volume = weight / self.reagent.density
            if reagent_volume < 1.0:
                return f"Add {reagent_volume*1000:.3f} uL of {self.reagent.name} to {self.volume:.3f} mL of {self.solvent.name}."
            else:
                return f"Add {reagent_volume:.3f} mL of {self.reagent.name} to {self.volume:.3f} mL of {self.solvent.name}."
        else:
            raise ValueError("unknown reagent type")

    def __str__(self):
        if self.concentration > 0.1:
            return f"{self.reagent.name} ({self.concentration:.2f} M in {self.solvent.name})"
        else:
            return f"{self.reagent.name} ({self.concentration*1000.0:.1f} mM in {self.solvent.name})"

# represents a generic plate
class Plate(object):
    # name: name of plate
    # make: name of this kind of plate
    # rows: number of rows or list of names of rows
    # columns: number of columns or list of names of columns
    # max_volume_per_well: maximum volume of each well in uL
    def __init__(self, name, make, rows, columns, max_volume_per_well):
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError("invalid plate name")
        self.name = name

        if not isinstance(make, str) or len(make) == 0:
            raise ValueError("invalid plate make")
        self.make = make

        if isinstance(rows, int):
            if rows < 1:
                raise ValueError("illegal number of rows")
            self.n_rows = rows
            self.row_names = [ f"{i+1}" for i in range(rows) ]
        elif isinstance(rows, list):
            if len(rows) == 0:
                raise ValueError("must have at least one row")
            for row in rows:
                if not isinstance(row, str):
                    raise ValueError("row names must be strings")
            if len(rows) != len(set(rows)):
                raise ValueError("duplicate row names found")
            self.n_rows = len(rows)
            self.row_names = rows
        else:
            raise ValueError("rows must be int or list")

        self.max_volume_per_well = max_volume_per_well

        if isinstance(columns, int):
            if columns < 1:
                raise ValueError("illegal number of columns")
            self.n_columns = columns
            self.column_names = [ f"{i+1}" for i in range(columns) ]
        elif isinstance(columns, list):
            if len(columns) == 0:
                raise ValueError("must have at least one row")
            for column in columns:
                if not isinstance(column, str):
                    raise ValueError("row names must be strings")
            if len(columns) != len(set(columns)):
                raise ValueError("duplicate column names found")
            self.n_columns = len(columns)
            self.column_names = columns
        else:
            raise ValueError("columns must be int or list")

        self.reagents = []                                       # labels the reagents in self.moles
        self.volumes = np.zeros((self.n_rows,self.n_columns))    # in uL
        self.moles = None                                        # in micromoles, shape:(reagent, rows, columns)
        self.instructions = []                                   # list of instructions for making this plate

    def __str__(self):
        return f"{self.name} ({self.make}, {self.n_rows}x{self.n_columns}, max {self.max_volume_per_well:.0f} uL/well)"

    # add specified volume of stock to one row
    # volume: in uL
    # stock_solution: which stock to add
    # row: row name or row index (1-indexed)
    def add_stock_to_row(self, volume, stock_solution, row):
        if (not isinstance(volume, (int,float))) or volume <= 0.0:
            raise ValueError("invalid volume")
        if not isinstance(stock_solution, StockSolution):
            raise ValueError(f"expected a StockSolution, but got a {str(type(stock_solution))}")
        if isinstance(row, str):
            if row not in self.row_names:
                raise ValueError(f"row name {row} not found")
            row = self.row_names.index(row)
        elif isinstance(row, int):
            if row < 1 or row > self.n_rows:
                raise ValueError("row out of range")
            row = row - 1
        else:
            raise ValueError("must specify row as 1-indexed number or row name")

        # record this addition as an Instruction
        destinations = [ (row,column) for column in range(self.n_columns) ]
        instruction = Instruction(volume, stock_solution, destinations, self, destination_type="row")
        self.instructions.append(instruction)
        #print(instruction)

        # update the volumes
        self.volumes[row,:] += volume

        # warn if we have exceeded volumes
        current_max_volume = np.max(self.volumes)
        if np.max(self.volumes) > self.max_volume_per_well:
            print(f"Warning: exceeded maximum well volume!  (Now {current_max_volume:.0f} uL, but limit is {self.max_volume_per_well:.0f} ul).")

        # determine if we have added this reagent already
        reagent = stock_solution.reagent
        reagent_index = -1
        if reagent not in self.reagents:
            self.reagents.append(reagent)
            reagent_index = len(self.reagents)-1
            blank_array = np.zeros((1, self.n_rows, self.n_columns))
            if len(self.reagents) == 1:
                # this is the first reagent
                self.moles = blank_array
            else:
                # this is the n-th reagent
                self.moles = np.concatenate((self.moles, blank_array), axis=0)
        else:
            reagent_index = self.reagents.index(reagent)

        # update the moles
        extra_moles = volume * stock_solution.concentration
        self.moles[reagent_index,row,:] += extra_moles

    # add specified volume of stock to one column
    # volume: in uL
    # stock_solution: which stock to add
    # column: column name or column index (1-indexed)
    def add_stock_to_column(self, volume, stock_solution, column):
        if (not isinstance(volume, (int,float))) or volume <= 0.0:
            raise ValueError("invalid volume")
        if not isinstance(stock_solution, StockSolution):
            raise ValueError(f"expected a StockSolution, but got a {str(type(stock_solution))}")
        if isinstance(column, str):
            if column not in self.column_names:
                raise ValueError(f"column name {column} not found")
            column = self.column_names.index(column)
        elif isinstance(column, int):
            if column < 1 or column > self.n_columns:
                raise ValueError("column out of range")
            column = column - 1
        else:
            raise ValueError("must specify column as 1-indexed number or column name")

        # record this addition as an Instruction
        destinations = [ (row,column) for row in range(self.n_rows) ]
        instruction = Instruction(volume, stock_solution, destinations, self, destination_type="column")
        self.instructions.append(instruction)
        #print(instruction)

        # update the volumes
        self.volumes[:,column] += volume

        # warn if we have exceeded volumes
        current_max_volume = np.max(self.volumes)
        if np.max(self.volumes) > self.max_volume_per_well:
            print(f"Warning: exceeded maximum well volume!  (Now {current_max_volume:.0f} uL, but limit is {self.max_volume_per_well:.0f} ul).")

        # determine if we have added this reagent already
        reagent = stock_solution.reagent
        reagent_index = -1
        if reagent not in self.reagents:
            self.reagents.append(reagent)
            reagent_index = len(self.reagents)-1
            blank_array = np.zeros((1, self.n_rows, self.n_columns))
            if len(self.reagents) == 1:
                # this is the first reagent
                self.moles = blank_array
            else:
                # this is the n-th reagent
                self.moles = np.concatenate((self.moles, blank_array), axis=0)
        else:
            reagent_index = self.reagents.index(reagent)

        # update the moles
        extra_moles = volume * stock_solution.concentration
        self.moles[reagent_index,:,column] += extra_moles

    # converts a location tuple into a canonical form:
    # (row, column) (both zero-indexed)
    def location_tuple_to_index_form(self, location):
        if not isinstance(location, tuple):
            raise ValueError("location must be a tuple")
        if not len(location) == 2:
            raise ValueError("locations must be tuples of length 2")

        row, column = location

        # convert row to row index
        if isinstance(row, str):
            if row in self.row_names:
                row = self.row_names.index(row)
            else:
                if is_integer(row) and int(row) > 0 and int(row) <= self.n_rows:
                    row = int(row) - 1
                else:
                    raise ValueError(f"'{row}' in location {str(location)} does not correspond to a valid row")
        elif isinstance(row, int):
            if row < 1 or row > self.n_rows:
                raise ValueError("row {row} out of range for {str(location)}")
            row = row - 1
        else:
            raise ValueError(f"error parsing {str(location)}: must specify row as 1-indexed number or row name")

        # convert column to column index
        if isinstance(column, str):
            if column in self.column_names:
                column = self.column_names.index(column)
            else:
                if is_integer(column) and int(column) > 0 and int(column) <= self.n_columns:
                    column = int(column) - 1
                else:
                    raise ValueError(f"'{column}' in location {str(location)} does not correspond to a valid column")
        elif isinstance(column, int):
            if column < 1 or column > self.n_columns:
                raise ValueError("column {column} out of range for {str(location)}")
            column = column - 1
        else:
            raise ValueError(f"error parsing {str(location)}: must specify column as 1-indexed number or column name")

        result = (row,column)
        return result

    # add specified volume of stock to specified wells
    # volume: in uL
    # stock_solution: which stock to add
    # destinations: (row,column) or [ (row,column) ], can specify 1-indexed locations or row/column names like "A:1"
    def add_stock_to_wells(self, volume, stock_solution, destinations):
        if (not isinstance(volume, (int,float))) or volume <= 0.0:
            raise ValueError("invalid volume")
        if not isinstance(stock_solution, StockSolution):
            raise ValueError(f"expected a StockSolution, but got a {str(type(stock_solution))}")

        # construct list of destinations: [ (row, column) ] with 0-indexing
        new_destinations = []
        if isinstance(destinations, (tuple, str)):
            destinations = [ destinations ]
        if isinstance(destinations, list):
            for destination in destinations:
                if isinstance(destination, str):
                    fields = destination.split(":")
                    if len(fields) != 2:
                        raise ValueError(f"invalid location string {destination}")
                    destination = tuple(fields)
                if isinstance(destination, tuple):
                    destination = self.location_tuple_to_index_form(destination)
                else:
                    raise ValueError(f"unrecognized location tuple {str(destination)}")
                new_destinations.append(destination)
        else:
            raise ValueError("destinations must be a single tuple or list of tuples")

        # record this addition as an Instruction
        instruction = Instruction(volume, stock_solution, new_destinations, self, destination_type="misc")
        self.instructions.append(instruction)
        #print(instruction)

        # update the volumes
        for row,column in new_destinations:
            self.volumes[row,column] += volume

        # warn if we have exceeded volumes
        current_max_volume = np.max(self.volumes)
        if np.max(self.volumes) > self.max_volume_per_well:
            print(f"Warning: exceeded maximum well volume!  (Now {current_max_volume:.0f} uL, but limit is {self.max_volume_per_well:.0f} ul).")

        # determine if we have added this reagent already
        reagent = stock_solution.reagent
        reagent_index = -1
        if reagent not in self.reagents:
            self.reagents.append(reagent)
            reagent_index = len(self.reagents)-1
            blank_array = np.zeros((1, self.n_rows, self.n_columns))
            if len(self.reagents) == 1:
                # this is the first reagent
                self.moles = blank_array
            else:
                # this is the n-th reagent
                self.moles = np.concatenate((self.moles, blank_array), axis=0)
        else:
            reagent_index = self.reagents.index(reagent)

        # update the moles
        extra_moles = volume * stock_solution.concentration
        for row,column in new_destinations:
            self.moles[reagent_index,row,column] += extra_moles

    # create an Excel spreadsheet summarizing this plate
    def to_excel(self, filename, colormap='plasma', do_not_overwrite=False):
        # delete file if it exists
        print(f"Writing plate to {filename}...", end='')
        if os.path.exists(filename):
            if do_not_overwrite:
                raise ValueError(f"Error: {filename} already exists.")
            else:
                os.remove(filename)

        # create file
        workbook = xlsxwriter.Workbook(filename)
        cm = plt.get_cmap(colormap)
        normalizer = mpl.colors.Normalize(vmin=0.0, vmax=self.max_volume_per_well)
        def get_colors(volume):
            rgba = cm(normalizer(volume))
            r,g,b,a = rgba
            background_color = mpl.colors.to_hex(rgba)
            brightness = (.299 * r) + (.587 * g) + (.114 * b)
            if brightness < 0.5:
                font_color = "#FFFFFF"
            else:
                font_color = "#000000"
            #print(brightness,background_color,font_color)
            return background_color, font_color

        # total volumes
        volumes_worksheet = workbook.add_worksheet(self.name)
        volumes_worksheet.set_column(0,0,10)
        bold = workbook.add_format({'bold':True})
        volumes_worksheet.write(0,0,"Volumes (uL)")
        for i,column_name in enumerate(self.column_names):
            volumes_worksheet.write_string(0,i+1,column_name,bold)
        for i,row_name in enumerate(self.row_names):
            volumes_worksheet.write_string(i+1,0,row_name,bold)
        for row in range(self.n_rows):
            for column in range(self.n_columns):
                volume = self.volumes[row,column]
                bg_color, font_color = get_colors(volume)
                cell_format = workbook.add_format()
                cell_format.set_bg_color(bg_color)
                cell_format.set_font_color(font_color)
                if volume > self.max_volume_per_well:
                    cell_format.set_border(5)
                    cell_format.set_border_color("#FF0000")
                volumes_worksheet.write(row+1, column+1, volume, cell_format)

	# instructions

	# reagents


        # reagent concentrations

        # update status
        workbook.close()
        print("done.")

# represents an addition of a StockSolution to a Plate
class Instruction(object):
    # volume: in uL
    # stock_solution: StockSolution
    # destinations: list of 0-indexed (row, column) tuples
    # destination_type: = 
    def __init__(self, volume, stock_solution, destinations, plate, destination_type="misc"):
        self.volume = volume
        self.stock_solution = stock_solution
        self.destinations = destinations
        stock_name = stock_solution.reagent.name
        stock_concentration = stock_solution.concentration * 1000.0
        stock_solvent = stock_solution.solvent.name

        # generate string that explains how to perform this addition in words
        # no checking is done to see if destinations and destination_type are consistent
        if destination_type == "row":
            row_index = destinations[0][0]
            row_name = plate.row_names[row_index]
            if row_name == str(row_index+1):
                instruction_string = f"Add {volume} uL of {stock_name} ({stock_concentration} mM in {stock_solvent}) to row {row_name}."
            else:
                instruction_string = f"Add {volume} uL of {stock_name} ({stock_concentration} mM in {stock_solvent}) to row {row_name} (row number {row_index+1})."
        elif destination_type == "column":
            column_index = destinations[0][1]
            column_name = plate.column_names[column_index]
            if column_name == str(column_index+1):
                instruction_string = f"Add {volume} uL of {stock_name} ({stock_concentration} mM in {stock_solvent}) to column {column_name}."
            else:
                instruction_string = f"Add {volume} uL of {stock_name} ({stock_concentration} mM in {stock_solvent}) to column {column_name} (column number {column_index+1})."
        elif destination_type == "misc":
            instruction_string = f"Add {volume} uL of {stock_name} ({stock_concentration} mM in {stock_solvent}) to:\n   "
            count = 0
            for i,(row,column) in enumerate(destinations):
                row_name = plate.row_names[row]
                column_name = plate.column_names[column]
                well = f"{row_name}{column_name}"
                instruction_string += f"{well:6s} "
                count += 1
                if count > 20 and i != len(destinations)-1:
                    count = 0
                    instruction_string += "\n   "
        else:
            raise ValueError("unknown destination type")
        self.instruction_string = instruction_string

    def __str__(self):
        return self.instruction_string

# represents a 96 well plate
class Generic96WellPlate(Plate):
    def __init__(self, name, max_volume_per_well):
        make = "generic 96 well plate"
        rows = UPPERCASE_LETTERS[:8]
        columns = 12
        super().__init__(name, make, rows, columns, max_volume_per_well)

# represents a 384 well plate
class Generic384WellPlate(Plate):
    def __init__(self, name, max_volume_per_well):
        make = "generic 384 well plate"
        rows = UPPERCASE_LETTERS[:16]
        columns = 24
        super().__init__(name, make, rows, columns, max_volume_per_well)

