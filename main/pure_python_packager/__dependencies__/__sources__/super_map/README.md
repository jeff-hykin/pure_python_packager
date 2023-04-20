# What is this?

A python package that provides an alternative to `dict` that is much easier for lazy people to use.

# How do I use this?

`pip install super_map`


```python
from super_map import Map, LazyDict

item = Map()

# no error
item["value"]["subvalue"] = True

# prints true
print(item.value.subvalue == item["value"]["subvalue"]) # prints true

# dont need .items()
for each_key, each_value in item:
    print(each_key)

for each_key in item[Map.Keys]:
    print(each_key)

for each_key in item[Map.Values]:
    print(each_key)

value = item.a.b.c.d.e
if not value:
    # this prints out
    print("item.a.b.c.d.e doesn't exist")

item_as_dict = item[Map.Dict]

item.f.g.h += 1
print('will print out 1:', item.f.g.h)
```
