#!/usr/bin/env python3
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
        for each_index in range(10_000):
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