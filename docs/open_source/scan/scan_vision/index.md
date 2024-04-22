# 📸 Vision model scan

**The giskard-vision extension is under development. For now, only landmark detection models are available.**


The Giskard python library provides an automatic scan functionality designed to automatically detect [potential vulnerabilities](https://docs.giskard.ai/en/latest/knowledge/key_vulnerabilities/index.html) affecting your ML model. It enables you to proactively identify and address key issues to ensure the reliability, fairness, and robustness of your Machine Learning models.


## Step 1: Wrap your dataset

To scan your model, start by **wrapping your dataset** with `DataLoaderBase`. Your class should implement `get_image` that loads an image as a `np.ndarray` and `get_marks` that returns landmark coordinates from a file.

> ### ⚠️ Warning
>
> It's highly recommended that you wrap your data **before preprocessing** so that you can easily interpret
> the scan results.

```python
from giskard-vision.landmark_detection.dataloaders.base
from giskard_vision.landmark_detection.demo import get_300W

dataloader = get_300W()


class DataLoaderLandmarkDetection(DataLoaderBase):
    """Your data loader for landmark detection
    """

    def get_image(self, idx: int) -> np.ndarray:
        """
        Gets an image for a specific index.

        Args:
            idx (int): Index of the data.

        Returns:
            np.ndarray: Image data for the given index.
        """
        return dataloader.get_image(idx)

    def get_marks(self, idx: int) -> np.ndarray:
        """
        Gets marks for a specific index.

        Args:
            idx (int): Index of the data.

        Returns:
            np.ndarray: Marks for the given index.
        """
        return dataloader.get_marks(idx)


giskard_dataset = DataLoaderLandmarkDetection()
```

## Step 2: Wrap your model

Next, **wrap your model** with `FaceLandmarksModelBase`. It should contain a method `predict_image` that returns landmarks as `np.ndarray`, as shown here:

```python
from giskard-vision.landmark_detection.models.base import FaceLandmarksModelBase
from giskard_vision.landmark_detection.models.wrappers import OpenCVWrapper

model = OpenCVWrapper()


class ModelLandmarkDetection(FaceLandmarksModelBase):
    """Wrapper class for facial landmarks detection.
    """

    def predict_image(self, image: np.ndarray) -> np.ndarray:
        """
        Predict facial landmarks for a given image.

        Args:
            image: The input image.

        Returns:
            np.ndarray: Predicted facial landmarks.

        """
        return model.predict_image(image)


giskard_model = ModelLandmarkDetection()
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
