# gesture_player.py

import rclpy
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory


class GesturePlayer:

    def __init__(self, node):
        self.node = node

        self.client = ActionClient(
            node,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory",
        )

    def play(self, trajectory: JointTrajectory):

        if not self.client.wait_for_server(timeout_sec=5.0):
            self.node.get_logger().error("Controller action server not available")
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self.node, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Trajectory rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self.node, result_future)

        self.node.get_logger().info("Trajectory execution completed")
        return True
