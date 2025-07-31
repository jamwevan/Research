import csv
import os
from sympy import isprime, primerange

# Check whether n is a power of 2
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

# Check whether n is a prime power (n = p^k for some prime p and integer k ≥ 1)
def is_prime_power(n):
    if n < 2:
        return False
    for p in primerange(2, n + 1):
        k = 1
        while (power := p**k) <= n:
            if power == n:
                return True
            k += 1
    return False

# Check whether q matches the conjecture form: q = 1 + 2 * ℓ^j
def matches_conjecture_form(l, q):
    j = 1
    while True:
        candidate = 1 + 2 * (l ** j)
        if candidate == q:
            return True
        if candidate > q:
            return False
        j += 1

# Read existing (ℓ, q) pairs from CSV, ignoring any extra columns
def read_existing_pairs(file_path):
    existing = set()
    if os.path.exists(file_path):
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2:
                    try:
                        l, q = int(row[0]), int(row[1])
                        existing.add((l, q))
                    except ValueError:
                        continue
    return existing

# Append new pairs to CSV file
def append_pairs_to_file(file_path, pairs):
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for l, q in pairs:
            writer.writerow([l, q])

# Generate counterexample (ℓ, q) pairs meeting new logic
def generate_lq_counterexamples(count, existing_pairs):
    results = []
    l = 2
    while len(results) < count:
        if not isprime(l):
            l += 1
            continue

        for q in range(3, 100):  # ONLY consider q < 100
            if not is_prime_power(q):
                continue
            if is_power_of_two(q):
                continue
            if matches_conjecture_form(l, q):
                continue
            if (l, q) not in existing_pairs:
                results.append((l, q))
                existing_pairs.add((l, q))
                if len(results) >= count:
                    break

        l += 1  # move on to next ℓ no matter what, once q hits 3 digits
    return results

# Main program
if __name__ == "__main__":
    file_path = "anti_pairs.csv"
    x = int(input("How many (ℓ, q) counterexample pairs do you want? "))

    existing = read_existing_pairs(file_path)
    new_pairs = generate_lq_counterexamples(x, existing)
    append_pairs_to_file(file_path, new_pairs)

    print(f"\nWrote {len(new_pairs)} counterexample (ℓ, q) pairs to {file_path}.")
