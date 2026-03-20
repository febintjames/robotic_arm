from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import TimerAction
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    package_name = "simple_moveitmanual"
    package_share = get_package_share_directory(package_name)

    is_sim_arg = DeclareLaunchArgument(
        "is_sim",
        default_value="true"
    )

    is_sim = LaunchConfiguration("is_sim")

    # ---------------- MoveIt Config ----------------
    moveit_config = (
        MoveItConfigsBuilder("simplearm", package_name=package_name)
        .robot_description(file_path=os.path.join(package_share, "urdf", "simplearm.urdf"))
        .robot_description_semantic(file_path="config/simplearm.srdf")
        .planning_pipelines(
            default_planning_pipeline="ompl",
            pipelines=["ompl"],
            load_all=False,
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .to_moveit_configs()
    )

    # Path to ros2_controllers.yaml (THIS WAS MISSING)
    ros2_controllers_path = os.path.join(
        package_share,
        "config",
        "ros2_controllers.yaml",
    )

    # ---------------- Robot State Publisher ----------------
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[moveit_config.robot_description],
    )

    # ---------------- ros2_control Node ----------------
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.robot_description,
            ros2_controllers_path,  # Correct file loaded
        ],
        output="screen",
    )

    # ---------------- Controller Spawners ----------------
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller"],
        output="screen",
    )

    # Delay spawners slightly so ros2_control fully starts
    delayed_spawners = TimerAction(
        period=3.0,
        actions=[
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
        ],
    )

    # ---------------- Move Group ----------------
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": is_sim},
        ],
    )

    # ---------------- RViz ----------------
    rviz_config = os.path.join(package_share, "rviz", "arm.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
    )

    return LaunchDescription(
        [
            is_sim_arg,
            robot_state_publisher,
            ros2_control_node,
            delayed_spawners,   #  Correct startup order
            move_group_node,
            rviz_node,
        ]
    )
