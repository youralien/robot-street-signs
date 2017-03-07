#!/usr/bin/env python

""" This is a script that walks through some of the basics of working with images
    with opencv in ROS. """

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import copy

class StreetSignRecognizer(object):
    """ This robot should recognize street signs """
    def __init__(self):
        """ Initialize the street sign reocgnizer """
        rospy.init_node('street_sign_recognizer')
        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()
        self.binary_image = None
        self.hsv_image = None              
        self.contour_image = None
        cv2.namedWindow('video_window')        
        cv2.setMouseCallback('video_window', self.process_mouse_event)
        cv2.namedWindow('hsv_video_window')
        cv2.setMouseCallback('hsv_video_window', self.process_mouse_event)
        cv2.namedWindow('threshold_image')
        cv2.namedWindow('contour_image')

        # Trackers
        self.hsv_lb = np.array([0, 168, 168]) # hsv lower bound
        cv2.createTrackbar('H lb', 'threshold_image', 0, 255, self.set_h_lb)
        cv2.createTrackbar('S lb', 'threshold_image', 0, 255, self.set_s_lb)
        cv2.createTrackbar('V lb', 'threshold_image', 0, 255, self.set_v_lb)
        self.hsv_ub = np.array([98, 255, 255]) # hsv upper bound
        cv2.createTrackbar('H ub', 'threshold_image', 0, 255, self.set_h_ub)
        cv2.createTrackbar('S ub', 'threshold_image', 0, 255, self.set_s_ub)
        cv2.createTrackbar('V ub', 'threshold_image', 0, 255, self.set_v_ub)


        # Initialize for bounding box
        self.left_top = (0,0)
        self.right_bottom = (0,0)

        rospy.Subscriber("/camera/image_raw", Image, self.process_image)

    # Functions for trackers to set HSV bounds
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

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """

        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        self.hsv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2HSV)      
        self.binary_image = cv2.inRange(self.hsv_image,(self.hsv_lb[0], self.hsv_lb[1], self.hsv_lb[2]),(self.hsv_ub[0], self.hsv_ub[1], self.hsv_ub[2]))
        # Blur for better contours
        self.binary_image = cv2.GaussianBlur(self.binary_image, (3,3), 0)
        
        # Set bounding box corner points
        left_top, right_bottom = self.sign_bounding_box()
        left, top = left_top
        right, bottom = right_bottom

        # crop bounding box region of interest
        cropped_sign = self.cv_image[top:bottom, left:right]

        # draw bounding box rectangle
        cv2.rectangle(self.cv_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)
        cv2.rectangle(self.hsv_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)

    def process_mouse_event(self, event, x,y,flags,param):
        """ Process mouse events so that you can see the color values associated
            with a particular pixel in the camera images """
        image_info_window = 255*np.ones((500,500,3))
        cv2.putText(image_info_window,
                    'Color (b=%d,g=%d,r=%d)' % (self.cv_image[y,x,0], self.cv_image[y,x,1], self.cv_image[y,x,2]),
                    (5,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,0))
        cv2.imshow('image_info', image_info_window)
        cv2.waitKey(5)

    def sign_bounding_box(self):
        """
        Returns
        -------
        (left_top, right_bottom) where left_top and right_bottom are tuples of (x_pixel, y_pixel)
            defining topleft and bottomright corners of the bounding box
        """
        self.contour_image = copy.deepcopy(self.binary_image)
        contours, hierarchy = cv2.findContours(self.contour_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE) 
        if contours:
            cnt = contours[-1]
            if cnt.any():
                vertices = cv2.boundingRect(cnt)
                print vertices
                x, y, w, h = vertices
                # only draw box if large enough
                if w > 10 and h > 10:
                    self.left_top = (x, y)
                    self.right_bottom = (x+w, y+h)
            return self.left_top, self.right_bottom





    def run(self):
        """ The main run loop"""
        r = rospy.Rate(10)
        while not rospy.is_shutdown():
            if not self.cv_image is None:
                print "here"
                # creates a window and displays the image for X milliseconds
                cv2.imshow('video_window', self.cv_image)
                if self.binary_image is not None:
                    cv2.imshow('threshold_image', self.binary_image)
                if self.hsv_image is not None:
                    cv2.imshow('hsv_video_window', self.hsv_image)
                if self.contour_image is not None:
                    cv2.imshow('contour_image', self.contour_image)
                cv2.waitKey(5)
            r.sleep()

if __name__ == '__main__':
    node = StreetSignRecognizer()
    node.run()
