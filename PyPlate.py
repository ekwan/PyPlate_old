from enum import Enum
import numpy as np

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
            self.rows = rows
            self.row_names = [ f"{i+1}" for i in range(rows) ]
        elif isinstance(rows, list):
            if len(rows) == 0:
                raise ValueError("must have at least one row")
            for row in rows:
                if not isinstance(row, str):
                    raise ValueError("row names must be strings")
            self.rows = len(rows)
            self.row_names = rows
        else:
            raise ValueError("rows must be int or list")

        self.max_volume_per_well = max_volume_per_well

        if isinstance(columns, int):
            if columns < 1:
                raise ValueError("illegal number of columns")
            self.columns = columns
            self.column_names = [ f"{i+1}" for i in range(columns) ]
        elif isinstance(columns, list):
            if len(columns) == 0:
                raise ValueError("must have at least one row")
            for column in columns:
                if not isinstance(column, str):
                    raise ValueError("row names must be strings")
            self.columns = len(columns)
            self.column_names = columns
        else:
            raise ValueError("columns must be int or list")

        self.reagents = []                                   # labels the reagents in self.moles
        self.volumes = np.zeros((self.rows,self.columns))    # in uL
        self.moles = None                                    # in moles, shape:(reagent, rows, columns)
        self.instructions = []                               # list of instructions for making this plate

    def __str__(self):
        return f"{self.name} ({self.make}, {self.rows}x{self.columns}, max {self.max_volume_per_well:.0f} uL/well)"

# represents a 96 well plate
class Generic96WellPlate(Plate):
    def __init__(self, name, max_volume_per_well):
        make = "generic 96 well plate"
        rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
        columns = 12
        super().__init__(name, make, rows, columns, max_volume_per_well)

# represents an addition of a StockSolution to a Plate
class Instruction(object):
    def __init__(self):
        pass

    def __str__(self):
        pass

### testing ###

sodium_sulfate = Reagent.create_solid("sodium sulfate", 142.04)
triethylamine = Reagent.create_liquid("triethylamine", 101.19, 0.726)
water = Reagent.create_liquid("water", 18.01528, 0.997)
DMSO = Reagent.create_liquid("DMSO", 78.13, 1.1)

sodium_sulfate_halfM = StockSolution(sodium_sulfate, 0.5, water, volume=10.0)
triethylamine_10mM = StockSolution(triethylamine, 0.01, DMSO, volume=10.0)

print(sodium_sulfate)
print(sodium_sulfate_halfM)
print(sodium_sulfate_halfM.get_instructions_string())

print()

print(triethylamine)
print(triethylamine_10mM)
print(triethylamine_10mM.get_instructions_string())

print()

plate = Generic96WellPlate("test plate", 500.0)
print(plate)
