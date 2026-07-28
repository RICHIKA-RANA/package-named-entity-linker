def get_distance(seq1, seq2, seqType='w'):
    if (seqType == 's'):
        seq1 = seq1.split(' ')
        seq2 = seq2.split(' ')
    return damerau_levenshtein(seq1, seq2)

def damerau_levenshtein(seq1, seq2):
    """
    Compute the Damerau-Levenshtein distance.

    Supports insertions, deletions, substitutions and adjacent
    transpositions.

    Time Complexity:
        O(len(seq1) * len(seq2))

    Space Complexity:
        O(len(seq2))
    """

    if seq1 == seq2:
        return 0

    if not seq1:
        return len(seq2)

    if not seq2:
        return len(seq1)

    previous_previous = None
    previous = list(range(len(seq2) + 1))

    for i, c1 in enumerate(seq1):
        current = [i + 1]

        for j, c2 in enumerate(seq2):
            insert_cost = current[j] + 1
            delete_cost = previous[j + 1] + 1
            replace_cost = previous[j] + (c1 != c2)

            value = min(insert_cost, delete_cost, replace_cost)

            if (
                i > 0
                and j > 0
                and c1 == seq2[j - 1]
                and seq1[i - 1] == c2
            ):
                value = min(value, previous_previous[j - 1] + 1)

            current.append(value)

        previous_previous = previous
        previous = current

    return previous[-1]
