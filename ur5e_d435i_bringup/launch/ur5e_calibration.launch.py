# ArUco hand-eye calibration launch.
#
# Prerequisites: ur5e_bringup.launch.py must already be running
# (provides robot TF and camera image topics).
#
# Usage:
#   ros2 launch ur5e_d435i_bringup ur5e_calibration.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur5e_d435i_share = FindPackageShare("ur5e_d435i_bringup")

    declared_arguments = [
        DeclareLaunchArgument(
            "marker_size",
            default_value="0.05",
            description="ArUco marker side length in meters.",
        ),
        DeclareLaunchArgument(
            "marker_id",
            default_value="0",
            description="ArUco marker ID to detect.",
        ),
        DeclareLaunchArgument(
            "num_samples",
            default_value="15",
            description="Number of calibration samples to collect.",
        ),
    ]

    aruco_node = Node(
        package="aruco_opencv",
        executable="aruco_tracker_autostart",
        name="aruco_tracker",
        output="screen",
        parameters=[
            PathJoinSubstitution(
                [ur5e_d435i_share, "config", "aruco_params.yaml"]
            ),
            {"marker_size": LaunchConfiguration("marker_size")},
        ],
        remappings=[
            ("image", "/camera/color/image_raw"),
            ("camera_info", "/camera/color/camera_info"),
        ],
    )

    calibration_node = Node(
        package="ur5e_d435i_bringup",
        executable="hand_eye_calibration.py",
        name="hand_eye_calibration",
        output="screen",
        parameters=[
            {
                "marker_id": LaunchConfiguration("marker_id"),
                "num_samples": LaunchConfiguration("num_samples"),
                "robot_base_frame": "base_link",
                "robot_ee_frame": "tool0",
                "camera_frame": "camera_color_optical_frame",
            },
        ],
    )

    return LaunchDescription(declared_arguments + [aruco_node, calibration_node])
