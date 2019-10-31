from PyPlate import Reagent, StockSolution, Solvent, Generic96WellPlate

### testing ###

# define reagents
print("reagents:")
sodium_sulfate = Reagent.create_solid("sodium sulfate", molecular_weight=142.04)
triethylamine = Reagent.create_liquid("triethylamine", molecular_weight=101.19, density=0.726)
print(sodium_sulfate)
print(triethylamine)
print()

# create solvents
print("solvents:")
water_DI = Solvent(volume=10.0, name="DI water")       # volume in mL
water_tap = Solvent(volume=20.0, name="tap water")
DMSO = Solvent(volume=15.0, name="DMSO")
print(water_DI)
print(water_tap)
print(DMSO)
print()

# create stocks
# concentrations in M
# volumes in M
print("stock solutions:")
sodium_sulfate_halfM = StockSolution(what=sodium_sulfate, concentration=0.5, solvent=water_DI, volume=10.0)
triethylamine_10mM = StockSolution(triethylamine, 0.01, DMSO, volume=10.0)
triethylamine_50mM = StockSolution(triethylamine, 0.05, DMSO, volume=10.0)
print(sodium_sulfate_halfM)
print(triethylamine_10mM)
print(triethylamine_50mM)
print()

# create plate
print("plate:")
plate = Generic96WellPlate("test plate", 500.0)
print(plate)

# add stuff to the plate
# volume in uL
plate.add_custom(what=sodium_sulfate_halfM, dispense_map={(1,1):1.0, ("A",2):2.0, (1,3):3.0})
plate.add_custom(what=sodium_sulfate_halfM, dispense_map={(3,3):7.0, ("D",3):10.0, (5,"3"):9.0})
plate.add_custom(what=triethylamine_10mM, dispense_map={"D:10":1.0, (5,10):2.0, (5,"11"):3.0})
plate.add_custom(what=triethylamine_10mM, dispense_map={"D:10":20000.0})

dispense_map = {}
for i,column in enumerate(plate.column_names):
    where=f"1:{i+1}"
    volume=42.0*(i+1)
    dispense_map[where]=volume
plate.add_custom(what=triethylamine_10mM, dispense_map=dispense_map)

plate.add_to_rows(what=triethylamine_10mM, how_much=2.0, rows=6)
plate.add_to_rows(what=triethylamine_10mM, how_much=7.0, rows=[7,"H"])
plate.add_to_columns(what=triethylamine_10mM, how_much=8.0, columns="10")
plate.add_to_columns(what=triethylamine_10mM, how_much=9.0, columns=[11,12])

plate.add_to_rows(what=water_DI, how_much=20.0, rows=[i+1 for i in range(8)])
plate.add_to_columns(what=DMSO, how_much=1.0, columns=[i+1 for i in range(12)])

print()

# print total volumes
print("volumes:")
print(plate.volumes)
print()

# print how much of each stock solution or solvent we used:
print("used volumes:")
for item,volume in plate.volumes_used.items():
    print(f"{item} : {volume:.1f} uL")
print()

# print moles
print("micromoles:\n")
for i in range(len(plate.moles)):
    print(plate.reagents[i])
    print(plate.moles[i,:,:])
    print()
print()

# dump plate to excel
filename = "plate.xlsx"
plate.to_excel(filename)
