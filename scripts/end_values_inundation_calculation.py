import math

def iteration(end: int, initial: int, increment: int) -> int:
    iterations: float = (end - initial) / increment + 1
    iter: int = math.ceil(iterations)

    return iter

def end_val(iter: int, initial: int, increment: int) -> int:
    if iter == 0:
        return initial
    end: int = initial + ((iter - 1) * increment)

    return end

iter_result = iteration(end=246, initial=100, increment=1)
print(f"Antal iterationer: {iter_result}")

end_result = end_val(iter_result, 100, 1)
print(f"Slutværdi: {end_result:.0f} cm")
