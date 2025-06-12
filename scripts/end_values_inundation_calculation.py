import math

'''
Funktionalitet til at udregne end values og num of iterations i Create Inundation værktøjet fra Inundation Modellen
'''


def iteration(end, initial, increment):
    iterations = (end - initial) / increment + 1
    iter = math.ceil(iterations)

    return  iter

def end_val(iter, initial, increment):
    if iter == 0:
        return initial
    end = initial + ((iter - 1) * increment)

    return end

iter_result = iteration(200, 100, 1)
print(f"Antal iterationer: {iter_result}")

end_result = end_val(iter_result, 100, 1)
print(f"Slutværdi: {end_result:.0f} cm")
