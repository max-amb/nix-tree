"""Contains the stacks and queue implementations used in throughout the program

Note:
    Inheritance is useless due to all the stacks being of different data types by design, to avoid confusion
"""

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


class OperationsQueue:
    """Defines an operations queue for reversing the order of the operations stack"""

    def __init__(self) -> None:
        """Creates the queue list"""

        self.__queue: list[ListItem] = []

    def enqueue(self, item: ListItem) -> None:
        """Takes in an item and places it at the front of the queue

        Args:
            item: ListItem - the item to add
        """

        self.__queue.insert(0, item)

    def dequeue(self) -> ListItem:
        """Removes the uppermost item in the queue - using order FIFO order of operations

        Returns:
            ListItem - the item at the front of the queue
        """

        return self.__queue.pop(0)

    def get_len(self) -> int:
        """Returns the queues length

        Returns:
            int - the length of the queue
        """

        return len(self.__queue)

    def return_queue(self) -> list[ListItem]:
        """Returns the queue as a list

        Returns:
            list[ListItem] - the queue as a list
        """

        return self.__queue
