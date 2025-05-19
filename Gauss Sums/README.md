# Modular Gauss Sum Analysis Tools

This repository contains programs developed to investigate a conjecture about modular counter examples to the classical converse theorem of Gauss sums. While the classical theorem (over ℂ) uniquely determines multiplicative characters without counter examples, our work focuses on the modular setting (over the algebraic closure of Fℓ, Fℓ̄) where counter examples do occur. According to the conjecture by Bakeberg, Gerbelli-Gauthier, Goodson, Iyengar, Moss, and Zhang, such counter examples occur precisely when:

q = 2ℓ^i + 1 (for some integer i > 0)

## Tools

- **pair_generator.py**  
When the script is executed, it first prompts the user to specify how many new \((\ell, q)\) pairs to generate. It then reads in any previously recorded pairs from the file \texttt{pairs.csv} to ensure no duplicates are produced. Using this existing data, the script generates the requested number of new pairs of the form \(q = 1 + 2\ell^j\), where \(\ell\) is a prime and \(q\) is a prime power. Once generated, the new pairs are appended to the CSV file. Finally, the script prints a message indicating how many new \((\ell, q)\) pairs were successfully added to the file.

- **anti_pair_generator.py** 
This script generates \((\ell, q)\) pairs that intentionally fall \textit{outside} the form \(q = 1 + 2\ell^j\), with the goal of identifying structured counterexamples to the conjecture. After prompting the user for the number of pairs to generate, it reads in any existing data from \texttt{anti\_pairs.csv} to avoid duplication. It then loops over prime values of \(\ell\) and checks integers \(q < 100\), filtering for those that are prime powers, not powers of 2, and do not satisfy the conjectural form. Any such \((\ell, q)\) pair not already in the file is added to the output list. Once the desired number of new pairs is found, the script appends them to the CSV file and prints a message indicating how many were added.

- **converse_theorem_info.sage**  
  Investigates specific (ℓ, q) pairs by computing Gauss sums modulo ℓ to verify whether they serve as counter examples, regardless of their form.

## Getting Started

### Prerequisites

- **SageMath**: Required for running the `.sage` scripts.
- **Python 3**: Required for running `pair_generator.py`.
- Additional dependencies as needed.

### Installation

1. **Clone the repository**:
`git clone https://github.com/jamwevan/Gauss-Sums-Research.git`  
`cd Gauss-Sums-Research/Code`

## Usage

1. **Run the Pair Generator**:  
`python pair_generator.py`  

2. **Run the Anti-Pair Generator**:  
`python anti_pair_generator.py`

3. **Test Specific (ℓ, q) Pairs with converse_theorem.sage**:  
`sage converse_theorem_info.sage`  
Follow the prompts to enter any (ℓ, q) pair. This script computes Gauss sums modulo ℓ and verifies if the pair is a counter example.

## Contributors

James Evans, Xinning Ma, & Yanshun Zhang

## Contact

**James Evans**  
Email: [jamwevan@umich.edu](mailto:jamwevan@umich.edu)
