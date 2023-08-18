{% for group, issues in issues_by_group.items() %}

## {{loop.index}}. {{ group }} ({{ issues|length }} issues found)

{% for issue in issues %}

{% include "_issues/default.md" %}

---

{% endfor %}

{{ "=" * 100}}

{% endfor %}
