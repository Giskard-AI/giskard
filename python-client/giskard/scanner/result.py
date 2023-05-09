from collections import defaultdict
import pandas as pd


class ScanResult:
    def __init__(self, issues):
        self.issues = issues

    def has_issues(self):
        return len(self.issues) > 0

    def __repr__(self):
        if not self.has_issues():
            return "<PerformanceScanResult (no issues)>"

        return f"<PerformanceScanResult ({len(self.issues)} issue{'s' if len(self.issues) > 1 else ''})>"

    def _ipython_display_(self):
        from IPython.core.display import display_html

        html = self._repr_html_()
        display_html(html, raw=True)

    def _repr_html_(self):
        from jinja2 import Environment, PackageLoader, select_autoescape
        from html import escape

        env = Environment(
            loader=PackageLoader("giskard.scanner", "templates"),
            autoescape=select_autoescape(),
        )
        tpl = env.get_template("scan_results.html")

        issues_by_group = defaultdict(list)
        for issue in self.issues:
            issues_by_group[issue.group].append(issue)

        html = tpl.render(
            issues=self.issues,
            issues_by_group=issues_by_group,
            num_major_issues={
                group: len([i for i in issues if i.is_major]) for group, issues in issues_by_group.items()
            },
            num_medium_issues={
                group: len([i for i in issues if not i.is_major]) for group, issues in issues_by_group.items()
            },
        )

        escaped = escape(html)

        return f'''<iframe srcdoc="{escaped}" style="width: 100%; border: none;" class="gsk-scan"></iframe>
<script>
(function() {{
    // @TODO: fix this
    let elements = document.querySelectorAll(".gsk-scan");
    elements.forEach(el => {{
        el.style.height = el.contentWindow.document.body.scrollHeight + "px";
        setTimeout(() => {{
            el.style.height = el.contentWindow.document.body.scrollHeight + "px";
        }}, 1000)

    }})
}})()
</script>
'''

    def to_dataframe(self):
        df = pd.DataFrame(
            [
                {
                    "domain": issue.domain,
                    "metric": issue.metric,
                    "deviation": issue.deviation,
                    "description": issue.description,
                }
                for issue in self.issues
            ]
        )
        return df
