# TASK_LOG

## 1. Physics Parameters for Stable T-Shape Manipulation

### T-shape model parameters
- Model file: `src/simple_moveitmanual/models/t_shape/model.sdf`
- Mass: `1.2 kg`
- Inertia tensor:
  - `ixx=0.0028`
  - `iyy=0.0052`
  - `izz=0.0061`
  - Off-diagonal terms set to `0.0`
- Contact/friction (both stem and top bar collisions):
  - `mu=0.75`
  - `mu2=0.75`
  - restitution: `0.02`

These values were chosen to avoid jitter/sliding artifacts while still allowing controlled pushes from the rod tip.

### Robot-side contact/stability parameters
- Gazebo robot file: `src/simple_moveitmanual/urdf/simplearm_gazebo.urdf`
- Joint damping/friction:
  - `joint1`: damping `0.3`, friction `0.12`
  - `joint2`: damping `0.25`, friction `0.1`
  - `joint3`: damping `0.2`, friction `0.08`
- End-effector (`tcp`) surface:
  - `mu1=1.2`, `mu2=1.2`
  - contact gains: `kp=150000.0`, `kd=10.0`

### World physics
- World file: `src/simple_moveitmanual/worlds/align_t_world.world`
- ODE solver settings:
  - `max_step_size=0.001`
  - `real_time_update_rate=1000`
  - `real_time_factor=1.0`

## 2. Task Orchestrator vs GestureManager Architecture

### Nodes
- `gesture_manager_node`:
  - Owns recording/saving/playback.
  - Exposes `/start_recording`, `/stop_save_recording`, `/play_gesture`.
- `task_orchestrator_node`:
  - Owns high-level task execution.
  - Exposes `/execute_task`.
  - Maps task names to gesture dataset names using `config/task_mappings.yaml`.
  - Calls `/play_gesture` as a client and returns success/failure with context.

### Separation and communication
- The orchestrator is a separate node and does not access recorder/player internals directly.
- Coordination happens through ROS 2 services (`ExecuteTask -> PlayGesture`) to preserve modularity.

## 3. Launch and Run Instructions

### Build
```bash
cd /home/febintj007/Desktop/replay_sim
colcon build
source install/setup.bash
```

### Launch full simulation (Gazebo + MoveIt)
```bash
ros2 launch simple_moveitmanual sim_task.launch.py
```

### Launch gesture + task services
```bash
ros2 launch gesture_interface gesture_interface.launch.py
```

### Trigger autonomous Align-T task
```bash
ros2 service call /execute_task gesture_interface_msgs/srv/ExecuteTask "{task_name: 'align_t'}"
```

### Optional: replay directly
```bash
ros2 service call /play_gesture gesture_interface_msgs/srv/PlayGesture "{name: 'align_t_task'}"
```

## Notes
- Deliverable gesture dataset added: `src/gesture_interface/gestures/align_t_task.yaml`.
- Highlight zone is visual-only (no collision) in `models/highlight_zone/model.sdf`.
- T-shape object is a separate dynamic SDF model with inertial + collision geometry in `models/t_shape/model.sdf`.
