# TurtleBot Autonomous Navigation with Landmark Detection

A full-stack autonomous indoor navigation system on TurtleBot, integrating
SLAM, image-based landmark detection, multi-floor map management, and
voice/text command interfaces -- built on ROS.

![ROS Noetic](https://img.shields.io/badge/ROS-Noetic-blue)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2020.04-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## Demo

<!-- Add your map screenshot and video here once uploaded -->
![Map demo](docs/media/map_demo.png)

## What it does

- Real-time landmark detection using an OpenCV + ROS image pipeline,
  mapping unique visual features to world coordinates for navigation
- Multi-floor map support: separate 2D occupancy maps per floor
  (downstairs, floor2, upstairs) with automated switching and
  persistent localization via AMCL
- Voice + text command interface: say or type a landmark name and the
  robot autonomously navigates there via move_base
- YAML-based landmark storage, decoupling perception from navigation
- ~95% system accuracy demonstrated in controlled indoor testing

## Repository Structure

## Dependencies

| Package | Purpose | Install |
|---|---|---|
| ROS Noetic + navigation | move_base, AMCL, costmap_2d | `sudo apt install ros-noetic-navigation` |
| turtlebot3, turtlebot3_msgs, turtlebot3_simulations | Robot driver + Gazebo models | `sudo apt install ros-noetic-turtlebot3*` |
| OpenCV (cv_bridge) | Landmark detection pipeline | `sudo apt install ros-noetic-cv-bridge ros-noetic-vision-opencv` |
| slam_toolbox | SLAM mapping | `sudo apt install ros-noetic-slam-toolbox` |
| rf2o_laser_odometry | Laser-based odometry | build from source, see docs |

## Installation

```bash
mkdir -p ~/catkin_ws/src && cd ~/catkin_ws/src
git clone https://github.com/<your-username>/turtlebot-landmark-navigation.git
sudo apt install ros-noetic-navigation ros-noetic-turtlebot3 \
                  ros-noetic-turtlebot3-msgs ros-noetic-turtlebot3-simulations \
                  ros-noetic-cv-bridge ros-noetic-vision-opencv ros-noetic-slam-toolbox
cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

## Usage

**Mapping session (simulation, Habitat-Sim):**
```bash
roscore
roslaunch habitat_ros oreo.launch scene:=00861
roslaunch habitat_ros my_slam.launch
# brings up rf2o odometry, slam_toolbox, move_base, explore_lite, YOLO, controller_node, RViz
```

**Mapping session (real robot):**
```bash
roslaunch rf2o_laser_odometry rf2o_laser_odometry.launch
roslaunch slam_toolbox online_sync.launch
```

**Save the generated map:**
```bash
rosrun map_server map_saver -f ~/catkin_ws/maps/my_map
```

**Navigation session (map + landmarks already exist):**
```bash
roscore
roslaunch habitat_ros oreo.launch
roslaunch rf2o_laser_odometry rf2o_laser_odometry.launch
roslaunch image_logger locate.launch floor:=upstairs
# or with typed commands instead of voice:
roslaunch image_logger locate.launch floor:=upstairs command_mode:=typed
```

**Object detection:**
```bash
roslaunch image_logger object_detection.launch
rosrun image_logger yolo_run.py
```

## Note

Core launch files, maps, and captured perception data are included.
Additional scripts (YOLO detection runner, voice/text landmark locator)
live on a separate development machine and will be added in a follow-up commit.

## Future Work

- Replace hand-tuned landmark features with a learned detector (YOLO), fully merged in
- Automatic floor-transition detection for multi-floor switching
- Multi-robot exploration with shared landmark maps

## License

MIT -- see [LICENSE](./LICENSE).
