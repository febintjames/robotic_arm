import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    package_name = "simple_moveitmanual"
    package_share = get_package_share_directory(package_name)

    world_path = os.path.join(package_share, "worlds", "align_t_world.world")
    model_path = os.path.join(package_share, "models")
    robot_urdf = os.path.join(package_share, "urdf", "simplearm_gazebo.urdf")
    with open(robot_urdf, "r", encoding="utf-8") as urdf_file:
        robot_description_content = urdf_file.read().replace(
            "$(find simple_moveitmanual)", package_share
        )

    moveit_config = (
        MoveItConfigsBuilder("simplearm", package_name=package_name)
        .robot_description(file_path=os.path.join("urdf", "simplearm_gazebo.urdf"))
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

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={"world": world_path, "verbose": "true"}.items(),
    )

    set_gazebo_model_path = SetEnvironmentVariable(
        name="GAZEBO_MODEL_PATH",
        value=f"{model_path}:{os.environ.get('GAZEBO_MODEL_PATH', '')}",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {"robot_description": robot_description_content, "use_sim_time": True}
        ],
    )

    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            "simplearm",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.02",
        ],
        output="screen",
    )

    spawn_t_shape = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-entity",
            "t_shape",
            "-file",
            os.path.join(model_path, "t_shape", "model.sdf"),
            "-x",
            "0.58",
            "-y",
            "0.00",
            "-z",
            "0.03",
        ],
        output="screen",
    )

    spawn_highlight_zone = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-entity",
            "highlight_zone",
            "-file",
            os.path.join(model_path, "highlight_zone", "model.sdf"),
            "-x",
            "0.92",
            "-y",
            "0.0",
            "-z",
            "0.0",
        ],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "60",
        ],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "60",
        ],
        output="screen",
    )

    delayed_controller_spawners = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[
                TimerAction(
                    period=2.0,
                    actions=[joint_state_broadcaster_spawner, arm_controller_spawner],
                )
            ],
        )
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict(), {"use_sim_time": True}],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(package_share, "rviz", "arm.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            {"use_sim_time": True},
        ],
    )

    delayed_moveit_ui = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[move_group_node, rviz_node],
        )
    )

    return LaunchDescription(
        [
            set_gazebo_model_path,
            gazebo,
            robot_state_publisher,
            spawn_robot,
            spawn_t_shape,
            spawn_highlight_zone,
            delayed_controller_spawners,
            delayed_moveit_ui,
        ]
    )
