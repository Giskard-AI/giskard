{% for view in groups -%}
<details>
<summary>{{ view.group.name }} issues ({{ view.issues|length }})</summary>

| Vulnerability | Level | Data slice | Metric | Transformation | Deviation | Description |
|---------------|-------|------------|--------|----------------|-----------|-------------|
{% for issue in view.issues -%}
| {{ view.group.name }} | {{ issue.level.value }} | {{ issue.slicing_fn if issue.slicing_fn else "—" }} | {% if "metric" in issue.meta %}{{ issue.meta.metric }} = {{ issue.meta.metric_value|format_metric }}{% else %} "—" {% endif %} | {{ issue.transformation_fn if issue.transformation_fn else "—" }} | {{ issue.meta["deviation"] if "deviation" in issue.meta else "—" }} | {{ issue.description }} |
{% endfor %}

</details>
{% endfor -%}