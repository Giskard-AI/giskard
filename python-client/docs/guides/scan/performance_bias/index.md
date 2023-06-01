# Performance bias
## What happens?

<aside>
⛔ Your model contains biased data. For instance:

- **credit_amount > 5000** has an F1 score that is **4 times** smaller than the global F1
- **Gender == female** has an F1 score that is **5 times** smaller than the global F1

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/c320b18f-0be3-4d36-9e8f-3907a85e49ed/Untitled.png)

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/faaa96fc-9760-4d1f-971b-8d1cc9673f62/Untitled.png)

</aside>

## Why does this happen?

<aside>
👨‍🦰 Performance bias may happen for different **reasons**: 
    -  Not enough examples in the low-performing data slice in the training set
    -  Wrong labels in the training set in the low-performing data slice
    -  Drift between your training set and test set

</aside>

## How to correct this?

<aside>
👉 We strongly recommend you **inspect** the incorrect examples inside these data slices with debugging tools. This will enable you to find the right feature engineering strategies or data augmentation to avoid these biases.

- To debug the biased slices, click **here**
- For a full scan with more slice, click **here**
</aside>
