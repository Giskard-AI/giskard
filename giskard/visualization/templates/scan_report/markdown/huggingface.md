Hey Team!🤗✨ 

We’re thrilled to share some amazing evaluation results that’ll make your day!🎉📊

{% for view in groups -%}
<details>
<summary>👉{{ view.group.name }} issues ({{ view.issues|length }})</summary>

{% for issue in view.issues -%}

| Vulnerability | Level | Data slice | Metric | Transformation | Deviation | Description |
|---------------|-------|------------|--------|----------------|-----------|-------------|
| {{ view.group.name }} | {{ issue.level.value }} | {{ issue.slicing_fn if issue.slicing_fn else "—" }} | {% if "metric" in issue.meta %}{{ issue.meta.metric }} = {{ issue.meta.metric_value|format_metric }}{% else %} "—" {% endif %} | {{ issue.transformation_fn if issue.transformation_fn else "—" }} | {{ issue.meta["deviation"] if "deviation" in issue.meta else "—" }} | {{ issue.description }} |

<details>
<summary> 🔍✨Examples</summary>

{% if issue.examples(3)|length %}
{{ issue.examples(issue.meta.num_examples if "num_examples" in issue.meta else 3).to_markdown(
index=not issue.meta.hide_index if "hide_index" in issue.meta
else True)|replace("\\n", "<br>")|safe }}
{% endif %}
</details>

{% endfor %}

</details>
{% endfor -%}
<br />

### 💡 What's Next?

The Giskard community is always buzzing with ideas. 🐢🤔 What do you want to see next? Your feedback is our favorite fuel, so drop your thoughts in the community forum! 🗣️💬 Together, we're building something extraordinary.

### 🙌 Big Thanks!

We're grateful to have you on this adventure with us. 🚀🌟 Here's to more breakthroughs, laughter, and code magic! 🥂✨ Keep hugging that code and spreading the love! 💻 #Giskard #Huggingface #AISafety 🌈👏 Your enthusiasm, feedback, and contributions are what seek. 🌟 Keep being awesome!

