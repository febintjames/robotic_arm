# gesture_recorder.py

import time
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from threading import Thread, Event


class GestureRecorder:
    """Records joint states over time into a JointTrajectory."""

    def __init__(self, node, rate=10):
        self.node = node
        self.joint_states = None
        self.traj = None
        self.recording_thread = None
        self.stop_event = Event()
        self.rate = rate  # samples per second

        # Subscribe to /joint_states
        self.node.create_subscription(
            JointState,
            "/joint_states",
            self.joint_callback,
            10,
        )

    def joint_callback(self, msg):
        self.joint_states = msg

    def start(self):
        """Start recording in a background thread."""
        if self.recording_thread and self.recording_thread.is_alive():
            return False

        if not self.joint_states:
            self.node.get_logger().warn("No joint states available yet")
            return False

        self.traj = JointTrajectory()
        self.traj.joint_names = list(self.joint_states.name)
        self.stop_event.clear()

        self.recording_thread = Thread(target=self._record_loop)
        self.recording_thread.start()
        return True

    def _record_loop(self):
        t = 0.0
        dt = 1.0 / self.rate
        while not self.stop_event.is_set():
            if self.joint_states:
                point = JointTrajectoryPoint()
                point.positions = list(self.joint_states.position)
                point.time_from_start.sec = int(t)
                point.time_from_start.nanosec = int((t % 1.0) * 1e9)
                self.traj.points.append(point)
            time.sleep(dt)
            t += dt

    def stop(self) -> JointTrajectory | None:
        """Stop recording and return the captured trajectory."""
        if self.recording_thread:
            self.stop_event.set()
            self.recording_thread.join()
            return self.traj
        return None
