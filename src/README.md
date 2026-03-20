# Gesture Interface for 3-DOF Robot Arm



## Overview
This ROS 2 package implements a **Gesture System** for a 3-DOF robotic arm.  
It allows you to **record**, **save**, and **play back** robot motions (gestures) with high fidelity using MoveIt 2.

A **gesture** is a named sequence of joint states captured over time.  
This system is modular, with separate components for **recording**, **storage**, and **playback**.

---

## Part  1 - System Bring-up & Debugging

-   Fixes Applied

1.  Corrected URDF  for  3-DOF arm.
2.  Included ros2_control plugin in URDF 
3.  Additional joint added in URDF
4.  Corrected  robot name difference in parameter file
5.  Updated launch file to include moveitgroup and  ros2 control node. [Refer demo.launch.py for changes made]
6.  Verified ros2_control YAML configuration for joint controllers and made sure joint names match the URDF.
7. Updated launch file to include joint state publisher
8.  ros_parameter header missing from parameter files


##  Tested in RViz:

MotionPlanning plugin can plan and execute motions.

/joint_states topic correctly publishes simulated or real joint states.

## Architecture

            ┌─────────────────────┐
            │  User / RViz Motion │
            │  Planning Commands  │
            └─────────┬───────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │  GestureManager     │
            │  (ROS 2 Node)       │
            └─────────┬───────────┘
     Start/Stop Recording / Play
        /           |          \
       ▼            ▼           ▼
┌────────────────┐ ┌──────────────┐ ┌───────────────┐
│ GestureRecorder│ │ GestureStorage│ │ GesturePlayer │
│ (/joint_states│ │ save/load │ │ Executes │
│ subscriber) │ │ YAML files │ │ Trajectory │
└────────────────┘ └──────────────┘ └───────────────┘
▲
│
│
Joint States Published
by Robot
/simulated or real/


### Components

- **GestureManager Node**:  
  - Provides ROS 2 services:
    - `/start_recording` → Begin capturing joint states.
    - `/stop_save_recording` → Stop recording and save gesture.
    - `/play_gesture` → Execute a saved gesture.
  - Coordinates Recorder, Storage, and Player.

- **GestureRecorder**:  
  - Subscribes to `/joint_states`.
  - Records joint positions over time while recording is active.

- **GestureStorage**:  
  - Saves and loads gestures as **YAML files**.
  - Stores gestures in the `gestures` folder inside the `gesture_interface` package:
    ```
    <workspace>/src/gesture_interface/gestures/
    ```

- **GesturePlayer**:  
  - Plays back gestures using **MoveIt 2** trajectory execution.
  - Ensures motions are executed via the planning pipeline.

---

## Installation

1. Make sure ROS 2 Humble is installed.
2. Clone your workspace:
   ```bash
   mkdir -p ~/ws_gesture/src
   cd ~/ws_gesture/src
   git clone <repo_name> gesture_interface

cd ~/ws_gesture
colcon build
source install/setup.bash

Usage

1. Launch URDF in RVIZ with Moveit Motion planning

    ros2 launch simple_moveitmanual demo.launch.py 

    Please keep the fixed frame as "base_link". The "demo.launch.py" is adapted from the "moveit.launch.py".

2. Launch Gesture Manager

    ros2 launch gesture_interface gesture_interface.launch.py 

3.  Record a Gesture

    -   Start Recording:

    ros2 service call /start_recording gesture_interface_msgs/srv/StartRecording


    -   Move the robot in RViz using Plan & Execute.

    -   Joint states are recorded automatically.

4.  Stop & Save Recording:

    ros2 service call /stop_save_recording gesture_interface_msgs/srv/StopSaveRecording "{name: 'test_gesture'}"


    -   This saves the gesture as test_gesture.yaml in:  <workspace>/src/gesture_interface/gestures/test_gesture.yaml

5.  Play a Gesture

    ros2 service call /play_gesture gesture_interface_msgs/srv/PlayGesture "{name: 'test_gesture'}"


    -   The recorded motion will be executed via MoveIt 2.

##  Notes

-   Gestures persist across restarts since they are stored as YAML files.

-   Playback uses MoveIt 2 planning pipeline, ensuring valid trajectories.

-   Recording does not require stopping RViz or the node between gestures.- 

-   File format is human-readable YAML, with joint names and time-stamped positions.

##  Submission Checklist

-   All bugs in the original MoveIt configuration have been resolved.

-   Gesture system is modular: Recorder → Storage → Player.

-   Recorded gesture test_gesture can be played back via service call.

-   All gestures are stored in the package folder gestures/ for easy persistence and sharing.

##  Example YAML (gesture file)

joint_names:
- joint1
- joint2
- joint3
points:
- positions:
  - 0.0
  - 0.0
  - 0.0
  time_from_start: 0.0
- positions:
  - 0.0
  - 0.0
  - 0.0
  time_from_start: 0.1
- 
