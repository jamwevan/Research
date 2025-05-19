import csv
import os
from sympy import isprime, primerange

# Check whether n is a prime power (n = p^k for some prime p and integer k >= 1)
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

# Read existing (ℓ, q) pairs from a CSV file into a set
# Now supports files with more than 2 columns by only reading the first two
def read_existing_pairs(file_path):
    existing = set()
    if os.path.exists(file_path):
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2:  # Accept rows with 2+ columns
                    try:
                        l, q = int(row[0]), int(row[1])
                        existing.add((l, q))
                    except ValueError:
                        continue
    return existing

# Write new (ℓ, q) pairs to the CSV file (still writes only 2 columns)
def append_pairs_to_file(file_path, pairs):
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for l, q in pairs:
            writer.writerow([l, q])

# Generate the first `count` many (ℓ, q) pairs satisfying the given condition
def generate_lq_pairs(count, existing_pairs):
    results = []
    l = 2
    while len(results) < count:
        if not isprime(l):
            l += 1
            continue
        j = 1
        while True:
            q = 1 + 2 * (l**j)
            if is_prime_power(q):
                if (l, q) not in existing_pairs:
                    results.append((l, q))
                    existing_pairs.add((l, q))
                    if len(results) >= count:
                        break
            elif q > 5000:
                break
            j += 1
        l += 1
    return results

# Main program
if __name__ == "__main__":
    file_path = "pairs.csv"
    x = int(input("How many (ℓ, q) pairs do you want? "))

    existing = read_existing_pairs(file_path)
    new_pairs = generate_lq_pairs(x, existing)
    append_pairs_to_file(file_path, new_pairs)

    print(f"\nWrote {len(new_pairs)} new (ℓ, q) pairs to {file_path}.")
