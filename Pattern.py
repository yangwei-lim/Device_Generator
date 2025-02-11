import operator

def simple_1d_clustered_pattern(inst: list) -> list:
    """
    @brief: simple 1D clustered pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @return: pattern -> pattern list (e.g. [0, 1, 1, 2, 2, 2])
    """
    pattern = []

    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))

    # create the pattern
    for i in counts:
        for _ in range(counts[i]):
            pattern.append(i)
    
    return pattern


def simple_1d_interdigitated_pattern(inst: list) -> list:
    """
    @brief: simple 1D interdigitated pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @return: pattern -> pattern list (e.g. [0, 1, 2, 1, 2, 2])
    """
    pattern = []

    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))

    # find the maximum count
    max_count = max(inst)

    # create the interdigitated pattern
    # loop through the maximum count
    for _ in range(max_count):

         # loop through the instance
        for num in counts:

            # check the instance count
            if counts[num] > 0:
                pattern.append(num)
                counts[num] -= 1

    return pattern    


def sorted_1d_interdigitated_pattern(inst: list) -> list:
    """
    @brief: sorted 1D interdigitated pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @return: pattern -> pattern list (e.g. [2, 1, 0, 2, 1, 2])
    """
    pattern = []

    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))

    # sort the dictionary by the value
    counts = dict(sorted(counts.items(), key=operator.itemgetter(1), reverse=True))

    # find the maximum count
    max_count = max(inst)

    # create the interdigitated pattern
    # loop through the maximum count
    for _ in range(max_count):

         # loop through the instance
        for num in counts:

            # check the instance count
            if counts[num] > 0:
                pattern.append(num)
                counts[num] -= 1

    return pattern


def balanced_1d_interdigitated_pattern(inst: list) -> list:
    """
    @brief: balanced 1D interdigitated pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @return: pattern -> pattern list (e.g. [2, 2, 1, 1, 0, 2])
    """
    pattern = []

    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))

    # sort the dictionary by the value
    counts = dict(sorted(counts.items(), key=operator.itemgetter(1), reverse=True))

    # calculate the interdigitated occurrence = previous num / current num
    occur = []
    prev = 0
    for i, num in enumerate(counts):
        if i != 0:
            occur.append(round(prev / counts[num]))

        prev = counts[num]

    occur.append(1)

    # find the maximum count
    max_count = max(inst)

    # create the interdigitated pattern
    # loop through the maximum count
    for _ in range(max_count):

         # loop through the instance
        for i, num in enumerate(counts):

            # occurrence dependency
            for _ in range(occur[i]):

                # check the instance count
                if counts[num] > 0:
                    pattern.append(num)
                    counts[num] -= 1

    return pattern


def simple_1d_common_centroid_pattern(inst: list) -> list:
    """
    @brief: simple 1D common centroid pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @return: pattern -> pattern list (e.g. [1, 2, 0, 2, 2, 1])
    """
    pattern = []
    left_pattern = []
    right_pattern = []
    
    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))
    odd_counts = {}

    # get the odd number instance
    for i in counts:
        if counts[i] % 2 != 0:
            # Method 1:
            # odd_counts[i] = counts[i]   # get the odd instances from the counts
            # counts[i] = 0               # remove all the odd instances from the counts

            # Method 2:
            odd_counts[i] = 1           # get one count for the odd instances
            counts[i] -= 1              # minus one from the counts

    # create the left and right pattern based on the even instances
    post = "left"
    for i in counts:
        for _ in range(counts[i]):
            if post == "left":
                left_pattern.append(i)
                post = "right"
            else:
                right_pattern.append(i)
                post = "left"

    # add the odd instances to the left and right pattern
    post = "left"
    for i in odd_counts:
        for _ in range(odd_counts[i]):
            if post == "left":
                left_pattern.append(i)
                post = "right"
            else:
                right_pattern.append(i)
                post = "left"

    # create the pattern by combining the left and right (reversed) pattern
    pattern = left_pattern + right_pattern[::-1]

    return pattern


def simple_2d_clustered_pattern(inst: list, row: int) -> list:
    """
    @brief: simple 2D clustered pattern
    @param: inst -> instance list (e.g. [1, 2, 3]: one 0, two 1, three 2)
    @param: row -> row number
    @return: pattern -> pattern list (e.g. [0, 1, 1, 2, 2, 2])
    """
    pattern = []

    # convert the instances number to a dictionary
    counts = dict(enumerate(inst))

    # get dummy instance
    dummy = row - (sum(inst) % row) if sum(inst) % row != 0 else 0

    # insert the dummy instance
    counts["d"] = dummy

    # create 1d pattern from the instance
    pattern_1d = []
    for i in counts:
        for _ in range(counts[i]):
            pattern_1d.append(i)

    # get column number
    col = sum(inst) // row + 1 if dummy > 0 else sum(inst) // row

    # create 2d pattern from 1d pattern, row and column
    for _ in range(row):
        tmp = []
        for _ in range(col):
            tmp.append(pattern_1d.pop(0))
        pattern.append(tmp)
    
    return pattern


def custom_2d_pattern(inst: str) -> list:
    """
    @brief: custom pattern
    @param: inst -> string of instance list (e.g. "[01,10]")
    @return: pattern -> pattern list (e.g. [[0, 1], [1, 0]])
    """
    pattern = []
    row_inst = inst.strip("][").split(",")
    for i in row_inst:
        tmp = []
        for num in i:
            tmp.append(int(num)) if num != "d" else tmp.append('d')
        pattern.append(tmp)

    return pattern