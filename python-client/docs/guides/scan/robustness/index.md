## Report

<aside>
⛔ Your model provides unrobust results:

- **Content** is volatile against **small typos.** As an illustration, see the following example ….
- Credit amount is volatile against small change. As an illustration, see the following example ….
</aside>

## Explanation

<aside>
👨‍🦰 Volatile results may be caused by overfitting. When your model learned noise (out of distribution), its results may vary against small changes

</aside>

## Action

<aside>
👉 We strongly recommend you **inspect** the volatile examples. This will enable you to find

- The right data augmentation strategy to make your model invariant to small changes
- The right feature engineering techniques to reduce the complexity of your model
- The regularization techniques to avoid overfitting
</aside>
