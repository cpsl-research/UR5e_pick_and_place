# ur5e_d435i_bringup

ROS2 Jazzy bringup package for a **UR5e** robot with a wrist-mounted **Intel RealSense D435i** camera, **MoveIt** motion planning, point cloud visualization in RViz, and ArUco-based hand-eye calibration.

## Hardware Setup

- **Robot**: Universal Robots UR5e (IP: `192.168.56.101`)
- **Host**: NVIDIA Jetson (Tegra), IP: `192.168.56.1` on interface `enP2p1s0`
- **Camera**: Intel RealSense D435i, connected via USB 3.2
- **Wrist Mount**: PickNik UR5 RealSense camera adapter (rev2)
- **Network**: Direct Ethernet connection between Jetson and UR5e control box

## Package Structure

```
ur5e_d435i_bringup/
  CMakeLists.txt
  package.xml
  README.md
  meshes/
    picknik_ur5_realsense_camera_adapter_rev2.STL   # Wrist mount CAD (mm scale)
  urdf/
    ur5e_d435i.urdf.xacro           # Extended UR5e URDF + wrist mount + D435i
    d435i_wrist_mount.urdf.xacro    # Macro: tool0 -> wrist_mount_link -> camera_link
  launch/
    ur5e_bringup.launch.py          # Full system: driver + camera + MoveIt + RViz
    ur5e_rsp.launch.py              # Custom robot_state_publisher (uses extended URDF)
    ur5e_camera.launch.py           # Standalone camera launch
    ur5e_calibration.launch.py      # ArUco hand-eye calibration launch
  config/
    d435i_params.yaml               # RealSense camera parameters
    aruco_params.yaml               # ArUco detection parameters (DICT_7X7_100)
    ur5e_d435i.rviz                 # RViz config: MoveIt + PointCloud2 + TF
  scripts/
    hand_eye_calibration.py         # Interactive hand-eye calibration (OpenCV)
    test_aruco_detection.py         # Quick ArUco detection test (standalone)
```

## Prerequisites

### 1. ROS2 Jazzy Workspace

The following must already be built in `~/ur5e_manipulator/ur5_ws/`:
- Universal_Robots_ROS2_Driver (jazzy branch)
- Universal_Robots_ROS2_Description
- MoveIt2
- ros2_control / ros2_controllers

### 2. Install ROS2 Packages

```bash
sudo apt install -y \
  ros-jazzy-realsense2-camera \
  ros-jazzy-realsense2-camera-msgs \
  ros-jazzy-realsense2-description \
  ros-jazzy-aruco-opencv \
  ros-jazzy-aruco-opencv-msgs
```

### 3. Build librealsense from Source (Required on Jetson)

The apt-installed librealsense does not work on Jetson Tegra kernels. You must build from source with the RSUSB backend:

```bash
sudo apt install -y git cmake libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev libglfw3-dev

cd ~/ur5e_manipulator
git clone --depth 1 --branch v2.56.4 https://github.com/IntelRealSense/librealsense.git
cd librealsense
mkdir build && cd build
cmake .. -DFORCE_RSUSB_BACKEND=ON -DCMAKE_BUILD_TYPE=Release -DBUILD_EXAMPLES=false -DBUILD_GRAPHICAL_EXAMPLES=false
make -j$(nproc)
sudo make install

# Install udev rules
sudo cp ../config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

# Replace the ROS-packaged librealsense with the source-built one
sudo mv /opt/ros/jazzy/lib/aarch64-linux-gnu/librealsense2.so.2.56.4 /opt/ros/jazzy/lib/aarch64-linux-gnu/librealsense2.so.2.56.4.bak
sudo ln -sf /usr/local/lib/librealsense2.so.2.56.4 /opt/ros/jazzy/lib/aarch64-linux-gnu/librealsense2.so.2.56.4
sudo ldconfig

# Verify camera is detected
rs-enumerate-devices
```

### 4. Network Configuration

Set the static IP for the Jetson Ethernet interface (persists across reboots):

```bash
sudo nmcli con mod enP2p1s0 ipv4.addresses 192.168.56.1/24 ipv4.method manual
sudo nmcli con up enP2p1s0
ping 192.168.56.101  # Should respond
```

### 5. Build This Package

```bash
cd ~/ur5e_manipulator/ur5_ws
ln -sf ~/ur5e_manipulator/ur5e_d435i_bringup src/ur5e_d435i_bringup
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon build --packages-select ur5e_d435i_bringup --symlink-install
```

## Usage

Requires **two terminals** — one for the nodes, one for RViz.

### Terminal 1: Launch Nodes (Robot + Camera + MoveIt)

```bash
source ~/ur5e_manipulator/ur5_ws/install/setup.bash
ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py launch_rviz:=false
```

Then on the **UR5e teach pendant**:
1. Create/open a program with **URCaps > External Control** node
2. Verify host IP: `192.168.56.1`, port: `50002`
3. Press **Play from beginning**

The terminal should show `"Robot connected to reverse interface"`.

### Terminal 2: Launch RViz

```bash
source ~/ur5e_manipulator/ur5_ws/install/setup.bash
rviz2 -d ~/ur5e_manipulator/ur5_ws/src/ur5e_d435i_bringup/config/ur5e_d435i.rviz
```

RViz opens with the robot model, point cloud, MoveIt MotionPlanning controls, and TF frames.

### Launch Options (Terminal 1)

| Argument | Default | Description |
|----------|---------|-------------|
| `robot_ip` | `192.168.56.101` | UR5e IP address |
| `ur_type` | `ur5e` | Robot type |
| `use_mock_hardware` | `false` | Use simulated robot (no real hardware) |
| `launch_rviz` | `false` | Open RViz from launch (use Terminal 2 instead) |
| `launch_camera` | `true` | Start RealSense D435i |
| `launch_moveit` | `true` | Start MoveIt motion planning |

Examples:

```bash
# Mock hardware (no real robot or camera needed)
ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py use_mock_hardware:=true launch_camera:=false launch_rviz:=false

# Real robot without camera
ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py launch_camera:=false launch_rviz:=false
```

### Standalone Camera Test

```bash
ros2 launch ur5e_d435i_bringup ur5e_camera.launch.py
```

### ArUco Detection Test (No ROS required)

```bash
python3 ~/ur5e_manipulator/ur5e_d435i_bringup/scripts/test_aruco_detection.py
```

Opens a window showing the camera feed with detected ArUco markers (DICT_7X7_100) highlighted. Press `q` to quit.

### Hand-Eye Calibration

Refines the camera-to-tool transform using ArUco markers:

```bash
# First ensure the full system is running, then in another terminal:
ros2 launch ur5e_d435i_bringup ur5e_calibration.launch.py
```

1. Place an ArUco marker (DICT_7X7_100, ID 0, 50mm) on a flat surface in the workspace
2. Move the robot to 15 different poses where the marker is visible
3. Press ENTER after each pose to capture a sample
4. The script outputs calibrated camera offset values

Update the calibrated values in `urdf/d435i_wrist_mount.urdf.xacro` (camera_offset parameters) and relaunch.

## URDF / TF Tree

```
world -> base_link -> ... -> wrist_3_link -> flange -> tool0
                                                         |
                                                    wrist_mount_link
                                                         |
                                                    camera_link
                                                    /    |    \
                                          (published by realsense2_camera node)
                                     camera_depth_frame  camera_color_frame  ...
                                          |                    |
                                camera_depth_optical_frame  camera_color_optical_frame
```

The URDF defines `tool0 -> wrist_mount_link -> camera_link`. The RealSense node publishes TF from `camera_link` to the optical frames.

### Camera Transform (tool0 -> camera_link)

Current calibrated values:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `camera_offset_x` | `0.0` | Lateral offset (m) |
| `camera_offset_y` | `-0.09` | Side offset from tool0 (m) |
| `camera_offset_z` | `0.0` | Height offset (m) |
| `camera_offset_roll` | `0.0` | Roll (rad) |
| `camera_offset_pitch` | `-80 deg` | Tilt from horizontal (-pi/2 + 10 deg) |
| `camera_offset_yaw` | `90 deg` | Rotation around tool axis (pi/2) |

## RViz Displays

The included `ur5e_d435i.rviz` config provides:

- **MotionPlanning**: MoveIt interactive planning (Plan & Execute)
- **PointCloud2**: D435i depth/color point cloud (`/camera/depth/color/points`)
- **TF**: Key frames (tool0, camera_link, wrist_mount_link)
- **Image** (disabled): Color camera feed (`/camera/color/image_raw`)

## Troubleshooting

### Camera not detected
- Check USB: `lsusb | grep Intel`
- Verify librealsense: `rs-enumerate-devices`
- If `bad optional access` error: rebuild librealsense from source (see Prerequisites)

### Robot won't connect
- Check network: `ping 192.168.56.101`
- If no route: `sudo nmcli con up enP2p1s0`
- Verify External Control program is running on teach pendant

### MoveIt plugin not found in RViz
- Source the workspace before opening RViz:
  ```bash
  source ~/ur5e_manipulator/ur5_ws/install/setup.bash
  rviz2 -d ~/ur5e_manipulator/ur5e_d435i_bringup/config/ur5e_d435i.rviz
  ```

### Point cloud misaligned
- Run hand-eye calibration to refine the camera transform
- Or manually adjust `camera_offset_*` values in `urdf/d435i_wrist_mount.urdf.xacro`

### Controller manager overrun warnings
- Normal on Jetson (no RT kernel). Does not affect functionality.
