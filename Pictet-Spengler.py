from PyPlate import Reagent, StockSolution, Generic96WellPlate

amino_acids = {'Gly': 1.008, 'Ala': 15.035, 'tLeu': 57.07, 'Chg': 83.086, 'Val': 43.055, 'CF3': 69.00, 'SerOMe': 46.053, 'Phg': 77.039}
catalysts = [None] * 8
catalyst_solns = [None] * 8

toluene = Reagent.create_liquid("toluene", 92.14, 0.867)

for index, aa in enumerate(amino_acids.keys()):
    mw = 474.44 + amino_acids[aa]
    catalysts[index] = Reagent.create_solid(f"Ph-{aa}-S-ArF", mw)

    #### make stock sol'n using 100 mg catalyst, 5 mL toluene
    mmol = 100 / mw
    molarity = mmol/5

    catalyst_solns[index] = StockSolution(catalysts[index], molarity, toluene, volume=5.0)

