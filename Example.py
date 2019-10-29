from PyPlate import Reagent, StockSolution, Generic96WellPlate

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
plate.add_stock_to_wells(volume=10.0, stock_solution=triethylamine_10mM, destinations=["A:1","B:2"])

for i,column in enumerate(plate.column_names):
    plate.add_stock_to_wells(volume=50.0*(i+1), stock_solution=triethylamine_10mM, destinations=f"1:{i+1}")
plate.add_stock_to_row(volume=15.0, stock_solution=sodium_sulfate_halfM, row=2)
print("micromoles")
print(plate.moles[0])

#plate.add_stock_to_column(volume=15.0, stock_solution=triethylamine_10mM, column="2")
#print(plate.moles[0])
#plate.add_stock_to_row(volume=25.0, stock_solution=sodium_sulfate_halfM, row="A")
#print(plate.moles[0])
#print(plate.moles[1])
#plate.add_stock_to_row(volume=25.0, stock_solution=sodium_sulfate_halfM, row=1)
#print(plate.moles[0])
#print(plate.moles[1])
#print()


print("volumes")
print(plate.volumes)

plate.to_excel("plate.xlsx")
