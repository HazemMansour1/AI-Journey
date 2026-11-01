
from task_extractor import convert_to_hours

# Full-time employee
print(convert_to_hours(1, "week", 8, 5))

# AI Engineering student (90 minutes daily)
print(convert_to_hours(1, "week", 1.5, 7))

# Part-time worker (4 hours/day, 5 days/week)
print(convert_to_hours(1, "week", 4, 5))