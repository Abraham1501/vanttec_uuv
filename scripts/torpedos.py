#!/usr/bin/env python
# -- coding: utf-8 --

import math
import time
import numpy as np
import rospy
from std_msgs.msg import Float32MultiArray, Int32, String
from geometry_msgs.msg import Pose, PoseStamped, Point
from vanttec_uuv.msg import GuidanceWaypoints
from nav_msgs.msg import Path

# Class Definition
class TorpedosMission:
    def __init__(self):
        self.ned_x = 0
        self.ned_y = 0
        self.ned_z = 0
        self.yaw = 0
        self.objects_list = []
        self.activated = True
        self.state = -1
        self.searchstate = -1
        self.distance = 0
        self.InitTime = rospy.Time.now().secs
        self.offset = .55 #camera to ins offset
        self.target_x = 0
        self.target_y = 0
        self.ned_alpha = 0
        self.choose_side = 'left'
        self.distance_away = 5
        self.waypoints = GuidanceWaypoints()
        self.uuv_path = Path()
        self.heading_threshold = 0.01
        self.depth_threshold = 0.
        #findimage works as a counter however with vision input once it identifies the target it should set this variable to True
        self.findimage = 0
        self.searchx = 0.0
        self.searchy = 0.0
        self.searchz = 0.0
        self.sweepstate = -1
        self.foundstate = -2
        self.enterwaypoint = 0.0
        self.staywaypoint = 0.0
        self.ylabel = 0.0
        self.bin = Point()
        self.bin.x = 0.0
        self.bin.y = 0.0
        self.bin.z = 0.0
        self.stopsearch = False
        self.timewait = 0.0
        self.cameraoffsetx = 0.0
        #self.cameraoffsety = 0.0
        self.cameraoffsetz = -0.1
        self.foundimage = {}
        #Waypoint test instead of perception node


        # ROS Subscribers
        rospy.Subscriber("/uuv_simulation/dynamic_model/pose", Pose, self.ins_pose_callback)
        rospy.Subscriber("buoy_2_pos_pub",Point,self.bin_callback)
        '''
        rospy.Subscriber("/usv_perception/yolo_zed/objects_detected", obj_detected_list, self.objs_callback)
        '''

        # ROS Publishers
        self.uuv_waypoints = rospy.Publisher("/uuv_guidance/guidance_controller/waypoints", GuidanceWaypoints, queue_size=10)
        self.uuv_path_pub = rospy.Publisher("/uuv_planning/motion_planning/desired_path", Path, queue_size=10)
        self.status_pub = rospy.Publisher("/mission/status", Int32, queue_size=10)
        self.test = rospy.Publisher("/mission/state", Int32, queue_size=10)

        #Waypoint test instead of perception node
        #This array shall be modified with zed inputs of distance 
        '''self.foundimage = {
                'X': 5.15,
                'Y': -0.1,
                'Z': 0.0
            }'''     
    def ins_pose_callback(self,pose):
        self.ned_x = pose.position.x
        self.ned_y = pose.position.y
        self.ned_z = pose.position.z
        self.yaw = pose.orientation.z      
    def bin_callback(self, msg):
        self.bin.x = msg.x + self.cameraoffsetx
        self.bin.y = msg.y #+ self.cameraoffsety
        self.bin.z = msg.z + self.cameraoffsetz
    def wait(self,nextmission):
        #Yolo neural network shall be included here
        self.waypoints.guidance_law = 0
        self.waypoints.heading_setpoint = 0
        timeduration = rospy.get_time()-self.timewait
        rospy.logwarn("Analyzing image with yolo neural network")
        if(self.bin.x!=0.0):
            self.foundimage = {
                'X': self.bin.z,
                'Y': self.bin.x,
                'Z': self.bin.y
                }
        if(timeduration >= 3):
            self.timewait = 0
            rospy.logwarn("Finish waiting")
            self.foundstate = nextmission      
        
    def sweep(self,nextmission):
        self.waypoints.guidance_law = 0
        if(self.bin.x!=0.0):
            self.stopsearch = True
        if(self.sweepstate == -1):
            if (self.waypoints.heading_setpoint <=  -math.pi/4):
                self.sweepstate = 2
            self.waypoints.heading_setpoint -= math.pi/400.0
            self.waypoints.waypoint_list_x = [0, 0]
            self.waypoints.waypoint_list_y = [0, 0]
            self.waypoints.waypoint_list_z = [0,0]
            self.desired(self.waypoints)
        elif(self.sweepstate == 2): 
            if (self.waypoints.heading_setpoint >= math.pi/4):
                self.sweepstate = 2.1
            else:
                self.waypoints.guidance_law = 0
                self.waypoints.heading_setpoint += math.pi/400.0
                self.waypoints.waypoint_list_x = [0 ,0]
                self.waypoints.waypoint_list_y = [0, 0]
                self.waypoints.waypoint_list_z = [0,0]
                self.desired(self.waypoints)
        elif(self.sweepstate == 2.1): 
            if (self.waypoints.heading_setpoint <= 0):
                self.waypoints.guidance_law = 0
                self.searchstate = nextmission
                self.searchx = self.ned_x + 3
                self.searchy = self.ned_y
                self.sweepstate = -1
                self.findimage += 1  
                self.desired(self.waypoints)
            else:
                self.waypoints.guidance_law = 0
                self.waypoints.heading_setpoint -= math.pi/400.0
                self.waypoints.waypoint_list_x = [0, 0]
                self.waypoints.waypoint_list_y = [0, 0]
                self.waypoints.waypoint_list_z = [0,0]
                self.desired(self.waypoints) 
    def sweeptorpedo(self,nextmission,heading1, heading2):
        self.waypoints.guidance_law = 0
        rospy.logwarn(self.sweepstate)
        if(self.sweepstate == -1):
            if (self.waypoints.heading_setpoint <= heading1):
                self.sweepstate = 2
            self.waypoints.heading_setpoint -= math.pi/400.0
            self.waypoints.waypoint_list_x = [0, 0]
            self.waypoints.waypoint_list_y = [0, 0]
            self.waypoints.waypoint_list_z = [0,0]
            self.desired(self.waypoints)
        elif(self.sweepstate == 2): 
            if (self.waypoints.heading_setpoint >= heading2):
                self.waypoints.guidance_law = 0
                self.foundstate = nextmission
                self.sweepstate = -1
                self.desired(self.waypoints)
            else:
                self.waypoints.guidance_law = 0
                self.waypoints.heading_setpoint += math.pi/400.0
                self.waypoints.waypoint_list_x = [0 ,0]
                self.waypoints.waypoint_list_y = [0, 0]
                self.waypoints.waypoint_list_z = [0,0]
                self.desired(self.waypoints)
           
    def search(self):
        #look subscriber of image distance
        if(self.stopsearch != True):
            rospy.logwarn("Searching image")
            self.timewait = rospy.get_time()
            if self.searchstate == -1:
                #sweep to find 
                self.sweep(0)
            elif self.searchstate ==0:
                self.waypoints.guidance_law = 1
                #move 2 meter
                _euc_distance = pow(pow(self.ned_x-self.searchx,2)+pow(self.ned_y-self.searchy,2),0.5)
                if(_euc_distance <0.35):
                    self.searchstate = -1
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.searchx]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.searchy]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   
        else:
            rospy.logwarn("Found image")
            if(self.foundstate == -2):
                if(self.bin.x!=0.0):
                    self.wait(-1)
            elif(self.foundstate == -1):
                self.centerx = self.ned_x + self.foundimage['X']-2
                self.centery = self.ned_y - self.foundimage['Y']
                self.rightx = self.ned_x + self.foundimage['X']-2
                self.righty = self.ned_y - self.foundimage['Y']+2
                self.leavewaypoint1x = self.ned_x+self.foundimage['X']-1
                self.leavewaypoint1y = self.ned_y-self.foundimage['Y']+1
                self.leavewaypoint2x = self.ned_x+self.foundimage['X']+2
                self.leavewaypoint2y = self.leavewaypoint1y 
                self.leavewaypoint3y = self.ned_y - self.foundimage['Y']
                self.leavewaypoint3x = self.leavewaypoint2x
                self.leavewaypoint4y = self.leavewaypoint3y
                self.leavewaypoint4x = self.leavewaypoint3x+2
                self.foundstate = 0
            #Orbit around
            elif(self.foundstate == 0):
                rospy.logwarn("center")
                self.waypoints.guidance_law = 1
                #orbit to center
                _euc_distance = pow(pow(self.ned_x-self.centerx,2)+pow(self.ned_y-self.centery,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 1
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.centerx]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.centery]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)
            elif(self.foundstate == 1):
                self.waypoints.guidance_law = 2
                rospy.logwarn("right")
               #orbit to right
                _euc_distance = pow(pow(self.ned_x-self.rightx,2)+pow(self.ned_y-self.righty,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 1.1
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.rightx]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.righty]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   
            elif(self.foundstate==1.1):
                rospy.logwarn("Sweep torpedo")
                heading2 = -math.pi/4+math.pi/8
                heading1 = -math.pi/4
                self.sweeptorpedo(1.2,heading1, heading2)
                self.timewait = rospy.get_time()
            elif(self.foundstate==1.2):
                self.wait(2)
            elif(self.foundstate == 2):
                rospy.logwarn("center")
                self.waypoints.guidance_law = 1
               #orbit to center
                _euc_distance = pow(pow(self.ned_x-self.centerx,2)+pow(self.ned_y-self.centery,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 2.11
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.centerx]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.centery]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)    
            elif(self.foundstate==2.11):
                rospy.logwarn("Sweep torpedo")
                heading2 = -math.pi/8
                heading1 = math.pi/8
                self.sweeptorpedo(2.12,heading1, heading2)
                self.timewait = rospy.get_time()
            elif(self.foundstate==2.12):
                self.wait(5)  
            #Leave
            elif(self.foundstate == 5):
                self.waypoints.guidance_law = 1
                rospy.logwarn("leave1")
               #move to leave waypoint1
                _euc_distance = pow(pow(self.ned_x-self.leavewaypoint1x,2)+pow(self.ned_y-self.leavewaypoint1y,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 6
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.leavewaypoint1x]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.leavewaypoint1y]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   
            elif(self.foundstate == 6):
                self.waypoints.guidance_law = 1
                rospy.logwarn("leave2")
               #move to leave waypoint2
                _euc_distance = pow(pow(self.ned_x-self.leavewaypoint2x,2)+pow(self.ned_y-self.leavewaypoint2y,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 7
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.leavewaypoint2x]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.leavewaypoint2y]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   
            elif(self.foundstate == 7):
                self.waypoints.guidance_law = 1
               #move to leave waypoint3
                rospy.logwarn("leave3")
                _euc_distance = pow(pow(self.ned_x-self.leavewaypoint3x,2)+pow(self.ned_y-self.leavewaypoint3y,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 8
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.leavewaypoint3x]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.leavewaypoint3y]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   
            elif(self.foundstate == 8):
                self.waypoints.guidance_law = 1
                rospy.logwarn("leave4")
               #move to leave waypoint4
                _euc_distance = pow(pow(self.ned_x-self.leavewaypoint4x,2)+pow(self.ned_y-self.leavewaypoint4y,2),0.5)
                if(_euc_distance <0.35):
                    self.foundstate = 9
                    self.waypoints.guidance_law = 0
                else:
                    self.waypoints.waypoint_list_x = [self.ned_x,self.leavewaypoint4x]
                    self.waypoints.waypoint_list_y = [self.ned_y,self.leavewaypoint4y]
                    self.waypoints.waypoint_list_z = [0,0]   
                    self.desired(self.waypoints)   


    def torpedosmission(self):
        self.waypoints.waypoint_list_length = 2
        self.waypoints.guidance_law = 1
        #self.waypoints.depth_setpoint = 4
        #depth_error = self.ned_z - self.waypoints.depth_setpoint
        
        if(self.state == -1):
            self.search()

    def desired(self, path):
        self.uuv_waypoints.publish(path)
        self.uuv_path.header.stamp = rospy.Time.now()
        self.uuv_path.header.frame_id = "world_ned"
        del self.uuv_path.poses[:]
        for index in range(path.waypoint_list_length):
            pose = PoseStamped()
            pose.header.stamp       = rospy.Time.now()
            pose.header.frame_id    = "world_ned"
            pose.pose.position.x    = path.waypoint_list_x[index]
            pose.pose.position.y    = path.waypoint_list_y[index]
            pose.pose.position.z    = path.waypoint_list_z[index]
            self.uuv_path.poses.append(pose)
        self.uuv_path_pub.publish(self.uuv_path)
    def results(self):
        rospy.logwarn("Inicial ned")
        rospy.logwarn(self.ned_x)
        rospy.logwarn(self.ned_y)
        rospy.logwarn(self.ned_z)     
        rospy.logwarn(self.yaw)         



    def activate(self):
        rate = rospy.Rate(20)
        while not rospy.is_shutdown() and self.activated:
            if(self.state != 6):
                rospy.loginfo("Torpedosmission is activated")
                self.torpedosmission()
            else:
                self.activated = False
            rate.sleep()
def main():
    rospy.init_node("torpedos_mission", anonymous=False)
    rate = rospy.Rate(20)
    torpedos_mission = TorpedosMission()
    last_detection = []
    while not rospy.is_shutdown() and torpedos_mission.activated:
        if(torpedos_mission.state != 9):
            rospy.loginfo("Torpedosmission is activated")
            torpedos_mission.torpedosmission()
        else:
            torpedos_mission.results()
        rate.sleep()
    rospy.spin()



if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:     
        pass