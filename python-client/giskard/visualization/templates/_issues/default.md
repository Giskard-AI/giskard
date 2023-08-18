#### {{ issue.visualization_attributes.domain }}

{% if issue.visualization_attributes.description_hidden %}

##### {{issue.visualization_attributes.description_hidden}}

{% endif %}

{% if issue.visualization_attributes.metric %}

##### Metric: {{ issue.visualization_attributes.metric }} {% if issue.visualization_attributes.submetric %}({{ issue.visualization_attributes.submetric }}){% endif %}

{% endif %}

{% if issue.visualization_attributes.deviation %}

##### Deviation: {{ issue.visualization_attributes.deviation }}

{% endif %}

{{ issue.visualization_attributes.description }}

{% if issue.visualization_attributes.examples|length %}

#### Examples

{{issue.visualization_attributes.examples.to_markdown()}}

{% endif %}

{% if issue.visualization_attributes.p_value and issue.visualization_attributes.metric %}
The hypothesis that the {{ issue.visualization_attributes.metric }} on the data slice was different with respect to the rest of the data was asserted with p-value = {{ issue.visualization_attributes.p_value }}.
{% endif %}
