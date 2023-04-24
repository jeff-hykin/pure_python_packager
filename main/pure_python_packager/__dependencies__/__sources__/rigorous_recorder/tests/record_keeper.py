#!/usr/bin/env python3
from rigorous_recorder import RecordKeeper
from random import random, sample, choices
recorder = RecordKeeper()

# parent data
experiment_recorder = RecordKeeper(experiment=1).set_parent(recorder)
episode_recorder    = RecordKeeper(episode=1).set_parent(experiment_recorder)

episode_recorder.push(x=1, y=1) # timestep1
episode_recorder.push(x=2, y=2) # timestep2
episode_recorder.push(x=3, y=3) # timestep3

episode_recorder.add(accuracy=random(), index=1)
episode_recorder.commit()

episode_recorder.save_to("data.ignore/episode_recorder.pickle")