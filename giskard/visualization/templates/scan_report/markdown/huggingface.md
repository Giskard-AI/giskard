{% for view in groups -%}

<details>
<summary>👉{{ view.group.name }} issues ({{ view.issues|length }})</summary>

{% for issue in view.issues -%}
{{ issue.description }}

| Level | Data slice | Metric | Deviation |
|-------|------------|--------|-----------|
| <span style="color:{% if issue.level.value == "major" %} red {% else %} orange {% endif %} "> {{ issue.level.value }} {% if issue.level.value == "major" %} 🔴 {% else %} 🟡 {% endif %} </span> | {{ issue.slicing_fn if issue.slicing_fn else "—" }} | {% if "metric" in issue.meta %}{{ issue.meta.metric }} = {{ issue.meta.metric_value|format_metric }}{% else %} "—" {% endif %} | {{ issue.meta["deviation"] if "deviation" in issue.meta else "—" }} |

{% if issue.taxonomy %}
<h4 class="font-bold text-sm mt-4">Taxonomy</h4>
{% for tag in issue.taxonomy %}
<span class="inline-block bg-blue-300/25 text-zinc-100 px-2 py-0.5 rounded-sm text-sm mr-1 my-2">
    {{ tag }}
</span>
{% endfor %}
<br />
{% endif %}

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
<!-- line breaker -->
{% endfor -%}
<br />

