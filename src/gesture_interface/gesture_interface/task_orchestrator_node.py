import os
import yaml

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from gesture_interface.gesture_player import GesturePlayer
from gesture_interface.gesture_storage import GestureStorage
from gesture_interface_msgs.srv import ExecuteTask, PlayGesture


class TaskOrchestrator(Node):
    """Maps high-level task names to gestures and executes them."""

    def __init__(self):
        super().__init__("task_orchestrator")
        self.callback_group = ReentrantCallbackGroup()

        default_mapping = os.path.join(
            get_package_share_directory("gesture_interface"),
            "config",
            "task_mappings.yaml",
        )

        self.declare_parameter("task_mapping_file", default_mapping)
        mapping_file = self.get_parameter("task_mapping_file").value
        self.task_map = self._load_task_map(mapping_file)

        self.storage = GestureStorage(self)
        self.player = GesturePlayer(self)
        self.play_client = self.create_client(
            PlayGesture,
            "/play_gesture",
            callback_group=self.callback_group,
        )
        self.execute_srv = self.create_service(
            ExecuteTask,
            "/execute_task",
            self._handle_execute_task,
            callback_group=self.callback_group,
        )

        self.get_logger().info(
            f"Task orchestrator ready with {len(self.task_map)} mapping(s)"
        )

    def _load_task_map(self, mapping_file):
        if not os.path.exists(mapping_file):
            self.get_logger().warn(
                f"Task mapping file not found: {mapping_file}. Using empty map."
            )
            return {}

        try:
            with open(mapping_file, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except (OSError, yaml.YAMLError) as exc:
            self.get_logger().error(
                f"Failed to load task mapping file '{mapping_file}': {exc}"
            )
            return {}

        mappings = data.get("task_mappings", {})
        if not isinstance(mappings, dict):
            self.get_logger().warn("Invalid task_mappings format. Expected dictionary.")
            return {}

        normalized = {}
        for task_name, gesture_value in mappings.items():
            if isinstance(gesture_value, str):
                normalized[str(task_name)] = [gesture_value]
                continue

            if isinstance(gesture_value, list) and all(
                isinstance(item, str) and item.strip() for item in gesture_value
            ):
                normalized[str(task_name)] = gesture_value
                continue

            self.get_logger().warn(
                f"Skipping invalid mapping for task '{task_name}'. Expected string or list of strings."
            )

        return normalized

    def _duration_to_seconds(self, duration_msg):
        return duration_msg.sec + duration_msg.nanosec * 1e-9

    def _seconds_to_duration(self, seconds):
        sec = int(seconds)
        nanosec = int(round((seconds - sec) * 1e9))
        if nanosec >= 1_000_000_000:
            sec += 1
            nanosec -= 1_000_000_000
        return sec, nanosec

    def _merge_gestures(self, gesture_names):
        merged = JointTrajectory()
        time_offset = 0.0

        for index, gesture_name in enumerate(gesture_names):
            trajectory = self.storage.load(gesture_name)
            if trajectory is None or not trajectory.points:
                self.get_logger().error(
                    f"Gesture '{gesture_name}' could not be loaded or has no points"
                )
                return None

            if not merged.joint_names:
                merged.joint_names = list(trajectory.joint_names)
            elif list(trajectory.joint_names) != list(merged.joint_names):
                self.get_logger().error(
                    f"Gesture '{gesture_name}' joint names do not match the merged trajectory"
                )
                return None

            points = trajectory.points
            if index > 0 and len(points) > 1:
                points = points[1:]

            for point in points:
                merged_point = JointTrajectoryPoint()
                merged_point.positions = list(point.positions)
                merged_point.velocities = list(point.velocities)
                merged_point.accelerations = list(point.accelerations)
                merged_point.effort = list(point.effort)

                total_time = time_offset + self._duration_to_seconds(
                    point.time_from_start
                )
                sec, nanosec = self._seconds_to_duration(total_time)
                merged_point.time_from_start.sec = sec
                merged_point.time_from_start.nanosec = nanosec
                merged.points.append(merged_point)

            time_offset = self._duration_to_seconds(merged.points[-1].time_from_start)

        return merged

    def _handle_execute_task(self, request, response):
        task_name = request.task_name.strip()
        if not task_name:
            response.success = False
            response.message = "Task name cannot be empty"
            return response

        gesture_names = self.task_map.get(task_name)
        if gesture_names is None:
            response.success = False
            response.message = f"Unknown task: '{task_name}'"
            return response

        if len(gesture_names) == 1:
            if not self.play_client.wait_for_service(timeout_sec=5.0):
                response.success = False
                response.message = "Gesture manager service '/play_gesture' is unavailable"
                return response

            play_req = PlayGesture.Request()
            play_req.name = gesture_names[0]

            future = self.play_client.call_async(play_req)
            rclpy.spin_until_future_complete(self, future, timeout_sec=120.0)

            if not future.done():
                response.success = False
                response.message = (
                    f"Timed out while executing task '{task_name}' on gesture '{gesture_names[0]}'"
                )
                return response

            result = future.result()
            if result is None:
                response.success = False
                response.message = (
                    f"Task '{task_name}' failed: no response while playing '{gesture_names[0]}'"
                )
                return response

            response.success = bool(result.success)
            response.message = result.message
            return response

        merged_trajectory = self._merge_gestures(gesture_names)
        if merged_trajectory is None:
            response.success = False
            response.message = (
                f"Task '{task_name}' failed while loading or merging gesture sequence"
            )
            return response

        if not self.player.play(merged_trajectory):
            response.success = False
            response.message = (
                f"Task '{task_name}' failed during merged trajectory playback"
            )
            return response

        response.success = True
        response.message = (
            f"Task '{task_name}' completed via merged playback of {len(gesture_names)} gesture(s)"
        )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = TaskOrchestrator()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
