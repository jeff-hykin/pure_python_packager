# What is this?

I needed an efficient data logger for my machine learning experiments. Specifically one that
- could log in a hierarchical way (not one big global logging variable)
- while still having a flat table-like structure for performing queries/summaries
- without having tons of duplicated data

This library would likely work well with PySpark

# What is a Use-case Example?

Lets say you're going to perform
- 3 experiments
- each experiment has 10 episodes
- each episode has 100,000 timesteps
- there is an an `x` and a `y` value at each timestep <br>

#### Example goal:
- We want to get the average `x` value across all timesteps in episode 2 (we don't care what experiment they're from)


Our timestamp data could look like:
```python
record1 = { "x":1, "y":1 } # first timestep
record2 = { "x":2, "y":2 } # second timestep
record3 = { "x":3, "y":3 } # third timestep
```

#### Problem
Those records don't contain the experiment number or the episode number (and we need those for our goal)

#### Bad Solution

Duplicating the data would provide a flat structure, but (for 100,000 timesteps) thats a huge memory cost
```python
record1 = { "x":1, "y":1, "episode":1, "experiment": 1, } # first timestep
record2 = { "x":2, "y":2, "episode":1, "experiment": 1, } # second timestep
record3 = { "x":3, "y":3, "episode":1, "experiment": 1, } # third timestep
```

#### Good-ish Solution

We could use references to be both more efficient and allow adding parent data after the fact

```python
# parent data
experiment_data = { "experiment": 1 }
episode_data    = { "episode":1, "parent": experiment_data }

record1 = { "x":1, "y":1, "parent": episode_data } # first timestep
record2 = { "x":2, "y":2, "parent": episode_data } # second timestep
record3 = { "x":3, "y":3, "parent": episode_data } # third timestep
```

We could reduce the cost of key duplication by having shared keys

```python
# parent data
experiment_data = { "experiment": 1 }
episode_data    = { "episode":1, "parent": experiment_data }

episode_keeper = {"parent": episode_data} # timestep 0
episode_keeper = { "x":[1],     "y":[1],     "parent": episode_data} # first timestep (keys added on-demand)
episode_keeper = { "x":[1,2],   "y":[1,2],   "parent": episode_data} # second timestep
episode_keeper = { "x":[1,2,3], "y":[1,2,3], "parent": episode_data} # third timestep
```

#### How does Rigorous Recorder Fix This?

The "Good-ish Solution" above is still crude, this library cleans it up
1. The `Recorder` class in this library is the core/pure data structure
2. The `ExperimentCollection` class automates common boilerplate for saving (python pickle), catching errors, managing experiments, etc

```python
from rigorous_recorder import Recorder
recorder = Recorder()

# parent data
experiment_recorder = Recorder(experiment=1).set_parent(recorder)
episode_recorder    = Recorder(episode=1).set_parent(experiment_recorder)

episode_recorder.push(x=1, y=1) # timestep1
episode_recorder.push(x=2, y=2) # timestep2
episode_recorder.push(x=3, y=3) # timestep3

recorder.save_to("where/ever/you_want.pickle")
```

# How do I use this?

`pip install rigorous-recorder`

```python
from rigorous_recorder import RecordKeeper, ExperimentCollection

from statistics import mean as average
from random import random, sample, choices

collection = ExperimentCollection("data/my_study") # <- this string is a filepath 
number_of_new_experiments = 1

for _ in range(number_of_new_experiments):
    
    # at the end (even when an error is thrown), all data is saved to disk automatically
    # experiment number increments based on the last saved-to-disk experiment number
    # running again (after error) won't double-increment the experiment number (same number until non-error run is achieved)
    with collection.new_experiment() as experiment_recorder:
        # we can create a hierarchy like this:
        # 
        #                          experiment_recorder
        #                           /              \
        #               model1_recorder           model2_recorder
        #                /        |                 |           \
        # m1_train_recorder m1_test_recorder   m2_test_recorder m2_train_recorder
        # 
        model1_recorder = RecordKeeper(model="model1").set_parent(experiment_recorder)
        model2_recorder = RecordKeeper(model="model2").set_parent(experiment_recorder)
        
        # 
        # training
        # 
        model1_train_recorder = RecordKeeper(training=True).set_parent(model1_recorder)
        model2_train_recorder = RecordKeeper(training=True).set_parent(model2_recorder)
        for each_index in range(100_000):
            # one approach
            model1_train_recorder.push(index=each_index, loss=random())
            
            # alternative approach (same outcome)
            model2_train_recorder.add(index=each_index)
            # - this way is very handy for adding data in one method (like a loss func)
            #   while calling .commit() in a different method (like update weights)
            model2_train_recorder.add({ "loss": random() })
            model2_train_recorder.commit()
            
        # 
        # testing
        # 
        model1_test_recorder = RecordKeeper(testing=True).set_parent(model1_recorder)
        model2_test_recorder = RecordKeeper(testing=True).set_parent(model2_recorder)
        for each_index in range(500):
            # one method
            model1_test_recorder.push(
                index=each_index,
                accuracy=random(),
            )
            
            # alternative way (same outcome)
            model2_test_recorder.add(index=each_index, accuracy=random())
            model2_test_recorder.commit()


# 
# 
# Analysis
# 
# 

all_records = collection.records
print("first record", all_records[0]) # behaves just like a regular dictionary

# slice across both models (first 500 training records from both models)
records_first_half_of_time = tuple(each for each in all_records if each["training"] and each["index"] < 500)
# average loss across both models
first_half_average_loss = average(tuple(each["loss"] for each in records_first_half_of_time))
# average only for model 1
model1_first_half_loss = average(tuple(each["loss"] for each in records_first_half_of_time if each["model"] == "model1"))
# average only for model 2
model2_first_half_loss = average(tuple(each["loss"] for each in records_first_half_of_time if each["model"] == "model2"))
```

# What are some other details?

The `ExperimentCollection` adds 6 keys as a parent to every record:
```
experiment_number     # int
error_number          # int, is only incremented for back-to-back error runs
had_error             # boolean for easy filtering
experiment_start_time # the output of time.time() from python's time module
experiment_end_time   # the output of time.time() from python's time module
experiment_duration   # the difference between start and end (for easy graphing/filtering)
```
