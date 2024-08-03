x = {"x": 1, "y": 2, "z": 0}
while True:
    swapped = False
    for i in range(0, len(x)):
        if list(x.values())[i-1] > list(x.values())[i]:
            list(x.items())[i-1], list(x.items())[i] = list(x.items())[i], list(x.items())[i-1]
            swapped = True
    if not swapped:
        break
print(x)
