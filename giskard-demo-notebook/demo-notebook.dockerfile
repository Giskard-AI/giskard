FROM jupyter/base-notebook:python-3.7.6
RUN pip install pandas==1.3.5 scikit-learn==0.24.2 numpy==1.21.5 giskard==1.1.0 ipywidgets==7.6.5