# Failure of Converse Theorems of Gauss Sums Modulo ℓ

SageMath code accompanying the paper by James Evans, Xinning Ma, and Yanshun Zhang.

## Requirements

SageMath 10.5 (release date 2024-12-04). Tested on macOS.

## Running

    sage converse_theorem.sage

The program prompts for a prime ℓ and a prime power q, then prints:

- M (the number of θ-indices) and Q (the restriction modulus)
- a table of collision classes, with size, common residue mod Q,
  a verification that the residue is shared, and whether the class
  is a genuine counterexample
- for each genuine class, its decomposition into Frobenius pairs

## Output

The `output/` folder contains the raw console output for every (ℓ, q) pair
reported in the paper.

## Notes

ℓ must differ from the characteristic p of F_q; the program raises an error otherwise.
