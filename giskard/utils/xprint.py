from colorama import Fore
from colorama import Style as _Style
from typing import Optional, List
from dataclasses import dataclass

CHARS_LIMIT = 120
PLACEHOLDER = "{}"

# Aliasing
FBLACK = Fore.LIGHTBLACK_EX
FRED = Fore.LIGHTRED_EX
FGREEN = Fore.LIGHTGREEN_EX
FYELLOW = Fore.LIGHTYELLOW_EX
FBLUE = Fore.LIGHTBLUE_EX
FMAGENTA = Fore.LIGHTMAGENTA_EX
FCYAN = Fore.LIGHTCYAN_EX
FWHITE = Fore.LIGHTWHITE_EX

RESET = _Style.RESET_ALL
BOLD = _Style.BRIGHT


@dataclass(frozen=True)
class Style:
    color: int = FBLACK
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
BLACK = Style(color=FBLACK)
RED = Style(color=FRED)
GREEN = Style(color=FGREEN)
YELLOW = Style(color=FYELLOW)
BLUE = Style(color=FBLUE)
MAGENTA = Style(color=FMAGENTA)
CYAN = Style(color=FCYAN)
WHITE = Style(color=FWHITE)


@dataclass(frozen=True)
class Catalog:
    Detector = Template(content="Running {}…", pstyles=[BLUE])
    PromptsNumber = Template(content="Evaluating {} prompts…", pstyles=[CYAN])
    PromptEvaluation = Template(content="Evaluating {} prompt with the {} evaluator…", pstyles=[MAGENTA, YELLOW])
    Evaluation = Template(content="Evaluating prompts with the {} evaluator…", pstyles=[YELLOW])
    PromptInjectionSuccess = Template(
        content="{} of the {} prompts manipulated your model into jailbreak.", pstyles=[GREEN, MAGENTA]
    )
    PromptInjectionFailure = Template(
        content="The injection of {} prompts manipulated your model into jailbreak {} of the times.",
        pstyles=[MAGENTA, RED],
    )
    StartSummary = Template(
        content="-" * (CHARS_LIMIT // 2 - 8) + " Summary of {} " + "-" * (CHARS_LIMIT // 2 - 8), pstyles=[BLUE]
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
