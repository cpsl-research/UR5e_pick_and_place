# UR5e_pick_and_place
Includes code and documentation for setting up the UR5e arm, hand-eye calibration, marker detection, and inverse kinematics. This repo does not include commands to open or close the gripper, but the arm should be able to "hit" objects at locations designated by the ArUco marker. 

This guide is split into many parts:
- Initial Setup
- Running Simulations In RViz
- Maker Detection
- Calibration
- Inverse Kinematics

# Initial Setup 

UR5e arm can be controlled with the Polyscope gui or external control. This documentation will be focused on setting up external control. I followed this guide https://www.ritsumei.ac.jp/~kawamura/doc/ros2_ur.pdf (best guide out there), but I'ved added all of the commands below. The documentation for UR5e is also great, but can be very dense at times. 

Step 1: Create a ROS2 Workspace.

```
export COLCON_WS=~/workspace/ros_ws_foxy_ur_driver
mkdir -p $COLCON_WS/src
```

Step 2: Clone repo for the Universal Robotics Driver and install dependencies.

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

Step 3: Install MoveIt.   
Depending on the device used, MoveIt installation can be painful. For context, it took around ~4 hours to install this software on the Jerson Orin Nano (as listed in the documentation, use the flag `https://moveit.picknik.ai/main/doc/tutorials/getting_started/getting_started.html`)
Follow this guide: https://moveit.picknik.ai/main/doc/tutorials/getting_started/getting_started.html 

Step 4: UR5e Cap Installation  
Luckily, I've already done this on the CPSL robot! This is the installation for the driver on the robot that facilitates communication between the robot arm and the PC. Any installations for software on the UR5e should be done with a USB stick. 

Step 5: Create external program   
Make sure the robot is on local control mode (not remote control even though remote might seem like it makes more sense). Then, click program icon in the menu and select "URCaps" and "External Control" as a node in the program tree (see a picture of what this looks like on page 10 of the guide). 

Step 6: Start the robot  
Press the red circle in the bottom left corner and press start twice (robot should make a sound to release brakes).

Step 7: Start the robot driver  
Connect your PC to the robot with ethernet and check if you can ping the IP address. 
The command in the guide is outdated, use this instead:
```
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e launch_rviz:=true robot_ip:=192.168.56.101
```

Step 8: Start external control program  
Go back to the program tree and press play in the bottom right corner

Step 9: Program the robot!  
Any ROS2 nodes for movement should work, you can start with the joint trajectory controller. 
