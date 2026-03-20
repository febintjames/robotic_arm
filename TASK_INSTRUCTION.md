
## Overview
This assessment evaluates your ability to transition a robotic system from a kinematic, "fake-hardware" environment to a dynamic **Gazebo-based physics simulation**. You are tasked with implementing a **Learning from Demonstration (LfD)** workflow where the robot is taught to interact with and manipulate physical objects.

Your goal is to extend the existing `gesture_interface` to support physical object alignment and high-level task orchestration within a simulated world.

**Time Limit:** [2 days]
**Environment:** ROS 2 Humble (Ubuntu 22.04), Gazebo Classic or Sim

---

## Part 1: Physics Integration & Environment Design

The current system lacks physical interaction. You must bridge the gap between MoveIt 2 and a physics-heavy simulation where collisions, mass, and friction are active.

**Requirements:**
1.  **Gazebo Bring-up:** Integrate `gazebo_ros2_control` into the 3-DOF arm URDF. Ensure the robot spawns in a Gazebo world with active controllers capable of following MoveIt trajectories.
2.  **T-Shape Object:** Design and spawn a **"T-shape"** object as a separate URDF/SDF. 
    * It must have realistic **inertial properties** (mass and inertia tensor) to prevent "jittering."
    * It must include **collision geometry** that allows the robot's end rod to physically push it.
3.  **Target Highlight Zone:** Create a **"Highlight Zone"** in the Gazebo world.
    * This should be a visual-only marker (e.g., a green semi-transparent plane) representing the target destination.
    * It must have no collision properties so the T-shape can reside within it.

---

## Part 2: Learning from Demonstration (The Push Task)

Once the physics environment is stable, you will use your recording system to "teach" the robot how to manipulate the T-shape.

**Requirements:**
1.  **Manual Teaching:** Use the MoveIt RViz MotionPlanning plugin or interactive markers to manually move the robot's end rod to push the T-shape from its starting point toward the Highlight Zone.
2.  **Task Capture:** Utilize your existing `GestureRecorder` to capture this interaction. 
3.  **Data Fidelity:** The recorded gesture must accurately replicate the contact dynamics. If the motion is too fast or the trajectory is slightly off, the T-shape may slide incorrectly or tip over.
4.  **Deliverable:** A saved gesture file named `align_t_task.yaml` that successfully completes the alignment when replayed.

---

## Part 3: The Task Orchestrator

You must move beyond simple file playback and implement a high-level logic node that manages "Tasks" rather than just "Gestures."

**Requirements:**
1.  **Task Orchestrator Node:** Create a new node that acts as a manager for multiple robot skills.
2.  **Command Interface:** Implement a ROS 2 interface (e.g., a Service `/execute_task`) that accepts a `task_name` string.
3.  **Dynamic Mapping:** The node must map high-level task names to specific gesture files (e.g., "align_t" -> `align_t_task.yaml`).
4.  **Execution Logic:** When a task is called, the orchestrator must trigger the `GesturePlayer` to execute the corresponding dataset and monitor the result.

---

## Demonstration & Constraints

**The Challenge:**
To verify your solution, the robot must be able to reset the environment and successfully align the T-shape into the Highlight Zone autonomously by calling the orchestrator.

**Success Criteria:**
1.  **Physical Interaction:** The robot end rod successfully collides with and moves the T-shape without the object glitching or passing through the arm.
2.  **Accuracy:** Upon playback, at least 70% of the T-shape must end up within the boundaries of the Highlight Zone.
3.  **Modularity:** The `task_orchestrator` should be separate from the `GestureManager`, communicating via ROS 2 services or actions.
4.  **Robustness:** The system handles errors gracefully (e.g., if a requested task name does not exist in the dataset).

## Submission
Please zip your workspace (excluding `build` and `install`) and include a `TASK_LOG.md` explaining:
1.  The physics parameters (friction, mass) you used for the T-shape to ensure stable manipulation.
2.  The architectural relationship between the `Task Orchestrator` and the `GestureManager`.
3.  Instructions on how to launch the full simulation environment and trigger the "Align T" task.
