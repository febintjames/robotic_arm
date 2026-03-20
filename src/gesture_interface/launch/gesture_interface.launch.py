# gesture_interface.launch.py

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    gesture_node = Node(
        package="gesture_interface",
        executable="gesture_manager_node",
        output="screen",
    )

    task_orchestrator_node = Node(
        package="gesture_interface",
        executable="task_orchestrator_node",
        output="screen",
    )

    return LaunchDescription([
        gesture_node,
        task_orchestrator_node,
    ])
