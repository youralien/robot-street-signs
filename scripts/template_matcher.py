import cv2
import numpy as np

"""
This code determines which of a set of template images matches
an input image the best using the SIFT algorithm
"""

class TemplateMatcher(object):

    def __init__ (self, images, min_match_count=10, good_thresh=0.7):
        self.signs = {} #maps keys to the template images
        self.kps = {} #maps keys to the keypoints of the template images
        self.descs = {} #maps keys to the descriptors of the template images
        if cv2.__version__=='3.1.0-dev':
            self.sift = cv2.xfeatures2d.SIFT_create()
        else:
            self.sift = cv2.SIFT() #initialize SIFT to be used for image matching

        # for potential tweaking
        self.min_match_count = min_match_count
        self.good_thresh = good_thresh #use for keypoint threshold
        self.ransac_thresh = 5

        for k, filename in images.iteritems():
            # load template sign images as grayscale
            self.signs[k] = cv2.imread(filename,0)

            # precompute keypoints and descriptors for the template sign 
            self.kps[k], self.descs[k] = self.sift.detectAndCompute(self.signs[k],None)

    def predict(self, img, e=.00001):
        """
        Uses gather predictions to get visual diffs of the image to each template
        returns a dictionary, keys being signs, values being confidences

        e: small number to deal with EOF in division
        """
        visual_diff = {}
        template_confidence = {}

        # store keypoints in variable kp and descriptors in des
        kp, des = self.sift.detectAndCompute(img,None)

        if img:
            for k in self.signs.keys():
                #cycle trough templage images (k) and get the image differences
                visual_diff[k] = self._compute_prediction(k, img, kp, des)

        if visual_diff:
            # convert difference between images (from visual_diff)
            # to confidence values (stored in template_confidence)
            # by inversing the difference
            for k in visual_diff:
                template_confidence[k] = 1/(visual_diff[k]+e)

            # normalize
            total = sum(template_confidence.values)
            for k in template_confidence:
                template_confidence[k] /= total

        else: # if visual diff was not computed (bad crop, homography could not be computed)
            # set 0 confidence for all signs
            template_confidence = {k: 0 for k in self.signs.keys()}

        return template_confidence


    def _compute_prediction(self, k, img, kp, des):
        """
        Return comparison values between a template k and given image
        k: template image for comparison, img: scene image
        kp: keypoints from scene image,   des: descriptors from scene image
        """

        # find matches by using BFmatcher 
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(self.descs[k], des, k=2)

        # store good matches according to ratio test
        good = [m for (m, n) in matches if (m.distance < 0.75 * n.distance)]

        # put corresponding keypoints from input image in img_pts
        img_pts = np.asarray([kp[match.trainIdx].pt for match in good])
        # put keypoints from template image in template_pts
        template_pts = np.asarray([self.kps[k][match.queryIdx].pt for match in good])

        # Transform input image so that it matches the template image as well as possible
        M, mask = cv2.findHomography(img_pts, template_pts, cv2.RANSAC, self.ransac_thresh)
        img_T = cv2.warpPerspective(img, M, self.signs[k].shape[::-1])

        visual_diff = compare_images(img_T, self.signs[k])
        return visual_diff

def compare_images(img1, img2, e=.00001):
    """
    Return difference between two normalized images

    e: small number to deal with EOF in division
    """

    # normalize images
    img1 = (img1 - np.mean(img1))/(np.std(img1)+e)
    img2 = (img2 - np.mean(img2))/(np.std(img2)+e)

    return np.mean(abs(img1-img2))

if __name__ == '__main__':
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