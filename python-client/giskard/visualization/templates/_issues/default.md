### {{ issue.summary.domain }}

{% if issue.summary.short_description %}

##### {{issue.summary.short_description}}

{% endif %}

{% if issue.summary.metric %}

##### Metric: {{ issue.summary.metric }} {% if issue.summary.submetric %}({{ issue.summary.submetric }}){% endif %}

{% endif %}

{% if issue.summary.deviation %}

##### Deviation: {{ issue.summary.deviation }}

{% endif %}

{% if issue.summary.description %}
{{ issue.summary.description }}
{% endif %}

{% if issue.summary.examples|length %}

#### Examples

{{issue.summary.examples.to_markdown()}}

{% endif %}

{% if issue.summary.p_value and issue.summary.metric %}
The hypothesis that the {{ issue.summary.metric }} on the data slice was different with respect to the rest of the data was asserted with p-value = {{ issue.summary.p_value }}.
{% endif %}
