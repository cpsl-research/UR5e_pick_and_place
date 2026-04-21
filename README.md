# UR5e_pick_and_place
Includes code and documentation for setting up the UR5e arm, hand-eye calibration, marker detection, and inverse kinematics. This repo does not include commands to open or close the gripper, but the arm should be able to "hit" objects at locations designated by the ArUco marker. 

This guide is split into many parts:
- Initial Setup
- Running Simulations In RViz
- Maker Detection For Hand-Eye Calibration
- Hand-Eye Calibration (Easy Hand-Eye)
- Hand-Eye Calibration Configs (Manual)
- Inverse Kinematics

# Initial Setup 

UR5e arm can be controlled with the Polyscope gui or external control. This documentation will be focused on setting up external control. I followed this guide https://www.ritsumei.ac.jp/~kawamura/doc/ros2_ur.pdf (best guide out there), but I'ved added all of the commands below. The documentation for UR5e is also great, but can be very dense at times. 

*Step 1: Create a ROS2 Workspace.*

```
export COLCON_WS=~/workspace/ros_ws_foxy_ur_driver
mkdir -p $COLCON_WS/src
```

*Step 2: Clone repo for the Universal Robotics Driver and install dependencies.*

```
cd $COLCON_WS
git clone
https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver.git
src/Universal_Robots_ROS2_Driver
vcs import src --skip-existing --input
src/Universal_Robots_ROS2_Driver/Universal_Robots_ROS2_Driver.repos
rosdep install --ignore-src --from-paths src -y -r
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

*Step 3: Install MoveIt.*
Depending on the device used, MoveIt installation can be painful. For context, it took around ~4 hours to install this software on the Jerson Orin Nano (as listed in the documentation, use the flag `MAKEFLAGS="-j4 -l1" colcon build --executor sequential`)
Follow this guide: https://moveit.picknik.ai/main/doc/tutorials/getting_started/getting_started.html 

*Step 4: UR5e Cap Installation*
Luckily, I've already done this on the CPSL robot! This is the installation for the driver on the robot that facilitates communication between the robot arm and the PC. Any installations for software on the UR5e should be done with a USB stick. 

*Step 5: Create external program*
Make sure the robot is on local control mode (not remote control even though remote might seem like it makes more sense). Then, click program icon in the menu and select "URCaps" and "External Control" as a node in the program tree (see a picture of what this looks like on page 10 of the guide). 

*Step 6: Start the robot*
Press the red circle in the bottom left corner and press start twice (robot should make a sound to release brakes).

*Step 7: Start the robot driver* 
Connect your PC to the robot with ethernet and check if you can ping the IP address. 
The command in the guide is outdated, use this instead:
```
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e launch_rviz:=true robot_ip:=192.168.56.101
```

*Step 8: Start external control program*
Go back to the program tree and press play in the bottom right corner

*Step 9: Program the robot!*
Any ROS2 nodes for movement should work, you can start with the joint trajectory controller. 

# Running Simulations In RViz  
Always best to simulate before running any programs on the robot!  
```
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e launch_rviz:=true robot_ip:=192.168.56.101 use_fake_hardware:=true
```
Now you can run any nodes and observe the robot's trajectory and plan on RViz.  

# Marker Detection
This marker detection script in `realsense_pub` uses the Intel RealSense ROS library to subscribe to topics containing camera's intrinsic matrix and frame data. This detection script will also draw the detected corners onto an image of the marker. The marker detection, *most importantly*, publishes a transform between `camera_color_optical_frame` and a frame called `marker`. Note this marker frame might need to be changed tos specific ID #s if different ArUco markers are used at once. Also I've accounted for ArUco markers 5 cm by 5 cm, but this might need to be updated. 
To test the marker detection script in isolation, first launch Intel RealSense:  
```
ros2 launch realsense2_camera rs_launch.py     pointcloud.enable:=true     align_depth.enable:=true     depth_module.depth_profile:=424x240x15     rgb_camera.color_profile:=424x240x15     pointcloud.pointcloud_qos:=SENSOR_DATA

```
These parameters also help with visualizing the point cloud in RViz.   

Then, run the marker detection node:  
```
ros2 run realsense_pub publisher_node
```
# Hand-Eye Calibration Easy Hand-Eye Library
Easy Hand-Eye Library is a very standard library for computing transforms between camera and gripper or base. I'd prefer this over manual calibration (measuring offet of gripper from camera) because it is much more precise, and easier to recompute transforms if the camera moves. To preface, I was not able to have everything working with this library, but I've included everything I've learned about it. This is the documentation I used: https://github.com/marcoesposito1988/easy_handeye2. The documentation is not very detailed or clear - the most useful part of it is this example launch file: https://github.com/IFL-CAMP/easy_handeye/blob/master/docs/example_launch/ur5e_realsense_calibration.launch (shows example input arguments for UR5e and Intel RealSense camera). 

To use this library, I'd recommend creating a launch file that runs these nodes (also using marker detector node in this repo):  

```
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e launch_rviz:=true robot_ip:=192.168.56.101
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e
ros2 launch realsense2_camera rs_launch.py     pointcloud.enable:=true     align_depth.enable:=true     depth_module.depth_profile:=424x240x15     rgb_camera.color_profile:=424x240x15     pointcloud.pointcloud_qos:=SENSOR_DATA
ros2 run realsense_pub publisher_node
ros2 launch easy_handeye2 calibrate.launch.py   name:=handeye1   calibration_type:=eye_in_hand   tracking_base_frame:=camera_color_optical_frame   tracking_marker_frame:=marker   robot_base_frame:=base_link   robot_effector_frame:=tool0
```
With these commands, you should be able to start taking samples and compute transforms!

The library will automatically save the transform to a file - to publish the transform to the transform tree, use this command (note: handeye1 is the name I chose for the transform):  
```
ros2 launch easy_handeye2 publish.launch.py name:=handeye1
```

# Manual Hand-Eye Calibration

In the `ur5e_d435i_bringup` directory, the transform is manually defined (measured transform and rotation between camera and gripper) in a urdf file called `ur5e_d435i.urdf.xacro`. By running these commands, it should be possible to publish the camera to gripper transform to the transform tree. 

```
ros2 launch ur5e_d435i_bringup ur5e_bringup.launch.py
```
Then press play in the Polyscope gui to start the external program.
```
rviz2 -d ~/ur5_ws/src/ur5e_d435i_bringup/config/ur5e_d435i.rviz
```
For more information on this directory, refer to the original git repo: https://github.com/cpsl-research/UR5_robot_arm_repo#.

# Inverse Kinematics 
This repo includes an inverse kinematics node (in the folder `ur5e_ik`) that reads the transform tree to move the robot arm to the ArUco marker. 
To run this script, make sure that there is a correct transform between the frames `camera_link` and `tool0` and that marker position is being detected and published (using the marker detector node in this repo). Also press play to start the external program.

Run this command.
```
ros2 run ur5e_movement ur5e_movement
```
