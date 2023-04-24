#!/usr/bin/env python3
from rigorous_recorder import Recorder
from random import random, sample, choices
recorder = Recorder()

# parent data
experiment_recorder = Recorder(experiment=1).set_parent(recorder)
episode_recorder    = Recorder(episode=1).set_parent(experiment_recorder)

episode_recorder.push(x=1, y=1) # timestep1
episode_recorder.push(x=2, y=2) # timestep2
episode_recorder.push(x=3, y=3) # timestep3

episode_recorder.add(accuracy=random(), index=1)
episode_recorder.commit()

for each in recorder.all_records:
    print(f'''each = {each}''')

print(f'''recorder.frame = {recorder.frame}''')
print(f'''episode_recorder.frame = {episode_recorder.frame}''')

episode_recorder.save_to("data.ignore/episode_recordr.pickle")