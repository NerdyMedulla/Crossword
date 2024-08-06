import sys
from collections import deque

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        for variable in self.domains:
            words_to_remove = []
            for word in self.domains[variable]:
                if len(word) != variable.length:
                    words_to_remove.append(word)
            for word in words_to_remove:
                self.domains[variable].remove(word)

    def revise(self, x, y):
        revised = False
        if (x, y) in self.crossword.overlaps:
            overlap = self.crossword.overlaps[x, y]
            if overlap:
                i, j = overlap
                words_to_remove = []
                for x_word in self.domains[x]:
                    satisfy = False
                    for y_word in self.domains[y]:
                        if x_word[i] == y_word[j]:
                            satisfy = True
                            break
                    if not satisfy:
                        words_to_remove.append(x_word)
                for word in words_to_remove:
                    self.domains[x].remove(word)
                    revised = True
        return revised

    def ac3(self, arcs=None):
        if arcs is None:
            arcs = [(x, y) for x in self.domains for y in self.crossword.neighbors(x)]

        queue = deque(arcs)
        while queue:
            (x, y) = queue.popleft()
            if self.revise(x, y):
                if not self.domains[x]:
                    return False
                for neighbor in self.crossword.neighbors(x):
                    if neighbor != y:
                        queue.append((neighbor, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return all(variable in assignment for variable in self.crossword.variables)

    def consistent(self, assignment):
        if len(set(assignment.values())) < len(assignment):
            return False

        for variable, word in assignment.items():
            if len(word) != variable.length:
                return False

            for neighbor in self.crossword.neighbors(variable):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[variable, neighbor]
                    if word[i] != assignment[neighbor][j]:
                        return False
        return True

    def order_domain_values(self, var, assignment):
        def count_conflicts(value):
            count = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    for neighbor_value in self.domains[neighbor]:
                        if value[i] != neighbor_value[j]:
                            count += 1
            return count

        return sorted(self.domains[var], key=count_conflicts)

    def select_unassigned_variable(self, assignment):
        unassigned_variables = [v for v in self.crossword.variables if v not in assignment]

        min_remaining = min(unassigned_variables, key=lambda var: len(self.domains[var]))
        candidates = [var for var in unassigned_variables if len(self.domains[var]) == len(self.domains[min_remaining])]

        if len(candidates) > 1:
            return max(candidates, key=lambda var: len(self.crossword.neighbors(var)))

        return candidates[0]



    def backtrack(self, assignment):
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(var, assignment):
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if self.consistent(new_assignment):
                result = self.backtrack(new_assignment)
                if result:
                    return result

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
