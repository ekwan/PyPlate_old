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
    catalyst_solns[index] = StockSolution(catalysts[index], 0.01, toluene, volume=5.0)
    print(catalyst_solns[index])

bzoh = Reagent.create_solid("PhCO2H", 122.12)
bzoh_soln = StockSolution(bzoh, 0.01, toluene, volume=5.0)

imine1 = Reagent.create_solid("tryptamine-benzaldehyde", 248.33)
imine2 = Reagent.create_solid("tryptamine-4Fbenzaldehyde", 266.32)
imine1_soln = StockSolution(imine1, 0.1, toluene, volume=10.0)
imine2_soln = StockSolution(imine2, 0.1, toluene, volume=10.0)

plate = Generic96WellPlate("test plate", 500.0)

plate.add_to_block(what=imine1_soln, how_much=50, upper_left='A:1', bottom_right='D:12')
plate.add_to_block(what=imine2_soln, how_much=50, upper_left='E:1', bottom_right='H:12')

plate.add_to_block(what=bzoh_soln, how_much=10, upper_left='A:1', bottom_right='H:12')

for index, catalyst_soln in enumerate(catalyst_solns):
    plate.add_to_columns(what=catalyst_soln, how_much=10, columns=[index+1])

plate.fill_block_up_to_volume(what=toluene, target_volume=100.0, upper_left="A:1", bottom_right="H:12")

filename = "ps_plate.xlsx"
plate.to_excel(filename)
