from statistics import median
import math

def sea_level_projection(
        lower_baseline: int = 1995,
        upper_baseline: int = 2014,
        slr_50: float = 0.12,
        projection: int = 2030,
        target: int = 2023,
        new_baseline_lower: int = 1981,
        new_baseline_upper: int = 2010,
        sea_level_century: float = 47.96 / 100
) -> tuple[float, float]:
    
    #Calculate the midtpoint (median) of the orginalbaselines
    midtpoint_baseline = math.ceil(median([lower_baseline, upper_baseline]))
    
    #Calculate the difference between projection year and median year
    projection_diff = math.floor(projection - midtpoint_baseline)

    #Calculate the difference between target and projection to baseline
    target_diff = math.floor(target - midtpoint_baseline)
    fraction = target_diff / projection_diff
    rise_baseline = slr_50 * fraction

    #Calculate median of the new baseline 
    new_baseline = math.floor(median([new_baseline_lower, new_baseline_upper]))

    #Calcualte the rate of change from newbaseline midtpoint to baseline midtpoint
    rate = slr_50 / projection_diff
    baseline_diff = midtpoint_baseline / new_baseline
    slr_change = baseline_diff * rate

    #Calculate the sea level change from baseline to target
    slr_change_new_baseline = slr_change + rise_baseline
    sea_level_from_target_to_late_century_meters = sea_level_century - slr_change_new_baseline

    sea_level_from_target_to_late_century_centimeter = sea_level_from_target_to_late_century_meters * 100

    return sea_level_from_target_to_late_century_meters, sea_level_from_target_to_late_century_centimeter
