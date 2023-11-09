from colorama import Fore
from colorama import Style as _Style
from typing import Optional, List
from dataclasses import dataclass

CHARS_LIMIT = 120
PLACEHOLDER = "{}"

# Aliasing
BLACK_COLOR = Fore.LIGHTBLACK_EX
RED_COLOR = Fore.LIGHTRED_EX
GREEN_COLOR = Fore.LIGHTGREEN_EX
YELLOW_COLOR = Fore.LIGHTYELLOW_EX
BLUE_COLOR = Fore.LIGHTBLUE_EX
MAGENTA_COLOR = Fore.LIGHTMAGENTA_EX
CYAN_COLOR = Fore.LIGHTCYAN_EX
WHITE_COLOR = Fore.LIGHTWHITE_EX

RESET = _Style.RESET_ALL
BOLD = _Style.BRIGHT


@dataclass(frozen=True)
class Style:
    color: int = RESET
    font: int = BOLD
    design: str = "{reset}{font}{color}{" + PLACEHOLDER + "}{reset}"


class Template:
    def __init__(self, content: str = PLACEHOLDER, pstyles: Optional[List[Style]] = None) -> None:
        self.content = content
        self.pstyles = pstyles
        if not self.pstyles:
            self.pstyles = [Style()]

    @property
    def num_placeholders(self):
        return len(self.content.split(PLACEHOLDER))

    @property
    def num_styles(self):
        return len(self.pstyles)


def get_design_templates(template: Template):
    _design_templates = []
    for i in range(template.num_placeholders - 1):
        _design_templates += [
            template.pstyles[i].design.format(
                reset=RESET,
                font=template.pstyles[i].font,
                color=template.pstyles[i].color,
                string_template=template.content,
            )
        ]
    return _design_templates


def process_template(template: Template):
    _content_template = template.content.replace(" " + PLACEHOLDER + " ", PLACEHOLDER)
    for p in [" " + PLACEHOLDER, PLACEHOLDER + " "]:
        _content_template = _content_template.replace(p, PLACEHOLDER)

    return _content_template.format(*get_design_templates(template)).split(PLACEHOLDER)


def style(*args, template: Optional[Template] = None):
    if not template:
        template = Template()
    wraps = process_template(template)
    out = []
    for i, _style in enumerate(template.pstyles):
        if i == template.num_styles - 1 and len(args[i:]) > 1:
            out += [wraps[i], *args[i:]]
            break
        out += [wraps[i], args[i]]
    out += [wraps[-1]]
    return out


# Aliasing
BLACK_STYLE = Style(color=BLACK_COLOR)
RED_STYLE = Style(color=RED_COLOR)
GREEN_STYLE = Style(color=GREEN_COLOR)
YELLOW_STYLE = Style(color=YELLOW_COLOR)
BLUE_STYLE = Style(color=BLUE_COLOR)
MAGENTA_STYLE = Style(color=MAGENTA_COLOR)
CYAN_STYLE = Style(color=CYAN_COLOR)
WHITE_STYLE = Style(color=WHITE_COLOR)

SCAN_COST_ESTIMATE_CONTENT = """ ⚠️{}
This automatic scan will use LLM-assisted detectors based on GPT-4 to identify vulnerabilities in your model.
These are the total estimated costs:
Estimated calls to your model: ~{}
Estimated OpenAI GPT-4 calls for evaluation: {} (~{} prompt tokens and ~{} sampled tokens)
OpenAI API costs for evaluation are estimated to ${}.
"""

SCAN_COST_SUMMARY_CONTENT = """LLM-assisted detectors have used the following resources:
OpenAI GPT-4 calls for evaluation: {} ({} prompt tokens and {} sampled tokens)
OpenAI API costs for evaluation amount to ${} (standard pricing).
"""


@dataclass(frozen=True)
class Catalog:
    Black = Template(content="{}", pstyles=[BLACK_STYLE])
    Red = Template(content="{}", pstyles=[RED_STYLE])
    Green = Template(content="{}", pstyles=[GREEN_STYLE])
    Yellow = Template(content="{}", pstyles=[YELLOW_STYLE])
    Blue = Template(content="{}", pstyles=[BLUE_STYLE])
    Magenta = Template(content="{}", pstyles=[MAGENTA_STYLE])
    Cyan = Template(content="{}", pstyles=[CYAN_STYLE])
    White = Template(content="{}", pstyles=[WHITE_STYLE])

    Detector = Template(content="Running {}…", pstyles=[BLUE_STYLE])
    PromptsNumber = Template(content="Evaluating {} prompts…", pstyles=[CYAN_STYLE])
    PromptEvaluation = Template(
        content="Evaluating {} prompt with the {} evaluator…", pstyles=[MAGENTA_STYLE, YELLOW_STYLE]
    )
    Evaluation = Template(content="Evaluating prompts with the {} evaluator…", pstyles=[YELLOW_STYLE])
    PromptInjectionSuccess = Template(
        content="{} of the {} prompts manipulated your model into jailbreak.", pstyles=[GREEN_STYLE, MAGENTA_STYLE]
    )
    PromptInjectionFailure = Template(
        content="The injection of {} prompts manipulated your model into jailbreak {} of the times.",
        pstyles=[MAGENTA_STYLE, RED_STYLE],
    )
    StartSummary = Template(
        content="-" * (CHARS_LIMIT // 2 - 8) + " Summary of {} " + "-" * (CHARS_LIMIT // 2 - 8), pstyles=[BLUE_STYLE]
    )
    DetectedIssues = Template(content="{}: {} detected. (Took {})", pstyles=[BLUE_STYLE, RED_STYLE, MAGENTA_STYLE])
    NoDetectedIssues = Template(content="{}: {} detected. (Took {})", pstyles=[BLUE_STYLE, GREEN_STYLE, MAGENTA_STYLE])
    ScanCostEstimate = Template(
        content=SCAN_COST_ESTIMATE_CONTENT,
        pstyles=[YELLOW_STYLE, MAGENTA_STYLE, MAGENTA_STYLE, CYAN_STYLE, CYAN_STYLE, RED_STYLE],
    )


def xprint(
    *args,
    template: Optional[Template] = None,
    filename: Optional[str] = None,
    verbose: bool = True,
    **kwargs,
):
    if not verbose:
        return

    args = style(*args, template=template)

    if filename is not None:
        with open(filename, "a") as f:
            print(
                *args,
                file=f,
                **kwargs,
            )
    else:
        print(
            *args,
            **kwargs,
        )
