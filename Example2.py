from PyPlate import Reagent, StockSolution, Solvent, Generic96WellPlate

### testing ###

# define reagents
cyclosporin = Reagent.create_solid("cyclosporin", molecular_weight=1202.61)
enk = Reagent.create_solid("Met-enkephalin", molecular_weight=573.67)
nitrile = Reagent.create_liquid("benzonitrile", molecular_weight=117.15, density = 1.015)

# create solvent
MeCN = Solvent(volume=20.0, name="acetonitrile")
water = Solvent(volume=5.0, name="water")

# create stocks
# concentration in M and volume in mL
nitrile_100mM = StockSolution(what=nitrile, concentration=0.1, solvent=MeCN, volume=1.0)
nitrile_10mM = StockSolution(what=nitrile_100mM, concentration=0.01, solvent=MeCN, volume=1.0) # conc. in M and volume in mL
nitrile_1mM = StockSolution(what=nitrile_10mM, concentration=0.001, solvent=MeCN, volume=1.0) # conc. in M and volume in mL
nitrile_0_1mM = StockSolution(what=nitrile_1mM, concentration=0.0001, solvent=MeCN, volume=1.0) # conc. in M and volume in mL
cyclosporin_5mM = StockSolution(what=cyclosporin, concentration=0.005, solvent = MeCN, volume=2.0)
cyclosporin_0_5mM = StockSolution(what=cyclosporin_5mM, concentration=0.0005, solvent = MeCN, volume=1.0)
cyclosporin_0_05mM = StockSolution(what=cyclosporin_0_5mM, concentration=0.00005, solvent = MeCN, volume=1.0)
enk_5mM = StockSolution(what=enk, concentration=0.005, solvent = water, volume=2.0)
enk_0_5mM = StockSolution(what=enk_5mM, concentration=0.0005, solvent = water, volume=1.0)
enk_0_05mM = StockSolution(what=enk_0_5mM, concentration=0.00005, solvent = water, volume=1.0)

# create plate
plate = Generic96WellPlate("test plate", max_volume_per_well=100.0)

# dispense internal standard
# add_to_gradient: add a series of linearly increasing volumes to a row or column
# add_to_block: add stuff to a rectangle of wells on the plate
plate.add_gradient_to_column(what=nitrile_100mM, top_position="A:11", bottom_position="D:11", lo_volume=10.0, hi_volume=40.0, order='backwards')
plate.add_gradient_to_column(what=nitrile_10mM, top_position="E:11", bottom_position="H:11", lo_volume=10.0, hi_volume=40.0, order='backwards')
plate.add_gradient_to_column(what=nitrile_1mM, top_position="A:12", bottom_position="D:12", lo_volume=10.0, hi_volume=40.0, order='backwards')
plate.add_gradient_to_column(what=nitrile_0_1mM, top_position="E:12", bottom_position="G:12", lo_volume=10.0, hi_volume=30.0, order='backwards')
plate.add_to_block(what=nitrile_10mM, how_much=5.0, upper_left="A:1", bottom_right="A:10")
plate.add_to_block(what=nitrile_10mM, how_much=5.0, upper_left="E:1", bottom_right="E:10")
plate.add_to_block(what=nitrile_1mM, how_much=5.0, upper_left="B:1", bottom_right="B:10")
plate.add_to_block(what=nitrile_1mM, how_much=5.0, upper_left="F:1", bottom_right="F:10")
plate.add_to_block(what=nitrile_0_1mM, how_much=5.0, upper_left="C:1", bottom_right="C:10")
plate.add_to_block(what=nitrile_0_1mM, how_much=5.0, upper_left="G:1", bottom_right="G:10")
plate.add_to_block(what=nitrile_0_1mM, how_much=5.0, upper_left="D:1", bottom_right="D:10")
plate.add_to_block(what=nitrile_0_1mM, how_much=5.0, upper_left="H:1", bottom_right="H:10")

# dispense peptides
plate.add_gradient_to_row(what=cyclosporin_5mM, lo_volume=50, hi_volume=95.0, left_position="A:1", right_position="A:10", order='backwards')
plate.add_gradient_to_row(what=cyclosporin_5mM, lo_volume=5.0, hi_volume=50.0, left_position="B:1", right_position="B:10")
plate.add_gradient_to_row(what=cyclosporin_0_5mM, lo_volume=5.0, hi_volume=50.0, left_position="C:1", right_position="C:10", order='backwards')
plate.add_gradient_to_row(what=cyclosporin_0_05mM, lo_volume=5.0, hi_volume=50.0, left_position="D:1", right_position="D:10")
plate.add_gradient_to_row(what=enk_5mM, lo_volume=50.0, hi_volume=95.0, left_position="E:1", right_position="E:10", order='backwards')
plate.add_gradient_to_row(what=enk_5mM, lo_volume=5.0, hi_volume=50.0, left_position="F:1", right_position="F:10")
plate.add_gradient_to_row(what=enk_0_5mM, lo_volume=5.0, hi_volume=50.0, left_position="G:1", right_position="G:10", order='backwards')
plate.add_gradient_to_row(what=enk_0_05mM, lo_volume=5.0, hi_volume=50.0, left_position="H:1", right_position="H:10")

# dispense solvent
# make up the volume in all wells to 100 uL
plate.fill_block_up_to_volume(what=MeCN, target_volume=100.0, upper_left="A:1", bottom_right="H:12")

# dump plate to excel
filename = "test.xlsx"
plate.to_excel(filename)
