# PyPlate

*a Python tool for designing chemistry experiments in plate format*

## Introduction

*PyPlate* is an open-source Python program for designing chemistry experiments to be run in plate format.  These experiments could be chemical reactions, calibrations for quantitation, assays, etc.  *PyPlate* provides a simple API for adding reagents to the plate.  After being given these user-provided instructions for creating the plate, *PyPlate* generates a color-coded *Excel* spreadsheet containing the resulting concentrations, volumes, and dispensing instructions.

## Contents
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [How to Use](#instructions)
  	- [Imports](#imports)
  	- [Reagents](#reagents)
  	- [Solvents](#solvents)
  	- [Stock Solutions](#stock-solutions)
  	- [Locations on a Plate](#locations-on-a-plate)
  	- [Simple Dispensing](#simple-dispensing)
  	- [Advanced Dispensing](#advanced-dispensing)
  	- [Creating Excel Output](#creating-excel-output)
  	- [Defining Custom Plates](#defining-custom-plates)
  	- [Example Code](#example-code)
  - [Authors](#authors)
  - [How To Cite](#how-to-cite)
  - [License](#license)


## Installation

*PyPlate* requires Python 3.7 or later, `numpy`, `matplotlib`, and `xlsxwriter` (use of a package manager like `conda` is recommended).  All requirements can be installed by typing:

`pip install -r requirements.txt`

All the *PyPlate* code is stored in `PyPlate.py`.  Simply copy this file to a directory of your choice or work directly in the project directory.

To view the spreadsheet output, you will need *Microsoft Excel*.

## How to Use

The philosophy behind *PyPlate* is to mimic the physical process of dispensing liquids into plates as closely as possible.  *PyPlate* assumes that only stock solutions or solvents will be added to plates (and not solids or neat liquids).

### Imports

For a typical design, we will need:

`from PyPlate import Reagent, StockSolution, Solvent, Generic96WellPlate`

### Reagents

A `Reagent` is a solid or liquid that will become the solute in a stock solution.  For example:

```
sodium_sulfate = Reagent.create_solid("sodium sulfate", molecular_weight=142.04)
triethylamine = Reagent.create_liquid("triethylamine", molecular_weight=101.19, density=0.726)
```

### Solvents

A `Solvent` will be the solvent in a stock solution.  For example:

```
water_DI = Solvent(volume=10.0, name="DI water")       # volume in mL
water_tap = Solvent(volume=20.0, name="tap water")
DMSO = Solvent(volume=15.0, name="DMSO")
```

### Stock Solutions

A `StockSolution` is a mixture of a reagent (solute) and solvent.  For example:

```
sodium_sulfate_halfM = StockSolution(what=sodium_sulfate, concentration=0.5, solvent=water_DI, volume=10.0)
triethylamine_10mM = StockSolution(triethylamine, 0.01, DMSO, volume=10.0)
triethylamine_50mM = StockSolution(triethylamine, 0.05, DMSO, volume=10.0)
```

Note that we can also create StockSolutions by diluting others:

```
triethylamine_10mM = StockSolution(triethylamine_50mM, 0.01, DMSO, volume=10.0)
```

(Trying to create a more concentrated stock from a less concentrated stock will result in an error.)  This process can be helpful for improving accuracy.

### Creating a Plate

To define a plate, you must use an existing plate template:

```
plate = Generic96WellPlate("test plate", max_volume_per_well=500.0)
```

(See below for instructions on how to define custom plate templates.)  The maximum volume is given in uL.

### Locations on a Plate

You can refer to rows/columns on plates either by number or label.  The origin of the plate is assumed to be the upper left and is given the coordinate "1:1".  In the provided plate implementations (e.g. `Generic96WellPlate`), rows are also labeled A, B, C, etc., while columns are labeled numerically.  Thus, examples of valid locations are:

- "1:1"
- "A:1"
- "5:1"
- "E:1"

If you make your own plate definitions, you can provide custom labels for the rows or columns.

### Simple Dispensing

The easiest thing to do is to add the same amount of liquid to a row or column:

```
plate.add_to_rows(what=triethylamine_10mM, how_much=2.0, rows=6)
plate.add_to_rows(what=triethylamine_10mM, how_much=7.0, rows=[7,"H"])
plate.add_to_columns(what=triethylamine_10mM, how_much=8.0, columns="10")
plate.add_to_columns(what=triethylamine_10mM, how_much=9.0, columns=[11,12])
```

Notice that the location can be a single row/column or a list of rows/columns.  A flexible input format is allowed: numbers are assumed to be row/column numbers (1-indexed), while strings are assumed to represent row/column labels.  All volumes are in uL (for all of these dispense functions).

The liquid can also be a solvent:

```
plate.add_to_rows(what=water_DI, how_much=20.0, rows=[i+1 for i in range(8)])
plate.add_to_columns(what=DMSO, how_much=1.0, columns=[i+1 for i in range(12)])
```

(However, you cannot add a solid or neat liquid.)

### Advanced Dispensing

You have a few options for fancier dispensing patterns:

- `add_gradient_to_column(what, top_position, bottom_position, lo_volume, hi_volume, order=`forwards`)`
	This lets you add a linearly increasing (`order='forwards'`) or decreasing (`order='backwards'`) amount of stock solution or solvent to a column.  `top_position` and `bottom_position` must be locations in the same column, with `top_position` being above `bottom_position`.
	
- `add_gradient_to_row(what, left_position, right_position, lo_volume, hi_volume, order=`forwards`)`
   This is the same but adds to rows.  Analogous requirements apply.

- `add_to_block(what, how_much, upper_left, bottom_right)`
   Adds the same amount of stuff to a rectangular region.

- `fill_block_up_to_volume(what, target_volume, upper_left, bottom_right)`
   Tops up the specified rectangular region so that `target_volume` is reached.  An error will be thrown if a negative volume is required.

### Creating Excel Output

When you have finished creating your plate, you can create an *Excel* spreadsheet:

```
filename = "test.xlsx"
plate.to_excel(filename)
```

The first tab will contain the total volume and individual reagent concentrations in each well.  The second tab will contain a set of instructions for how to prepare each stock solution, as well as a summary of how much of each stock will be used.  The third tab contains color-coded instructions on how to dispense the liquids to the plate.  The order here is precisely the order that was used to construct the plate object.  Thus, you can be creative here to create dispensing orders that are particularly convenient.

Every tab uses a perceptually-uniform colormap (`plasma`).  You can choose other `matplotlib` colormaps by changing the default keyword argument `colormap='plasma'` in your call to `to_excel`.

Occasionally, you may get a bold red box.  This can occur if you exceed the maximum allowed volume for a well or use more stock than is predicted to be available.

*Note:* The second tab ("stocks") information about how much of each stock solution is required.  The amount in column C includes the amount needed to dispense as well any amount needed to create other stock solutions.  Solvents are also listed in this tab.  However, the volumes listed are the volumes needed for dispensing only.  The volumes do not include any amounts that are required to create stock solutions.

### Defining Custom Plates

By default both 96- and 384-well plates are defined.  If you want to define some other plates, you can do so in `PyPlate.py`.  For example, here is the definition for a 96-well plate:

```
class Generic96WellPlate(Plate):
    def __init__(self, name, max_volume_per_well):
        make = "generic 96 well plate"
        rows = UPPERCASE_LETTERS[:8]
        columns = 12
        super().__init__(name, make, rows, columns, max_volume_per_well)
```

### Example Code

The code for the above examples can be found in `examples/Example.py`.  Please see `examples/Example2.py` for a more sophisticated example.

## Authors

*PyPlate* was written by Eugene Kwan and Corin Wagen.  Please email `ekwan16@gmail.com` with any questions.  We hope this program will facilitate high-throughput experimentation and analysis.

## How to Cite

Kwan, E.E.; Wagen, C.  *PyPlate*  **2019**, www.github.com/ekwan/PyPlate.

## License
   
This project is licensed under the Apache License, Version 2.0. See `LICENSE.txt` for full terms and conditions.
   
*Copyright 2019 by Eugene E. Kwan and Corin Wagen*
