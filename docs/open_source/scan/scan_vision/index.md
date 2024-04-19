# 📸 Vision model scan

**Feature under development**

The Giskard python library provides an automatic scan functionality designed to automatically detect [potential vulnerabilities](https://docs.giskard.ai/en/latest/knowledge/key_vulnerabilities/index.html) affecting your ML model. It enables you to proactively identify and address key issues to ensure the reliability, fairness, and robustness of your Machine Learning models.

The giskard-vision extension is under development. For now, only landmark detection models are available.

## Step 1: Wrap your dataset

To scan your model, start by **wrapping your dataset** with `DataLoaderBase`. Your class should implement `load_marks_from_file` that returns landmark coordinates from a file and `load_image_from_file` that loads an image an a `np.ndarray`.

> ### ⚠️ Warning
>
> It's highly recommended that you wrap your data **before preprocessing** so that you can easily interpret
> the scan results.

```python
from giskard-vision.landmark_detection.dataloaders.base

class DataLoader300W(DataLoaderBase):
    """Data loader for the 300W dataset. Ref: https://ibug.doc.ic.ac.uk/resources/300-W/

    Args:
        dir_path (Union[str, Path]): Path to the directory containing images and landmarks.
        **kwargs: Additional keyword arguments passed to the base class.

    Attributes:
        image_suffix (str): Suffix for image files.
        marks_suffix (str): Suffix for landmark files.
        n_landmarks (int): Number of landmarks in the dataset.
        n_dimensions (int): Number of dimensions for each landmark.

    Raises:
        ValueError: Raised for various errors during initialization.

    """

    image_suffix: str = ".png"
    marks_suffix: str = ".pts"
    n_landmarks: int = 68
    n_dimensions: int = 2

    def __init__(self, dir_path: Union[str, Path], **kwargs) -> None:
        """
        Initializes the DataLoader300W.

        Args:
            dir_path (Union[str, Path]): Path to the directory containing images and landmarks.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(
            dir_path,
            dir_path,
            name="300W",
            meta={
                "authors": "Imperial College London",
                "year": 2013,
                "n_landmarks": self.n_landmarks,
                "n_dimensions": self.n_dimensions,
                "preprocessed": False,
                "preprocessing_time": 0.0,
            },
            **kwargs,
        )

    @classmethod
    def load_marks_from_file(cls, mark_file: Path):
        """
        Loads landmark coordinates from a file.

        Args:
            mark_file (Path): Path to the file containing landmark coordinates.

        Returns:
            np.ndarray: Array containing landmark coordinates.
        """
        text = mark_file.read_text()
        return np.array([xy.split(" ") for xy in text.split("\n")[3:-2]], dtype=float)

    @classmethod
    def load_image_from_file(cls, image_file: Path) -> np.ndarray:
        """
        Loads images as np.array using OpenCV.

        Args:
            image_file (Path): Path to the image file.

        Returns:
            np.ndarray: Numpy array representation of the image.
        """
        return cv2.imread(str(image_file))

giskard_dataset = DataLoader300W("examples/landmark_detection/datasets/300W/")
```

## Step 2: Wrap your model

Next, **wrap your model** with `FaceLandmarksModelBase`. It should contain a method `predict_image` that returns landmarks as `np.ndarray`, as shown here:

```python
from giskard-vision.landmark_detection.models.base import FaceLandmarksModelBase

class OpenCVWrapper(FaceLandmarksModelBase):
    """Wrapper class for facial landmarks detection using OpenCV.

    This class uses the Haarcascades algorithm for face detection and the LBF model for facial landmark detection.

    Args:
        FaceLandmarksModelBase (_type_): Base class for facial landmarks models.

    Attributes:
        detector: Instance of the Haarcascades face detection classifier.
        landmark_detector: Instance of the facial landmark detector using the LBF model.

    Sources:
        https://medium.com/analytics-vidhya/facial-landmarks-and-face-detection-in-python-with-opencv-73979391f30e

    """

    def __init__(self):
        """
        Initialize the OpenCVWrapper.

        This constructor sets up the Haarcascades face detection classifier and loads the LBF model for facial landmark detection.

        """
        super().__init__(n_landmarks=68, n_dimensions=2, name="OpenCV")

        # save face detection algorithm's url in haarcascade_url variable
        haarcascade_url = (
            "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_alt2.xml"
        )

        # save face detection algorithm's name as haarcascade
        haarcascade = "haarcascade_frontalface_alt2.xml"

        # chech if file is in working directory
        if haarcascade not in os.listdir(os.curdir):
            # download file from url and save locally as haarcascade_frontalface_alt2.xml, < 1MB
            urlreq.urlretrieve(haarcascade_url, haarcascade)

        # create an instance of the Face Detection Cascade Classifier
        self.detector = cv2.CascadeClassifier(haarcascade)

        # save facial landmark detection model's url in LBFmodel_url variable
        LBFmodel_url = "https://github.com/kurnianggoro/GSOC2017/raw/master/data/lbfmodel.yaml"

        # save facial landmark detection model's name as LBFmodel
        LBFmodel = "lbfmodel.yaml"

        # check if file is in working directory
        if LBFmodel not in os.listdir(os.curdir):
            # download picture from url and save locally as lbfmodel.yaml, < 54MB
            urlreq.urlretrieve(LBFmodel_url, LBFmodel)

        # create an instance of the Facial landmark Detector with the model
        self.landmark_detector = cv2.face.createFacemarkLBF()
        self.landmark_detector.loadModel(LBFmodel)

    def predict_image(self, image):
        """
        Predict facial landmarks for a given image using the wrapped OpenCV face landmarks model.

        Args:
            image: The input image.

        Returns:
            np.ndarray: Predicted facial landmarks.

        """
        # Detect faces using the haarcascade classifier on the image
        faces = self.detector.detectMultiScale(image)
        # Detect landmarks on "image_gray"
        _, landmarks = self.landmark_detector.fit(image, faces)
        # temporary taking only one face
        return np.array(landmarks)[0, 0]  # only one image is passed


giskard_model = OpenCVWrapper()
```

## Step 3: Scan your model

Now you can scan your model and display your scan report:

```python
scan_results = giskard-vision.scan(giskard_model, giskard_dataset)
display(scan_results)  # in your notebook
```

![Vision scan results](../../../assets/scan_vision.png)

If you are not working in a notebook or want to save the results for later, you can save them to an HTML file like this:

```python
scan_results.to_html("model_scan_results.html")
```
