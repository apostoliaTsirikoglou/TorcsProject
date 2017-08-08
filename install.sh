#!/bin/bash

gym_torcs="$HOME/Documents/Thesis_work/gym_torcs"
TorcsProjectVersion="TorcsProjectVersion"

# version / commit installed
git log -n 1 > $gym_torcs/agent_version

# agents folder
rm -rf $gym_torcs/agents
cp -r agents $gym_torcs/agents

# run file
rm $gym_torcs/run_ddpg.py
cp run_ddpg.py $gym_torcs/

# run file
rm $gym_torcs/run_ddpg_cnn.py
cp run_ddpg_cnn.py $gym_torcs/
