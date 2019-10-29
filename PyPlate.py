from enum import Enum
from string import ascii_uppercase
import os
from collections import OrderedDict

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

# represents a chemical that will be added to solvent to make stock solutions
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

# represents a solvent for stock solutions
class Solvent(object):
    # name: name of solvent
    # volume: volume in mL
    def __init__(self, name, volume):
        if not isinstance(name, str):
            raise ValueError("solvent name must be string")
        if len(name) == 0:
            raise ValueError("solvent has zero-length name")
        self.name = name
        if not isinstance(volume, (int,float)):
            raise ValueError("expected number for volume")
        if volume <= 0.0:
            raise ValueError("volume must be positive")
        self.volume = volume

    def __str__(self):
        return f"{self.name} (solvent)"

# represents a solution of a reagent in a solvent
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
        if not isinstance(solvent, Solvent):
            raise ValueError(f"invalid solvent, must be Reagent (got {str(type(solvent))})")
        self.solvent = solvent
        if not isinstance(volume, (int,float)) or volume <= 0.0:
            raise ValueError("invalid volume")
        self.volume = float(volume)

    # return a string containing a recipe for this stock solution
    # volume in mL
    def get_instructions_string(self):
        if self.reagent.reagent_type == ReagentType.SOLID:
            # for solids, assume that the added solid contributes zero volume to the solution

            # (concentration mol / L) * (volume mL * L / 1000 mL) * (molecular_weight g / mol) = weight in g
            weight = self.concentration * (self.volume / 1000) * (self.reagent.molecular_weight)
            weight_string = f"{weight:.3f} g" if weight > 1.0 else f"{weight*1000.0:.1f} mg"
            volume_string = f"{self.volume:.3f} mL" if self.volume > 1.0 else f"{self.volume*1000.0:.1f} uL"

            return f"Add {weight_string} of {self.reagent.name} to {volume_string} of {self.solvent.name}."

        elif self.reagent.reagent_type == ReagentType.LIQUID:
            # for liquids, assume that the volumes of the reagent and solvent are additive

            # weight in g / density in g/mL = reagent volume in mL
            weight = self.concentration * (self.volume / 1000) * (self.reagent.molecular_weight)
            reagent_volume = weight / self.reagent.density
            required_solvent = self.volume - reagent_volume
            reagent_volume_string = f"{reagent_volume:.3f} mL" if reagent_volume > 1.0 else f"{reagent_volume*1000.0:.1f} uL"
            required_solvent_string = f"{required_solvent:.3f} mL" if required_solvent > 1.0 else f"{required_solvent*1000.0:.1f} uL"

            return f"Add {reagent_volume_string} of {self.reagent.name} to {required_solvent_string} of {self.solvent.name}."
        else:
            raise ValueError("unknown reagent type")

    def __str__(self):
        name = self.reagent.name
        if self.concentration > 0.1:
            return f"{name} ({self.concentration:.2f} M in {self.solvent.name})"
        else:
            return f"{name} ({self.concentration*1000.0:.1f} mM in {self.solvent.name})"

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
                if len(row.strip()) == 0:
                    raise ValueError("zero length strings are not allowed as column labels")
                if is_integer(row):
                    raise ValueError(f"please don't confuse me with row names that are integers ({row})")
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
                if len(column.strip()) == 0:
                    raise ValueError("zero length strings are not allowed as column labels")
                if is_integer(column):
                    raise ValueError(f"please don't confuse me with column names that are integers({column})")
            if len(columns) != len(set(columns)):
                raise ValueError("duplicate column names found")
            self.n_columns = len(columns)
            self.column_names = columns
        else:
            raise ValueError("columns must be int or list")

        # list of all reagents used, in the ordered added
        self.reagents = []

        # how much volume is currently in each well (in uL)
        self.volumes = np.zeros((self.n_rows,self.n_columns))

        # how many moles of each reagent are in each well (in micromoles, shape:(reagent, rows, columns))
        # note that only Reagent moles are tracked (Solvent moles are not tracked)
        # the ordering in axis 0 parallels the order in self.reagents
        self.moles = None

        # list of instructions for making this plate
        # each instruction is a map from a StockSolution or Solvent to a canonical dispense map
        # canonical dispense maps are dictionaries from 0-indexed (row,column) tuples to volumes in uL
        self.instructions = []

        # how much of each StockSolution or Solvent was used to make this plate (in uL)
        # map from item --> volume
        self.volumes_used = OrderedDict()

    def __str__(self):
        return f"{self.name} ({self.make}, {self.n_rows}x{self.n_columns}, max {self.max_volume_per_well:.0f} uL/well)"

    # converts a location tuple into a canonical form
    #
    # inputs are assumed to be 2-tuples
    # components can be row/column labels or 1-indexed locations
    #
    # examples:
    # (0,1) is already in canonical form
    # ("A",1) --> (0,0)
    # ("B","2") --> (1,1)
    def get_canonical_form(self, location):
        if not isinstance(location, tuple):
            raise ValueError("location must be a tuple")
        if not len(location) == 2:
            raise ValueError("locations must be tuples of length 2")

        row, column = location

        # convert row to row index
        if isinstance(row, str):
            if len(row) == 0:
                raise ValueError(f"empty row in {location}")
            elif row in self.row_names:
                row = self.row_names.index(row)
            else:
                if is_integer(row) and int(row) > 0 and int(row) <= self.n_rows:
                    row = int(row) - 1
                else:
                    raise ValueError(f"'{row}' in location {str(location)} does not correspond to a valid row")
        elif isinstance(row, int):
            if row < 1 or row > self.n_rows:
                raise ValueError(f"row {row} out of range for {str(location)}")
            row = row - 1
        else:
            raise ValueError(f"error parsing {str(location)}: must specify row as 1-indexed number or row name")

        # convert column to column index
        if isinstance(column, str):
            if len(column) == 0:
                raise ValueError(f"empty column in {location}")
            elif column in self.column_names:
                column = self.column_names.index(column)
            else:
                if is_integer(column) and int(column) > 0 and int(column) <= self.n_columns:
                    column = int(column) - 1
                else:
                    raise ValueError(f"'{column}' in location {str(location)} does not correspond to a valid column")
        elif isinstance(column, int):
            if column < 1 or column > self.n_columns:
                raise ValueError(f"column {column} out of range for {str(location)}")
            column = column - 1
        else:
            raise ValueError(f"error parsing {str(location)}: must specify column as 1-indexed number or column name")

        result = (row,column)
        return result

    # add StockSolution or Solvent to the specified destinations
    # all other adding methods call this method
    # what: StockSolution or Solvent
    # dispense_map: dictionary from location tuples or strings to volumes in uL
    # examples:
    # {"D:10":1.0, (5,10):2.0, (5,11):3.0}
    def add_custom(self, what, dispense_map):
        # check invariants
        if what is None or not isinstance(what, (StockSolution,Solvent)):
            raise ValueError(f"expected a StockSolution or Solvent, but got a {str(type(what))} instead")
        if dispense_map is None:
            raise ValueError("must provide a dispense map")
        if not isinstance(dispense_map, dict):
            raise ValueError(f"expected a dict for the dispense_map, but got a {str(type(dispense_map))} instead")
        if len(dispense_map) == 0:
            raise ValueError("must dispense at least one thing")
        for k,v in dispense_map.items():
            if isinstance(k,tuple):
                if len(k) != 2:
                    raise ValueError(f"locations in dispense map must have two coordinates: *{k}* -> {v}")
                if not isinstance(k[0], (int,str)) or not isinstance(k[1], (int,str)):
                    raise ValueError(f"invalid location in dispense map: *{k}* -> {v}")
            elif isinstance(k,str):
                if k.count(":") != 1:
                    raise ValueError(f"locations should have one colon (:) to separate rows from columns: *{k}* -> {v}")
            else:
                raise ValueError(f"invalid location in dispense map: *{k}* -> {v}")

                if not isinstance(v,(int,float)) or v <= 0.0:
                    raise ValueError(f"invalid volume in dispense map {k} -> *{v}*")

        # convert dispense map locations to canonical locations
        canonical_dispense_map = {}
        for input_location,volume in dispense_map.items():
            if isinstance(input_location,str):
                fields = input_location.split(":")
                input_location = tuple(fields)
            canonical_location = self.get_canonical_form(input_location)
            #print(input_location, ":", canonical_location)
            if canonical_location in canonical_dispense_map:
                raise ValueError(f"cannot add twice to location {input_location}")
            canonical_dispense_map[canonical_location] = volume

        # record this addition so that we can print it out later
        self.instructions.append((what, canonical_dispense_map))

        # update the volumes
        for (row,column),volume in canonical_dispense_map.items():
            self.volumes[row,column] += volume
            if what not in self.volumes_used:
                self.volumes_used[what] = 0.0
        self.volumes_used[what] += volume * len(canonical_dispense_map)

        # warn if volume limits have been exceeded for the plate
        current_max_volume = np.max(self.volumes)
        if current_max_volume > self.max_volume_per_well:
            print(f"Warning: exceeded maximum well volume!  (Now {current_max_volume:.0f} uL, but limit is {self.max_volume_per_well:.0f} ul).")

        # for StockSolutions, keep track of how many micromoles have been added of the relevant reagent
        if isinstance(what, StockSolution):
            reagent = what.reagent
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

            # update the moles (in micromoles)
            for (row,column),volume in canonical_dispense_map.items():
                extra_moles = volume * what.concentration  # uL * mol / L = umol
                self.moles[reagent_index,row,column] += extra_moles

    # add StockSolution or Solvent to the specified rows
    # what: StockSolution or Solvent
    # how_much: volume in uL (same for every row)
    # rows: 1, "B", or [1, 2, "C"] (no duplicates allowed, 1-indexed)
    def add_to_rows(self, what, how_much, rows):
        if not isinstance(what, (StockSolution,Solvent)):
            raise ValueError(f"must add StockSolution or Solvent but got {str(type(what))} instead")
        if not isinstance(how_much, (float,int)) or how_much <= 0.0:
            raise ValueError(f"invalid amount of stuff {how_much}")
        if rows is None:
            raise ValueError("must specify a destination")

        # convert to int if necessary
        elif isinstance(rows, str):
            if rows in self.row_names:
                rows = self.row_names.index(rows) + 1
            elif not is_integer(rows):
                raise ValueError(f"invalid location: {rows}")
            rows = int(rows)

        # construct canonical location map
        dispense_map = {}
        if isinstance(rows, int):
            if rows < 1 or rows > self.n_rows:
                raise ValueError(f"row out of range: {rows}")
            for column in range(self.n_columns):
                location = (rows,column+1)
                dispense_map[location] = how_much
        elif isinstance(rows, list):
            rows2 = []
            for row in rows:
                if isinstance(row,str):
                    if row in self.row_names:
                        row = self.row_names.index(row) + 1
                    elif not is_integer(rows):
                        raise ValueError(f"invalid row: {rows}")
                    row = int(row)
                elif isinstance(row,int):
                    if row < 1 or row > self.n_rows:
                        raise ValueError(f"row out of range: {row}")
                else:
                    raise ValueError(f"invalid location: {row}")
                rows2.append(row)
            if len(rows) != len(set(rows2)):
                raise ValueError(f"check for duplicates in locations: {rows}")
            for column in range(self.n_columns):
                for row in rows2:
                    location = (row,column+1)
                    dispense_map[location] = how_much
        else:
            raise ValueError(f"unexpected input for destination: {rows}")
        self.add_custom(what, dispense_map)

    # add StockSolution or Solvent to the specified columns
    # what: StockSolution or Solvent
    # how_much: volume in uL (same for every column)
    # columns: 1, "B", or [1, 2, "C"] (no duplicates allowed, 1-indexed)
    # add StockSolution or Solvent to the specified columns
    def add_to_columns(self, what, how_much, columns):
        if not isinstance(what, (StockSolution,Solvent)):
            raise ValueError(f"must add StockSolution or Solvent but got {str(type(what))} instead")
        if not isinstance(how_much, (float,int)) or how_much <= 0.0:
            raise ValueError(f"invalid amount of stuff {how_much}")
        if columns is None:
            raise ValueError("must specify a destination")

        # convert to int if necessary
        elif isinstance(columns, str):
            if columns in self.column_names:
                columns = self.column_names.index(columns) + 1
            elif not is_integer(columns):
                raise ValueError(f"invalid location: {columns}")
            columns = int(columns)

        # construct canonical location map
        dispense_map = {}
        if isinstance(columns, int):
            if columns < 1 or columns > self.n_columns:
                raise ValueError(f"column out of range: {columns}")
            for row in range(self.n_rows):
                location = (row+1,columns)
                dispense_map[location] = how_much
        elif isinstance(columns, list):
            columns2 = []
            for column in columns:
                if isinstance(column,str):
                    if column in self.column_names:
                        column = self.column_names.index(column) + 1
                    elif not is_integer(columns):
                        raise ValueError(f"invalid column: {columns}")
                    column = int(column)
                elif isinstance(column,int):
                    if column < 1 or column > self.n_columns:
                        raise ValueError(f"column out of range: {column}")
                else:
                    raise ValueError(f"invalid location: {column}")
                columns2.append(column)
            if len(columns) != len(set(columns2)):
                raise ValueError(f"check for duplicates in locations: {columns}")
            for row in range(self.n_rows):
                for column in columns2:
                    location = (row+1,column)
                    dispense_map[location] = how_much
        else:
            raise ValueError(f"unexpected input for destination: {columns}")
        self.add_custom(what, dispense_map)

    # create an Excel spreadsheet summarizing this plate
    def to_excel(self, filename, colormap='plasma', do_not_overwrite=False):
        # delete file if it exists
        print(f"Writing plate to {filename}...", end='')
        if os.path.exists(filename):
            if do_not_overwrite:
                raise ValueError(f"Error: {filename} already exists.")
            else:
                os.remove(filename)

        # helper function
        # value: color based on this number
        # normalizer: mpl.colors.Normalize(vmin, vmax)
        def get_colors(value, normalizer):
            if np.isnan(value):
                return "#000000","#000000"
            rgba = cm(normalizer(value))
            r,g,b,a = rgba
            background_color = mpl.colors.to_hex(rgba)
            brightness = (.299 * r) + (.587 * g) + (.114 * b)
            if brightness < 0.5:
                font_color = "#FFFFFF"
            else:
                font_color = "#000000"
            #print(brightness,background_color,font_color)
            return background_color, font_color

        # create file
        workbook = xlsxwriter.Workbook(filename)
        cm = plt.get_cmap(colormap)

        # total volumes
        worksheet1 = workbook.add_worksheet(self.name)
        worksheet1.set_column(0,0,20)
        bold = workbook.add_format({'bold':True,'align':'right'})
        bold_highlight = workbook.add_format({'bold':True,'bg_color':'#FFFF00','align':'right'})
        worksheet1.write(0,0,"Volumes (uL)",bold_highlight)
        for i,column_name in enumerate(self.column_names):
            worksheet1.write_string(0,i+1,column_name,bold)
        for i,row_name in enumerate(self.row_names):
            worksheet1.write_string(i+1,0,row_name,bold)
        normalizer = mpl.colors.Normalize(vmin=0.0, vmax=self.max_volume_per_well)
        for row in range(self.n_rows):
            for column in range(self.n_columns):
                volume = self.volumes[row,column]
                bg_color, font_color = get_colors(volume, normalizer)
                cell_format = workbook.add_format()
                cell_format.set_bg_color(bg_color)
                cell_format.set_font_color(font_color)
                if volume > self.max_volume_per_well:
                    cell_format.set_border(5)
                    cell_format.set_border_color("#FF0000")
                worksheet1.write(row+1, column+1, volume, cell_format)

        # reagent concentrations in millimolar
        row_zero = self.n_rows + 2
        for reagent_index,reagent in enumerate(self.reagents):
            moles = self.moles[reagent_index]  # in micromoles
            volumes = self.volumes             # in microliters
            with np.errstate(divide='ignore', invalid='ignore'):
                concentrations = np.true_divide(moles, volumes)
                concentrations[~np.isfinite(concentrations)]=0
                concentrations = concentrations * 1000.0
            max_concentration = np.max(concentrations)
            normalizer = mpl.colors.Normalize(vmin=0.0, vmax=max_concentration)
            worksheet1.write_string(row_zero,0,f"{reagent.name} (mM)",bold_highlight)
            for i,column_name in enumerate(self.column_names):
                worksheet1.write_string(row_zero,i+1,column_name,bold)
            for i,row_name in enumerate(self.row_names):
                worksheet1.write_string(i+1+row_zero,0,row_name,bold)
            for row in range(self.n_rows):
                for column in range(self.n_columns):
                    concentration = concentrations[row,column]
                    if np.isnan(concentration):
                        continue
                    bg_color, font_color = get_colors(concentration, normalizer)
                    cell_format = workbook.add_format()
                    cell_format.set_bg_color(bg_color)
                    cell_format.set_font_color(font_color)
                    cell_format.set_num_format('0.0')
                    worksheet1.write_number(row+1+row_zero,column+1,concentration,cell_format)
            row_zero += self.n_rows + 2

        # instructions for how to prepare stocks
        worksheet2 = workbook.add_worksheet("stocks")
        worksheet2.set_column(0,0,30)
        worksheet2.set_column(1,1,10)
        worksheet2.set_column(2,2,10)
        worksheet2.set_column(3,3,50)
        worksheet2.write(1,0,"item",bold)
        worksheet2.write(0,1,"available",bold)
        worksheet2.write(1,1,"volume (uL)",bold)
        worksheet2.write(0,2,"volume",bold)
        worksheet2.write(1,2,"needed (uL)",bold)
        worksheet2.write(1,3,"instructions",bold)
        row_zero = 2
        for i,(item,required_volume) in enumerate(self.volumes_used.items()):
            worksheet2.write(row_zero+i,0,str(item))
            available_volume = item.volume * 1000.0
            worksheet2.write(row_zero+i,1,available_volume)
            if available_volume < required_volume:
                cell_format = workbook.add_format()
                cell_format.set_border(5)
                cell_format.set_border_color("FF0000")
                worksheet2.write(row_zero+i,2,required_volume,cell_format)
            else:
                worksheet2.write(row_zero+i,2,required_volume)
            if isinstance(item, Solvent):
                worksheet2.write(row_zero+i,3,"n/a")
            elif isinstance(item, StockSolution):
                worksheet2.write(row_zero+i,3,item.get_instructions_string())
            else:
                raise ValueError("unexpected item type")

	# instructions for how to dispense
        worksheet3 = workbook.add_worksheet("dispensing")
        worksheet3.set_column(0,0,10)
        row_zero = 0
        bold_highlight2 = workbook.add_format({'bold':True,'bg_color':'#FFFF00','align':'left'})
        n_steps = len(self.instructions)
        for step,(what,canonical_dispense_map) in enumerate(self.instructions):
            worksheet3.merge_range(row_zero,0,row_zero,1,f"Step {step+1} of {n_steps}",bold_highlight2)
            worksheet3.merge_range(row_zero,2,row_zero,5,f"Add {str(what)} to:",bold_highlight2)
            for i,column_name in enumerate(self.column_names):
                worksheet3.write_string(row_zero+1,i+1,column_name,bold)
            for i,row_name in enumerate(self.row_names):
                worksheet3.write_string(row_zero+2+i,0,row_name,bold)
            max_volume_added = 0.0
            for location,volume in canonical_dispense_map.items():
                if volume > max_volume_added:
                    max_volume_added = volume
            normalizer = mpl.colors.Normalize(vmin=0.0, vmax = max_volume_added)
            for row in range(self.n_rows):
                for column in range(self.n_columns):
                    location = (row,column)
                    volume = 0.0
                    if location in canonical_dispense_map:
                        volume = canonical_dispense_map[location]
                    bg_color, font_color = get_colors(volume, normalizer)
                    cell_format = workbook.add_format()
                    cell_format.set_bg_color(bg_color)
                    cell_format.set_font_color(font_color)
                    worksheet3.write(row_zero+2+row,1+column,volume,cell_format)

            row_zero += self.n_rows + 3

        # update status
        workbook.close()
        print("done.")

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

