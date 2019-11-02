from PyPlate import Reagent, Solvent, StockSolution, Plate, Generic96WellPlate

r1 = Reagent.create_liquid("toluene", 92.14, 0.867)
#r2 = Reagent.create_liquid(123, 92.14, 0.867)
r3 = Reagent.create_liquid("123", 92, 867)
#r4 = Reagent.create_liquid(['a'], 92, 867)

s1 = Solvent(volume=15.0, name="toluene")
s2 = Solvent(volume=15, name="toluene")
s3 = Solvent(volume=0.00000000000000000000000000001, name="toluene")

ss1 = StockSolution(r3, 100, s3, volume=1)

p1 = Generic96WellPlate("test plate", 500.0)
p2 = Plate("p2", "test plate", ['A', 'aa', 'a'], ['1.5', '1.7', '1.70'], 10)
p3 = Plate("p2", "test plate", ['A', 'aa', '1.5'], ['1.5', 'A', '1.70'], 1000)
p4 = Plate("p2", "test plate", ['A', 'a', 'a '], ['1.700', 'A', '1.70'], 10)

for p in [p4]:
    p.add_custom(what=ss1, dispense_map={("a",1.7):1.0})
#    plate.add_custom(what=sodium_sulfate_halfM, dispense_map={(1,1):1.0, ("A",2):2.0, (1,3):3.0})
