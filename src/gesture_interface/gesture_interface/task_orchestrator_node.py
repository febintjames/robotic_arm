import os
import yaml

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node

from gesture_interface_msgs.srv import ExecuteTask, PlayGesture


class TaskOrchestrator(Node):
    """Maps high-level task names to gestures and executes them."""

    def __init__(self):
        super().__init__("task_orchestrator")

        default_mapping = os.path.join(
            get_package_share_directory("gesture_interface"),
            "config",
            "task_mappings.yaml",
        )

        self.declare_parameter("task_mapping_file", default_mapping)
        mapping_file = self.get_parameter("task_mapping_file").value
        self.task_map = self._load_task_map(mapping_file)

        self.play_client = self.create_client(PlayGesture, "/play_gesture")
        self.execute_srv = self.create_service(
            ExecuteTask,
            "/execute_task",
            self._handle_execute_task,
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

        return {str(k): str(v) for k, v in mappings.items()}

    def _handle_execute_task(self, request, response):
        task_name = request.task_name.strip()
        if not task_name:
            response.success = False
            response.message = "Task name cannot be empty"
            return response

        gesture_name = self.task_map.get(task_name)
        if gesture_name is None:
            response.success = False
            response.message = f"Unknown task: '{task_name}'"
            return response

        if not self.play_client.wait_for_service(timeout_sec=5.0):
            response.success = False
            response.message = "Gesture manager service '/play_gesture' is unavailable"
            return response

        play_req = PlayGesture.Request()
        play_req.name = gesture_name

        future = self.play_client.call_async(play_req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=120.0)

        if not future.done():
            response.success = False
            response.message = (
                f"Timed out while executing task '{task_name}' using gesture '{gesture_name}'"
            )
            return response

        result = future.result()
        if result is None:
            response.success = False
            response.message = (
                f"Task '{task_name}' failed: no response from gesture manager"
            )
            return response

        response.success = bool(result.success)
        if result.success:
            response.message = (
                f"Task '{task_name}' completed via gesture '{gesture_name}'"
            )
        else:
            response.message = (
                f"Task '{task_name}' failed via gesture '{gesture_name}': {result.message}"
            )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = TaskOrchestrator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
