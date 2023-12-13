{% for view in groups -%}
<details>
<summary>👉{{ view.group.name }} issues ({{ view.issues|length }})</summary>

{% for issue in view.issues -%}

| Vulnerability | Level | Data slice | Metric | Transformation | Deviation |
|---------------|-------|------------|--------|----------------|-----------|
| {{ view.group.name }} | <span style="color:{% if issue.level.value == "major" %} red {% else %} orange {% endif %} "> {{ issue.level.value }} {% if issue.level.value == "major" %} 🔴 {% else %} 🟡 {% endif %} </span> | {{ issue.slicing_fn if issue.slicing_fn else "—" }} | {% if "metric" in issue.meta %}{{ issue.meta.metric }} = {{ issue.meta.metric_value|format_metric }}{% else %} "—" {% endif %} | {{ issue.transformation_fn if issue.transformation_fn else "—" }} | {{ issue.meta["deviation"] if "deviation" in issue.meta else "—" }} |

<details>
<summary> 🔍✨Examples</summary>
{{ issue.description }}

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
