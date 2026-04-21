# Standalone RealSense D435i camera launch for testing.
#
# Usage:
#   ros2 launch ur5e_d435i_bringup ur5e_camera.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur5e_d435i_share = FindPackageShare("ur5e_d435i_bringup")

    declared_arguments = [
        DeclareLaunchArgument(
            "camera_params_file",
            default_value=PathJoinSubstitution(
                [ur5e_d435i_share, "config", "d435i_params.yaml"]
            ),
            description="Path to RealSense camera parameters YAML.",
        ),
    ]

    realsense_node = Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        name="camera",
        namespace="",
        output="screen",
        parameters=[LaunchConfiguration("camera_params_file")],
    )

    return LaunchDescription(declared_arguments + [realsense_node])
