from enum import Enum

class ReagentType(Enum):
    SOLID = 1
    LIQUID = 2

class Reagent(object):
    # MW in g/mol, density in g/mL
    def __init__(self, name, molecular_weight, reagent_type, density):
        self.name = name
        self.molecular_weight = molecular_weight
        self.reagent_type = reagent_type
        self.density = density

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
        self.reagent = reagent
        self.concentration = concentration
        self.solvent = solvent
        self.volume = volume

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


