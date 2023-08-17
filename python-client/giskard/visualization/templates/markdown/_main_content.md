{% for group, issues in issues_by_group.items() %}

## {{loop.index}}. {{ group }}

{% for issue in issues %}

{% include "_issues/default.md" %}

---

{% endfor %}

---

{% endfor %}
