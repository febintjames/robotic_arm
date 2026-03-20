# trajectory_builder.py

from trajectory_msgs.msg import JointTrajectory


class TrajectoryBuilder:

    def __init__(self, node):
        self.node = node

    def validate(self, trajectory: JointTrajectory):
        if not trajectory.points:
            self.node.get_logger().error("Empty trajectory")
            return False

        if not trajectory.joint_names:
            self.node.get_logger().error("No joint names")
            return False

        return True
