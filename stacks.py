"""Contains the stack implementation used in group management"""
from textual.widgets import ListItem


class GroupsStack:
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


class OperationsStack:
    """An implementation of the stack data-structure in order to store operations effectively"""

    def __init__(self) -> None:
        """Creates the stack and the stack variables"""

        self.__stack_array: list[ListItem] = []

    def pop(self) -> ListItem:
        """Pops the tops element of the stack

        Returns:
            ListItem - the top most element in the stack
        """

        return self.__stack_array.pop()

    def push(self, item: ListItem) -> None:
        """Pushes an element on to the stack

        Args:
            item: ListItem - the item to be added to the stack
        """

        self.__stack_array.append(item)

    def peek(self) -> ListItem:
        """Returns the uppermost value in the stack without removing it

        Returns:
            ListItem - the top most element in the stack
        """

        return self.__stack_array[-1]

    def get_len(self) -> int:
        """Returns the full stacks length

        Returns:
            int - the full stacks length
        """

        return len(self.__stack_array)
