# Full bringup: UR5e driver + D435i camera + MoveIt + RViz with point cloud
#
# Usage:
#   ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py
#   ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py use_mock_hardware:=true launch_camera:=false

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur5e_d435i_share = FindPackageShare("ur5e_d435i_bringup")
    ur_robot_driver_share = FindPackageShare("ur_robot_driver")
    ur_moveit_config_share = FindPackageShare("ur_moveit_config")

    declared_arguments = [
        DeclareLaunchArgument(
            "robot_ip",
            default_value="192.168.56.101",
            description="IP address of the UR5e robot.",
        ),
        DeclareLaunchArgument(
            "ur_type",
            default_value="ur5e",
            description="Type of UR robot.",
        ),
        DeclareLaunchArgument(
            "use_mock_hardware",
            default_value="false",
            description="Start robot with mock hardware.",
        ),
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="false",
            description="Launch RViz with point cloud and MoveIt displays.",
        ),
        DeclareLaunchArgument(
            "launch_camera",
            default_value="true",
            description="Launch the RealSense D435i camera node.",
        ),
        DeclareLaunchArgument(
            "launch_moveit",
            default_value="true",
            description="Launch MoveIt motion planning.",
        ),
    ]

    # 1. UR5e Driver with custom URDF (wrist mount + camera)
    ur_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [ur_robot_driver_share, "launch", "ur_control.launch.py"]
            )
        ),
        launch_arguments={
            "ur_type": LaunchConfiguration("ur_type"),
            "robot_ip": LaunchConfiguration("robot_ip"),
            "use_mock_hardware": LaunchConfiguration("use_mock_hardware"),
            "description_launchfile": PathJoinSubstitution(
                [ur5e_d435i_share, "launch", "ur5e_rsp.launch.py"]
            ),
            "launch_rviz": "false",
        }.items(),
    )

    # 2. RealSense D435i Camera
    realsense_node = Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        name="camera",
        namespace="",
        output="screen",
        parameters=[
            PathJoinSubstitution(
                [ur5e_d435i_share, "config", "d435i_params.yaml"]
            )
        ],
        condition=IfCondition(LaunchConfiguration("launch_camera")),
    )

    # 3. MoveIt (waits for /robot_description published by RSP above)
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [ur_moveit_config_share, "launch", "ur_moveit.launch.py"]
            )
        ),
        launch_arguments={
            "ur_type": LaunchConfiguration("ur_type"),
            "launch_rviz": "false",
            "launch_servo": "false",
        }.items(),
        condition=IfCondition(LaunchConfiguration("launch_moveit")),
    )

    # 4. RViz with PointCloud2 + MoveIt MotionPlanning displays
    rviz_config = PathJoinSubstitution(
        [ur5e_d435i_share, "config", "ur5e_d435i.rviz"]
    )

    import os
    rviz_node = ExecuteProcess(
        cmd=["rviz2", "-d", rviz_config],
        output="screen",
        additional_env={"DISPLAY": os.environ.get("DISPLAY", ":1")},
        condition=IfCondition(LaunchConfiguration("launch_rviz")),
    )

    return LaunchDescription(
        declared_arguments
        + [
            ur_control_launch,
            realsense_node,
            moveit_launch,
            rviz_node,
        ]
    )
