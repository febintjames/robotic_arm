import rclpy
from threading import Event

from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory


class GesturePlayer:

    def __init__(self, node):
        self.node = node
        self.callback_group = ReentrantCallbackGroup()

        self.client = ActionClient(
            node,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory",
            callback_group=self.callback_group,
        )

    def play(self, trajectory: JointTrajectory):
        if not self.client.wait_for_server(timeout_sec=5.0):
            self.node.get_logger().error("Controller action server not available")
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        goal_done = Event()
        result_done = Event()
        goal_error = None
        result_error = None
        goal_handle = None
        execution_ok = False

        future = self.client.send_goal_async(goal)

        def on_goal_done(done_future):
            nonlocal goal_error, goal_handle
            try:
                goal_handle = done_future.result()
            except Exception as exc:  # pragma: no cover - defensive path
                goal_error = exc
            finally:
                goal_done.set()

        future.add_done_callback(on_goal_done)

        if not goal_done.wait(timeout=10.0):
            self.node.get_logger().error("Timed out waiting for trajectory goal response")
            return False

        if goal_error is not None:
            self.node.get_logger().error(f"Failed to send trajectory goal: {goal_error}")
            return False

        if goal_handle is None or not goal_handle.accepted:
            self.node.get_logger().error("Trajectory rejected")
            return False

        result_future = goal_handle.get_result_async()

        def on_result_done(done_future):
            nonlocal result_error, execution_ok
            try:
                result = done_future.result()
                execution_ok = result.status == 4
            except Exception as exc:  # pragma: no cover - defensive path
                result_error = exc
            finally:
                result_done.set()

        result_future.add_done_callback(on_result_done)

        if not result_done.wait(timeout=120.0):
            self.node.get_logger().error("Timed out waiting for trajectory execution result")
            return False

        if result_error is not None:
            self.node.get_logger().error(
                f"Failed while waiting for trajectory result: {result_error}"
            )
            return False

        if not execution_ok:
            self.node.get_logger().error("Trajectory execution did not succeed")
            return False

        self.node.get_logger().info("Trajectory execution completed")
        return True
