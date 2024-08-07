"""Contains the stack implementation used in group management"""


class Stack:
    """An implementation of the stack data-structure in order to manage groups effectively"""
    def __init__(self) -> None:
        """Creates the stack and the stack variables"""

        self.__stack_array: list[tuple[str, tuple[int, int]]] = []

    def pop(self) -> tuple[str, tuple[int, int]]:
        """Pops the tops element of the stack

        Returns:
            tuple[str, tuple[int, int]] - the top most element in the stack
        """

        return self.__stack_array.pop()

    def push(self, item: tuple[str, tuple[int, int]]) -> None:
        """Pushes an element on to the stack

        Args:
            item: tuple[str, tuple[int, int]] - the item to be added to the stack
        """

        self.__stack_array.append(item)
