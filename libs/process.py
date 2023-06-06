﻿import cv2
import numpy as np
import math
import utils

class ImageColorSimplifier:
    """Change image to painting image.
    
    Parameters
    ----------
    img : np.ndarray
        Image that want to work

    Attributes
    ----------
    original_img : np.array
        Input original image
    painting : np.array
        Color clustered image (Applied K-Means Algorithm)
    colors : np.array
        Clustered color data list
    """

    def __init__(self, img):
        self.original_img = img
        self.painting = np.array([])
        self.colors = np.array([])
        return 
    
    def run(self, 
            # kmeans clustering
            k = 16, 
            attempts = 1,
            # expand size
            is_upscale = False,
            size = 3,
            # blurring
            enables_blurring = False,
            div = 8, 
            base_radius = 10, 
            base_sigma_color = 20,
            median_value = 5,
            step = 0):
        """Cluster image color with k-means algorithm.

        Parameters
        ----------
        k : int, optional (default: 16)
            Number of color clustered
        attempts : int, optional (default: 1)
            How many iterate try to k-means clustering
        is_upscale : bool, optional (default: False)
            Expand size of image
        size : int, optional (default: 3)
            Size that want to expand image.
            If you want to guess the proper size, set size value under 1.
        enables_blurring : bool, optional (default: False)
            Blurring image
        div : int, optional (default: 8)
            Reducing numbers of color on image
        base_radius : int, optional (default: 10)
            bilateralFilter Parameter
        base_sigma_color : int, optional (default: 20)
            bilateralFilter Parameter
        median_value : int, optional (default: 5)
            medianBlur Parameter
        step : int, optional (default: 0)
            Blurring intensity by step size

        Returns
        ----------
        self.painting : np.ndarray
            Color clustered image
        """

        target_image = self.original_img.copy()
        
        if enables_blurring:
            target_image = self.__blur_image(target_image,
                                        div = div,
                                        base_radius = base_radius,
                                        base_sigma_color = base_sigma_color,
                                        median_value = median_value,
                                        step = step)

        if is_upscale:
            target_image = self.__expand_image(target_image, size = size)

        self.painting, sse = self.__cluster_color(target_image, 
                                                            number_of_color = k, 
                                                            attempts = attempts)
        return self.painting
    
    def __blur_image(self, 
                image,
                div,
                base_radius, 
                base_sigma_color,
                median_value,
                step):
        """Image blurring

        Parameters
        ----------
        image : np.ndarray
            Input image
        div : int
            Reducing numbers of color on image
        base_radius : int
            bilateralFilter Parameter
        base_sigma_color : int
            bilateralFilter Parameter
        median_value : int
            medianBlur Parameter
        step : int
            Blurring intensity by step size

        Returns
        -------
        blurred_image : np.ndarray
            blurred Image
        """

        height, width = image.shape[:2]
        step = utils.get_value_in_range(step, 0, 5)
        
        # calcuate weights for blurring
        img_size_weight = int(math.sqrt(width * height)) // 100
        radius_weight = min(int(img_size_weight * 1.5), 40) + step * 2
        sigma_color_weight = min(int(img_size_weight * 2.5), 90) + step * 4

        radius = base_radius + radius_weight
        sigma_color = base_sigma_color + sigma_color_weight
        
        # blur image
        blured_image = cv2.bilateralFilter(image, radius, sigma_color, 60)
        blured_image = cv2.medianBlur(blured_image, median_value)
        blured_image = utils.division_blur(blured_image, div)

        return blured_image
    
    def __cluster_color(self, image, number_of_color, attempts):
        """Cluster image color with k-means algorithm.

        Parameters
        ----------
        image : np.ndarray
            Input image
        number_of_color : int
            Number of color clustered
        attempts : int
            How many iterate try to k-means clustering

        Returns
        ----------
        color_clustered_image : np.ndarray
            Color clustered image
        sse : float
            Sum of squared error
        """
        
        # transform color data to use k-means algorithm
        # need to trnasform into two-dimensional array
        # [[B, G, R], [B, G, R] ... , [B, G, R]]
        height, width = image.shape[:2]
        training_data_samples = image.reshape(height * width, 3).astype(np.float32)
        
        
        # sse : Sum of squared error
        # labels : Array about label, show like 0, 1
        # centers : Cluster centroid array
        sse, labels, centers = cv2.kmeans(
                                        training_data_samples,  # Align training data, data type = np.float32
                                        number_of_color,        # number of cluster
                                        None,                   # Sort the cluster numbers for each sample
                                        
                                        # TERM_CRITERIA_EPS : End iteration when a certain accuracy is reached
                                        # TERM_CRITERIA_MAX_ITER : End iteration after a certain number of iterations
                                        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
                                                    100000, # max_iter : Max number of iterations
                                                    0.0001), # epsilon : Specific Accuracy Required
                                        attempts = attempts,  # Number of iterations to run using different initial centroids
                                        
                                        # flags : To set the Initial Centroids
                                        # cv2.KMEANS_RANDOM_CENTERS : Random
                                        # cv2.KMEANS_PP_CENTERS : K-Means++ Algorithm
                                        # cv2.KMEANS_USE_INITIAL_LABELS : User selection
                                        flags = cv2.KMEANS_PP_CENTERS)
        
        centers = np.uint8(centers)
        res = centers[labels.flatten()]
        self.colors = centers
        # for returns
        sse = round(sse ** 0.5 // 10, 2)
        color_clustered_image = res.reshape((image.shape))
        return color_clustered_image, sse
   
    def __expand_image(self, image, size):
        """Expand image size

        Parameters
        ----------
        image : np.ndarray
            Input image
        size : int
            Size that want to expand image.
            If you want to guess the proper size, set size value under 1.

        Returns
        ----------
        output : np.ndarray
            Expanded image
        """
        STANDARD_SIZE_OF_IMAGE = 5000
        if size < 1:
            max_image_length = max(image.shape[1], image.shape[0])
            size = (STANDARD_SIZE_OF_IMAGE // max_image_length) + 1

        output = cv2.resize(image, None, fx = size, fy = size, interpolation = cv2.INTER_LINEAR)
        return output
    
    

class ColorSectorLineDrawer:
    """Draw line on image with color boundary
    
    Parameters
    ----------
    img : np.ndarray
        Input painting image

    Attributes
    ----------
    web : np.array
        Remain only lines from image color boundary, white background
    """
    def __init__(self, img):
        self.IMAGE_MAX_BINARY = 255
        self.painting = img
        self.web = np.zeros(self.painting.shape) + self.IMAGE_MAX_BINARY
        return 
    
    def run(self, outline = True):
        """Draw line on image

        Parameters
        ----------
        outline : bool, optional (default: True)
            Select that want to draw outline on web image

        Returns
        ----------
        self.web : np.ndarray
            Gray scale that line drawn on white background image
        """
        self.__draw_line(self.painting)
        if outline:
            self.__draw_outline()
        return self.web
    
    def __draw_line(self, painting):
        """Draw line with color boundary from painting image

        Parameters
        ----------
        painting : np.ndarray
            Input painting image

        Returns
        ----------
        self.web : np.ndarray
            Gray scale image that line drawn
        """
        for y, before_row in enumerate(painting[:-1]):
            next_row = self.painting[y+1]
            # 다음 row와 비교했을 때, 색상이 다른 index 추출
            compare_row = np.array( np.where((before_row == next_row) == False))
            for x in np.unique(compare_row[0]):
                # Convert to Black
                self.web[y][x] = np.array([0, 0, 0])
                            
        width = self.web.shape[1] # get Image Width

        for _, x in enumerate(range(width - 1)):
            # 다음 column과 비교했을 때, 색상이 다른 index 추출
            compare_col = np.array( np.where((self.painting[:,x] == self.painting[:,x+1]) == False))
            for y in np.unique(compare_col[0]):
                # Convert to Black
                self.web[y][x] = np.array([0, 0, 0])
        
        # threshold를 이용하여, 2차원 Image로 변환
        _, self.web = cv2.threshold(self.web, 199, self.IMAGE_MAX_BINARY, cv2.THRESH_BINARY)
        
        return self.web
    
    def __draw_outline(self):
        """Draw outline on image
        """
        self.web[0:2], self.web[-3:-1], self.web[:,0:2], self.web[:,-3:-1] = 0, 0, 0, 0
        return

    

if __name__ == "__main__":
    # How to Use?
    img = cv2.imread("lala.jpg")
    painting = ImageColorSimplifier(img)
    painting_image = painting.run(
                                k = 8,
                                is_upscale = False,
                                size = 2,
                                enables_blurring = True,)
    


    # drawing = ColorSectorLineDrawer(painting_image)
    # line_drawn_image = drawing.run(outline = True)
    
    

    cv2.imwrite('lala_after.jpg', painting_image)
    cv2.waitKey(0)