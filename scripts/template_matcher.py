import cv2
import numpy as np
from scipy.linalg import norm

"""
This code determines which of a set of template images matches
an input image the best using the SIFT algorithm
"""

class TemplateMatcher(object):

    def __init__ (self, images, min_match_count=5, good_thresh=0.7):
        cv2.namedWindow('template_img')
        cv2.namedWindow('result_img')
        self.signs = {} #maps keys to the template images
        self.kps = {} #maps keys to the keypoints of the template images
        self.descs = {} #maps keys to the descriptors of the template images
        if cv2.__version__=='3.1.0-dev' or cv2.__version__=='3.2.0': #this is gonna break in future versions so bad
            self.sift = cv2.xfeatures2d.SIFT_create()
        else:
            self.sift = cv2.SIFT() #initialize SIFT to be used for image matching

        # for potential tweaking
        self.min_match_count = min_match_count
        self.good_thresh = good_thresh #use for keypoint threshold
        self.ransac_thresh = 5.0

        for k, filename in images.iteritems():
            # load template sign images as grayscale
            self.signs[k] = cv2.imread(filename,0)
            # precompute keypoints and descriptors for the template sign
            self.kps[k], self.descs[k] = self.sift.detectAndCompute(self.signs[k],None)

    def predict(self, img):
        """
        Uses gather predictions to get visual diffs of the image to each template
        returns a dictionary, keys being signs, values being confidences
        """
        visual_diff = {}

        kp, des = self.sift.detectAndCompute(img,None)
        # get keypoints and descriptors from input image using SIFT
        #       store keypoints in variable kp and descriptors in des
        try:
            for k in self.signs.keys():
                #cycle trough template images (k) and get the image differences
                visual_diff[k] = self._compute_prediction(k, img, kp, des)
        except cv2.error as e:
            visual_diff[k] = None

        if None not in visual_diff.values():#convert from visual_diff to template_confidence
            template_confidence = {k: 0 for k in self.signs.keys()} #have default confidences
            confidence_sum = sum(visual_diff.values()) #sum up actual confidences
            for k in visual_diff:
                template_confidence[k] = 1-(visual_diff[k]/confidence_sum) #adjust to be on reasonable scale

        else:# if visual diff was not computed (bad crop, homography could not be computed)
            # set 0 confidence for all signs
            template_confidence = {k: 0 for k in self.signs.keys()}

        return template_confidence


    def _compute_prediction(self, k, img, kp, des):
        """
        Return comparison values between a template k and given image
        k: template image for comparison, img: scene image
        kp: keypoints from scene image,   des: descriptors from scene image
        """

        # find corresponding points in the input image and the template image
        #put keypoints from template image in template_pts
        #put corresponding keypoints from input image in img_pts
        good = []
        self.matcher = cv2.BFMatcher() #cv2's "brute force" matcher
        matches = self.matcher.knnMatch(self.descs[k],des,k=2)
        for m,n in matches:
            if m.distance < self.good_thresh*n.distance: #if first best keypoint is closer to the template than .7 * second best, it's good
                good.append(m)
        if len(good) > self.min_match_count:
            img_pts = np.float32([ kp[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
            template_pts = np.float32([ self.kps[k][m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        else:
            return None

        # Transform input image so that it matches the template image as well as possible
        M, mask = cv2.findHomography(img_pts, template_pts, cv2.RANSAC, self.ransac_thresh)
        img_T = cv2.warpPerspective(img, M, self.signs[k].shape[::-1])
        visual_diff = compare_images(img_T, self.signs[k])
        return visual_diff
# end of TemplateMatcher class

def compare_images(img1, img2):

    img1_norm = img1-np.mean(img1)/np.std(img1)
    img2_norm = img2-np.mean(img2)/np.std(img2)

    diff = np.subtract(img1_norm, img2_norm)
    dist = np.linalg.norm(diff)
    return dist
#option to watch and page through images being compared (for debugging)
    # cv2.imshow('template_img', img1)
    # cv2.imshow('result_img', img2)
    # cv2.waitKey(0)


if __name__ == '__main__':
#for sample images and scenes for testing
    images = {
        "left": '../images/leftturn_box_small.png',
        "right": '../images/rightturn_box_small.png',
        "uturn": '../images/uturn_box_small.png'
        }

    tm = TemplateMatcher(images)
    scenes = [
    "../images/uturn_scene.jpg",
    "../images/leftturn_scene.jpg",
    "../images/rightturn_scene.jpg"
    ]

    for filename in scenes:
        scene_img = cv2.imread(filename, 0)
        pred = tm.predict(scene_img)
        print filename.split('/')[-1]
        print pred
