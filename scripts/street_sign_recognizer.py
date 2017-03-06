#!/usr/bin/env python

""" This is a script that walks through some of the basics of working with images
    with opencv in ROS. """

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class StreetSignRecognizer(object):
    """ This robot should recognize street signs """


    def __init__(self):
        """ Initialize the street sign reocgnizer """
        rospy.init_node('street_sign_recognizer')
        self.cv_image = None                        # the latest image from the camera
        self.hsv_image = None
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV
        cv2.namedWindow('video_window')
        rospy.Subscriber("/camera/image_raw", Image, self.process_image)
        cv2.namedWindow('threshold_image')
        self.hsv_lb = np.array([0, 0, 0]) # hsv lower bound
        cv2.createTrackbar('H lb', 'threshold_image', 0, 255, self.set_h_lb)
        cv2.createTrackbar('S lb', 'threshold_image', 0, 255, self.set_s_lb)
        cv2.createTrackbar('V lb', 'threshold_image', 0, 255, self.set_v_lb)
        self.hsv_ub = np.array([255, 255, 255]) # hsv upper bound
        cv2.createTrackbar('H ub', 'threshold_image', 0, 255, self.set_h_ub)
        cv2.createTrackbar('S ub', 'threshold_image', 0, 255, self.set_s_ub)
        cv2.createTrackbar('V ub', 'threshold_image', 0, 255, self.set_v_ub)


    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        self.hsv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2HSV)
        self.binary_image = cv2.inRange(self.hsv_image, 
            (25,176,77), 
            (158,255,236))




        left_top, right_bottom = self.sign_bounding_box()
        left, top = left_top
        right, bottom = right_bottom

        # crop bounding box region of interest
        self.cropped_sign = self.cv_image[top:bottom, left:right]

        # draw bounding box rectangle
        cv2.rectangle(self.cv_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)

    def sign_bounding_box(self):
        """
        Returns
        -------
        (left_top, right_bottom) where left_top and right_bottom are tuples of (x_pixel, y_pixel)
            defining topleft and bottomright corners of the bounding box
        """
        #calculate contour and generate bounding rectangle
        ret, thresh = cv2.threshold(self.binary_image,127,255,cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, 1, 2)
        cnts = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
        cnt = cnts[0]
        


        x,y,w,h = cv2.boundingRect(cnt)
        print x,y,(x+w),(y+h)
        left_top = (x, y)
        right_bottom = (x+w, y+h)
        return left_top, right_bottom



    #callbacks for sliders
    def set_h_lb(self, val):
        """ set hue lower bound """
        self.hsv_lb[0] = val

    def set_s_lb(self, val):
        """ set saturation lower bound """
        self.hsv_lb[1] = val

    def set_v_lb(self, val):
        """ set value lower bound """
        self.hsv_lb[2] = val

    def set_h_ub(self, val):
        """ set hue upper bound """
        self.hsv_ub[0] = val

    def set_s_ub(self, val):
        """ set saturation upper bound """
        self.hsv_ub[1] = val

    def set_v_ub(self, val):
        """ set value upper bound """
        self.hsv_ub[2] = val

    def run(self):
        """ The main run loop"""
        r = rospy.Rate(10)
        while not rospy.is_shutdown():

            if not self.cv_image is None:
                cv2.imshow('video_window', self.cv_image)
                cv2.imshow('video_window2', self.cropped_sign)
                cv2.waitKey(5)
            r.sleep()

if __name__ == '__main__':
    node = StreetSignRecognizer()
    node.run()
