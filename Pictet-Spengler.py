from PyPlate import Reagent, Solvent, StockSolution, Generic96WellPlate

amino_acids = {'Gly': 1.008, 'Ala': 15.035, 'tLeu': 57.07, 'Chg': 83.086, 'Val': 43.055, 'CF3': 69.00, 'SerOMe': 46.053, 'Phg': 77.039}
catalysts = [None] * 8
catalyst_solns = [None] * 8

#toluene = Reagent.create_liquid("toluene", 92.14, 0.867)
toluene = Solvent(volume=15.0, name="toluene")

for index, aa in enumerate(amino_acids.keys()):
    mw = 474.44 + amino_acids[aa]
    catalysts[index] = Reagent.create_solid(f"Ph-{aa}-S-ArF", mw)

    #### make stock sol'n using 100 mg catalyst, 5 mL toluene
    mmol = 100 / mw
    molarity = mmol/5

    catalyst_solns[index] = StockSolution(catalysts[index], molarity, toluene, volume=5.0)
    print(catalyst_solns[index])

imine1 = Reagent.create_solid("tryptamine-benzaldehyde", 248.33)
imine2 = Reagent.create_solid("tryptamine-4Fbenzaldehyde", 266.32)
imine1_soln = StockSolution(imine1, 0.1, toluene, volume=10.0)
imine2_soln = StockSolution(imine2, 0.1, toluene, volume=10.0)

plate = Generic96WellPlate("test plate", 500.0)

plate.add_to_rows(what=imine1_soln, how_much=100, rows=[1, 2])
plate.add_to_rows(what=imine2_soln, how_much=100, rows=[3, 4])

for index, catalyst_soln in enumerate(catalyst_solns):
    plate.add_to_columns(what=catalyst_soln, how_much=50, columns=[index+1])


filename = "plate.xlsx"
plate.to_excel(filename)
