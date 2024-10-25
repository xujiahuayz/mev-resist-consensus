import timeit
import random

LIST_CHOICE = range(10_000)


print(timeit.timeit(lambda: random.choice(LIST_CHOICE), number=1_000_000))
print(timeit.timeit(lambda: random.choices(LIST_CHOICE, k=1_000), number=1_000))
