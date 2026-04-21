#!/usr/bin/env python3
"""
Hand-eye calibration for UR5e + D435i using ArUco markers.

Eye-in-hand calibration: camera mounted on robot end-effector,
ArUco marker fixed in the workspace.

Usage:
  1. Place an ArUco marker (DICT_5X5_100, ID 0) on a flat surface
     visible to the camera.
  2. Launch the full system:
     ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py
  3. Launch calibration:
     ros2 launch ur5e_d435i_bringup ur5e_calibration.launch.py
  4. Move robot to different poses where the marker is visible.
     Press ENTER in the terminal to capture each sample.
  5. After collecting enough samples, the script outputs the
     calibrated camera-to-end-effector transform.
"""

import threading

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from scipy.spatial.transform import Rotation

import tf2_ros
from aruco_opencv_msgs.msg import ArucoDetection


class HandEyeCalibrationNode(Node):
    def __init__(self):
        super().__init__("hand_eye_calibration")

        self.declare_parameter("marker_id", 0)
        self.declare_parameter("num_samples", 15)
        self.declare_parameter("robot_base_frame", "base_link")
        self.declare_parameter("robot_ee_frame", "tool0")
        self.declare_parameter("camera_frame", "camera_color_optical_frame")

        self.marker_id = self.get_parameter("marker_id").value
        self.num_samples = self.get_parameter("num_samples").value
        self.base_frame = self.get_parameter("robot_base_frame").value
        self.ee_frame = self.get_parameter("robot_ee_frame").value
        self.camera_frame = self.get_parameter("camera_frame").value

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.latest_marker_pose = None
        self.cb_group = ReentrantCallbackGroup()
        self.aruco_sub = self.create_subscription(
            ArucoDetection,
            "/aruco_detections",
            self.aruco_callback,
            10,
            callback_group=self.cb_group,
        )

        self.R_gripper2base_samples = []
        self.t_gripper2base_samples = []
        self.R_target2cam_samples = []
        self.t_target2cam_samples = []
        self.sample_count = 0

        self.get_logger().info(
            f"Hand-eye calibration: collecting {self.num_samples} samples. "
            f"Marker ID: {self.marker_id}"
        )
        self.get_logger().info(
            "Move the robot so the ArUco marker is visible, then press ENTER."
        )

    def aruco_callback(self, msg):
        for i, mid in enumerate(msg.marker_ids):
            if mid == self.marker_id:
                self.latest_marker_pose = msg.markers[i].pose

    def capture_sample(self):
        try:
            tf_ee = self.tf_buffer.lookup_transform(
                self.base_frame, self.ee_frame, rclpy.time.Time()
            )
        except tf2_ros.TransformException as e:
            self.get_logger().error(f"TF lookup failed: {e}")
            return False

        if self.latest_marker_pose is None:
            self.get_logger().warn("No ArUco marker detected. Skipping.")
            return False

        t = tf_ee.transform.translation
        q = tf_ee.transform.rotation
        R_g2b = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
        t_g2b = np.array([t.x, t.y, t.z]).reshape(3, 1)

        mp = self.latest_marker_pose
        R_t2c = Rotation.from_quat(
            [mp.orientation.x, mp.orientation.y, mp.orientation.z, mp.orientation.w]
        ).as_matrix()
        t_t2c = np.array(
            [mp.position.x, mp.position.y, mp.position.z]
        ).reshape(3, 1)

        self.R_gripper2base_samples.append(R_g2b)
        self.t_gripper2base_samples.append(t_g2b)
        self.R_target2cam_samples.append(R_t2c)
        self.t_target2cam_samples.append(t_t2c)

        self.sample_count += 1
        self.get_logger().info(f"Sample {self.sample_count}/{self.num_samples} captured.")
        self.latest_marker_pose = None
        return True

    def run_calibration(self):
        self.get_logger().info("Running hand-eye calibration...")

        if len(self.R_gripper2base_samples) < 3:
            self.get_logger().error(
                f"Need >= 3 samples, got {len(self.R_gripper2base_samples)}."
            )
            return

        R_g2b = [cv2.Rodrigues(R)[0] for R in self.R_gripper2base_samples]
        t_g2b = self.t_gripper2base_samples
        R_t2c = [cv2.Rodrigues(R)[0] for R in self.R_target2cam_samples]
        t_t2c = self.t_target2cam_samples

        methods = {
            "TSAI": cv2.CALIB_HAND_EYE_TSAI,
            "PARK": cv2.CALIB_HAND_EYE_PARK,
            "HORAUD": cv2.CALIB_HAND_EYE_HORAUD,
            "ANDREFF": cv2.CALIB_HAND_EYE_ANDREFF,
            "DANIILIDIS": cv2.CALIB_HAND_EYE_DANIILIDIS,
        }

        results = {}
        for name, method in methods.items():
            try:
                R_cam2ee, t_cam2ee = cv2.calibrateHandEye(
                    R_g2b, t_g2b, R_t2c, t_t2c, method=method,
                )
                results[name] = (R_cam2ee, t_cam2ee)
            except cv2.error as e:
                self.get_logger().warn(f"Method {name} failed: {e}")

        if not results:
            self.get_logger().error("All calibration methods failed!")
            return

        self.get_logger().info("=" * 60)
        self.get_logger().info("HAND-EYE CALIBRATION RESULTS")
        self.get_logger().info("=" * 60)

        for name, (R, t) in results.items():
            rpy = Rotation.from_matrix(R).as_euler("xyz")
            quat = Rotation.from_matrix(R).as_quat()
            self.get_logger().info(f"--- {name} ---")
            self.get_logger().info(
                f"  xyz: [{t[0,0]:.6f}, {t[1,0]:.6f}, {t[2,0]:.6f}]"
            )
            self.get_logger().info(
                f"  rpy: [{rpy[0]:.6f}, {rpy[1]:.6f}, {rpy[2]:.6f}]"
            )
            self.get_logger().info(
                f"  quat: [{quat[0]:.6f}, {quat[1]:.6f}, {quat[2]:.6f}, {quat[3]:.6f}]"
            )

        primary = "TSAI" if "TSAI" in results else list(results.keys())[0]
        R_best, t_best = results[primary]
        rpy_best = Rotation.from_matrix(R_best).as_euler("xyz")
        quat_best = Rotation.from_matrix(R_best).as_quat()

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"RECOMMENDED ({primary}):")
        self.get_logger().info("Update ur5e_d435i.urdf.xacro camera offsets:")
        self.get_logger().info(f'  camera_offset_x="{t_best[0,0]:.6f}"')
        self.get_logger().info(f'  camera_offset_y="{t_best[1,0]:.6f}"')
        self.get_logger().info(f'  camera_offset_z="{t_best[2,0]:.6f}"')
        self.get_logger().info(f'  camera_offset_roll="{rpy_best[0]:.6f}"')
        self.get_logger().info(f'  camera_offset_pitch="{rpy_best[1]:.6f}"')
        self.get_logger().info(f'  camera_offset_yaw="{rpy_best[2]:.6f}"')
        self.get_logger().info("")
        self.get_logger().info("Quick test with static_transform_publisher:")
        self.get_logger().info(
            f"ros2 run tf2_ros static_transform_publisher "
            f"--x {t_best[0,0]:.6f} --y {t_best[1,0]:.6f} --z {t_best[2,0]:.6f} "
            f"--qx {quat_best[0]:.6f} --qy {quat_best[1]:.6f} "
            f"--qz {quat_best[2]:.6f} --qw {quat_best[3]:.6f} "
            f"--frame-id tool0 --child-frame-id camera_link"
        )
        self.get_logger().info("=" * 60)

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = HandEyeCalibrationNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    def input_thread():
        while rclpy.ok() and node.sample_count < node.num_samples:
            try:
                input()
                node.capture_sample()
            except EOFError:
                break
        if node.sample_count >= node.num_samples:
            node.run_calibration()

    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == "__main__":
    main()
