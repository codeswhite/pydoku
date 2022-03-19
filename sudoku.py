#!/bin/env python3

from pathlib import Path
from time import sleep
from sys import argv
import functools

USER_WAIT = False

SUDOKU_STRENGTH = 3
POWER = SUDOKU_STRENGTH * SUDOKU_STRENGTH  # 9


def print_tensor(tensor):
    print("+------- matrix --------+")
    for y in range(POWER):
        if y and y % SUDOKU_STRENGTH == 0:
            print('|-------+-------+-------|')
        for x in range(POWER):
            if x % SUDOKU_STRENGTH == 0:
                print('| ', end='')
            val = tensor[y][x][0]
            print(val if val else '_', end='')
            print(' ', end='')
        print('|')
    print('+-----------------------+')


def load_from_file(filename: str):
    """
    Load 2 dimentional matrix from file,
    And convert 2d matrix to 3d tensor.
        The 3rd dimensions going as and array where
        the 2nd dimention value placed in the first index of the array.
    """

    # Create matrix and line arrays
    matrix = []
    for line in Path(filename).read_text().splitlines():
        matrix.append([[int(char), []] for char in line if char.isnumeric()])
    return matrix


def get_container_cells_array(pos_y: int, pos_x: int):
    arr = []
    cy_base = int(pos_y/SUDOKU_STRENGTH) * SUDOKU_STRENGTH
    cx_base = int(pos_x/SUDOKU_STRENGTH) * SUDOKU_STRENGTH
    for cy_id in range(cy_base, cy_base + SUDOKU_STRENGTH):
        for cx_id in range(cx_base, cx_base + SUDOKU_STRENGTH):
            arr.append((cy_id, cx_id))
    return arr


def get_neighbor_arrays(pos_y: int, pos_x: int):
    """Generate 3 arrays of cells: X lane, Y lane and container"""
    # X lane
    arr = []
    for x_lane in range(POWER):
        if x_lane != pos_x:
            arr.append((pos_y, x_lane))
    yield arr

    # Y lane
    arr = []
    for y_lane in range(POWER):
        if y_lane != pos_y:
            arr.append((y_lane, pos_x))
    yield arr

    # Container
    yield [pos
           for pos in get_container_cells_array(pos_y, pos_x)
           if pos != (pos_y, pos_x)]


def get_all_neighbors(pos_y: int, pos_x: int):
    all_neighbors = []
    for arr in get_neighbor_arrays(pos_y, pos_x):
        all_neighbors += arr
    return all_neighbors


def find_errors(tensor):
    # x lanes
    for y in range(POWER):
        acc = []
        for x in range(POWER):
            val = tensor[y][x][0]
            if val:
                if val in acc:
                    return y, x
                acc.append(val)
    # y lanes
    for x in range(POWER):
        acc = []
        for y in range(POWER):
            val = tensor[y][x][0]
            if val:
                if val in acc:
                    return y, x
                acc.append(val)
    # Container
    for y in range(0, POWER, SUDOKU_STRENGTH):
        for x in range(0, POWER, SUDOKU_STRENGTH):
            acc = []
            for cy, cx in get_container_cells_array(y, x):
                val = tensor[cy][cx][0]
                if val:
                    if val in acc:
                        return y, x
                    acc.append(val)
    return None  # No error


def is_completed(tensor):
    for y in range(POWER):
        for x in range(POWER):
            if not tensor[y][x][0]:
                return False
    return True


def stage1(tensor):
    # >> Stage 1
    # In stage 1 we try look for cells with only one option ("Sole candidate")
    # By subtracting options from all neighbors
    print("STARTING STAGE 1..")
    # sleep(1)

    found = 0
    for y in range(POWER):
        for x in range(POWER):
            aisle = tensor[y][x]
            if aisle[0]:
                continue

            # Empty number here
            # Find all options for current positions
            opts = list(range(1, POWER+1))

            for y_id, x_id in get_all_neighbors(y, x):
                val = tensor[y_id][x_id][0]
                if val in opts:
                    opts.remove(val)

            # Do operation based on ammout of options
            opts_c = len(opts)
            if not opts_c:
                print(f"Oops, error!, no options for position: {x=},{y=}!")
                print_tensor(tensor)
                exit()

            elif opts_c == 1:
                print(f"Found: [{y=},{x=}] is: {opts[0]}")
                aisle[0] = opts[0]
                found += 1

                # Just to make sure we dont have an error in the algorithm
                if err := find_errors(tensor):
                    print(f"ERR in: y={err[0]} x={err[1]}")
                    exit()

                # Show status and wait for user to press enter
                print_tensor(tensor)
                if USER_WAIT:
                    input(">>")
                sleep(0.1)

                continue

            else:
                print(f"Options for [{y=},{x=}] are: {opts}")
                aisle[1] = opts
                # missing += 1
                continue
    return found


def stage2(tensor):
    # >> Stage 2
    # In stage 2 we go over each cell's row, column and container to
    #   try and find wheter its the only option cell in that array.
    # Aka "Unique candidate" method
    # NOTE: Stage 2 can only be run on tensor with populated options.

    print("STARTING STAGE 2..")
    # sleep(1)

    found = 0
    for y in range(POWER):
        for x in range(POWER):
            aisle = tensor[y][x]
            if aisle[0]:
                continue

            print(f"[Stage 2] trying to solve {y=}, {x=}")
            print(f"    Current options are: {aisle[1]}")

            # Per lane or containter Iterate over all neighboring cells and subtract their options from ours
            for arr in get_neighbor_arrays(y, x):
                print(f"Checking array: ", arr)
                opts = list(aisle[1])
                for y_id, x_id in arr:
                    temp_aisle = tensor[y_id][x_id]
                    if temp_aisle[0]:
                        continue

                    print(
                        f'> Neighbor in {y_id=}, {x_id=} has: {temp_aisle[1]}')
                    for opt in temp_aisle[1]:
                        if opt in opts:
                            opts.remove(opt)

                    if not opts:
                        print("Futile, No options already, skipping..")
                        break

                # Do operation based on ammout of options
                opts_c = len(opts)
                # if not opts_c:
                #     print(f"Oops!, no solution in position: {x=},{y=}!")
                #     print_tensor(tensor)
                #     exit()

                if opts_c == 1:
                    print(f"Found: [{y=},{x=}] is: {opts[0]}")
                    aisle[0] = opts[0]
                    found += 1

                    # After finding in stage 2,
                    # update neighbor cells options

                    for y_id, x_id in get_all_neighbors(y, x):
                        temp_a = tensor[y_id][x_id]
                        if opts[0] in temp_a[1]:
                            temp_a[1].remove(opts[0])

                    # Just to make sure we dont have an error in the algorithm
                    if err := find_errors(tensor):
                        print(f"ERR in: y={err[0]} x={err[1]}")
                        exit()

                    # Show status and wait for user to press enter
                    print_tensor(tensor)
                    if USER_WAIT:
                        input(">>")
                    sleep(0.1)
                    break
    return found


def forcing_chain_stage(tensor):
    print("STARTING STAGE Forcing Chain..")
    sleep(1)

    for y in range(POWER):
        for x in range(POWER):
            aisle = tensor[y][x]
            if aisle[0]:
                continue

            print(
                f"[ForcingChain] Running on: [{y=}, {x=}], options are: {aisle[1]}")
            # For every option
            chains = []
            for assumed_option in aisle[1]:
                print(f"> Assuming option: {assumed_option}")

                # Shadow copy the matrix
                temp_tensor = tensor.copy()

                # # Put assumed option
                # temp_tensor[y][x][0] = assumed_option

                def forced_chain(pos_y, pos_x, r_val, r_tensor) -> list:
                    # Save current find
                    current_find = [(pos_y, pos_x, r_val), ]

                    # Apply val to tensor
                    r_tensor[pos_y][pos_x][0] = r_val

                    # For all the neighbors:
                    for ry, rx in get_all_neighbors(y, x):
                        r_cell = r_tensor[ry][rx]
                        if r_cell[0]:
                            continue

                        # Remove irrelevant `r_val` option
                        r_opts = r_cell[1]
                        if r_val in r_opts:
                            r_opts.remove(r_val)

                        # Do we have only one option here?
                        if len(r_opts) == 1:
                            # print(f">> found: {ry=},{rx=} -> {r_opts[0]}")
                            # return recursion
                            return current_find + forced_chain(ry, rx, r_opts[0], r_tensor)

                        if not r_opts:
                            print("ERROR , no options, debug me!")
                            exit()
                    return current_find

                chain = forced_chain(y, x, assumed_option, temp_tensor)[1:]
                print(
                    f"> Forced chain returned: [{len(chain)} findings], here: ", chain)
                if not chain:
                    print("> Futile, skipping..")
                    break
                chains.append(chain)

            if len(chains) < 2:
                continue

            implied_findings = functools.reduce(
                lambda a, b: [o for o in a if o in b], chains)
            if not implied_findings:
                continue

            print(
                f"Found {len(implied_findings)} implied findings: ", implied_findings)
            for implied in implied_findings:
                y, x, val = implied
                tensor[y][x][0] = val

                # Just to make sure we dont have an error in the algorithm
                if err := find_errors(tensor):
                    print(f"ERR in: y={err[0]} x={err[1]}")
                    exit()

                # Show status and wait for user to press enter
                print_tensor(tensor)
                if USER_WAIT:
                    input(">>")
                sleep(0.1)

            print("Stage 3 successful so repopulating opts and running stages 1 and 2")
            return len(implied_findings)


if __name__ == '__main__':
    tensor = load_from_file(argv[1])
    print_tensor(tensor)

    found = -1
    while found:
        found = 0

        if is_completed(tensor):
            print("Completed!")
            break

        for stage in (
            stage1,
            stage2,
            forcing_chain_stage,
        ):
            if found := stage(tensor):
                print_tensor(tensor)
                print(
                    f"Finished stage with {found} founds")
                print("Rerunning because we had successful findings")
                break
