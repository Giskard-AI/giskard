from colorama import Fore, Style
from typing import Optional, List
from dataclasses import dataclass, field

CHARS_LIMIT = 120

# Aliasing
BLACK = Fore.LIGHTBLACK_EX
RED = Fore.LIGHTRED_EX
GREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.LIGHTYELLOW_EX
BLUE = Fore.LIGHTBLUE_EX
MAGENTA = Fore.LIGHTMAGENTA_EX
CYAN = Fore.LIGHTCYAN_EX
WHITE = Fore.LIGHTWHITE_EX

BOLD = Style.BRIGHT


@dataclass(frozen=True)
class StyleBase:
    colors: List = field(default_factory=lambda: [BLACK])
    fonts: List = field(default_factory=lambda: [Style.BRIGHT])
    styles: List[str] = field(default_factory=lambda: ["{reset}{font}{color}{{}}{reset}"])
    template: str = "{}"
    num_args: int = 1

    def get_styles(self):
        _styles = []
        for i in range(len(self.template.split("{}")) - 1):
            _styles += [
                self.styles[i].format(
                    reset=Style.RESET_ALL, font=self.fonts[i], color=self.colors[i], template=self.template
                )
            ]
        return _styles

    def process_template(self):
        _template = self.template.replace(" {} ", "{}")
        for p in [" {}", "{} ", "{}"]:
            _template = _template.replace(p, "{}")

        return _template.format(*self.get_styles()).split("{}")

    def check_num_args(self, *args):
        if len(args) != self.num_args:
            p = "s" if self.num_args > 1 else ""
            raise ValueError(
                f"{self.__class__.__name__} expects exactly {self.num_args} argument{p} to xprint but "
                f"{len(args)} received."
            )

    def get(self, *args):
        wrap = self.process_template()
        return wrap[0], *args, wrap[1]


@dataclass(frozen=True)
class SingleStyleBase(StyleBase):
    num_args: int = 1

    def get(self, *args):
        self.check_num_args(*args)
        return super().get(*args)


@dataclass(frozen=True)
class DoubleStyleBase(StyleBase):
    colors: List = field(default_factory=lambda: [BLACK] * 2)
    fonts: List = field(default_factory=lambda: [Style.BRIGHT] * 2)
    styles: List[str] = field(default_factory=lambda: ["{reset}{font}{color}{{}}{reset}"] * 2)
    template: str = "{} {}"
    num_args: int = 2

    def get(self, *args):
        self.check_num_args(*args)
        wrap = self.process_template()
        return wrap[0], args[0], wrap[1], args[1], wrap[2]


@dataclass(frozen=True)
class DetectorStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [BLUE])
    template: str = "Running the {} detector…"


@dataclass(frozen=True)
class NumberOfPromptsStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [CYAN])
    template: str = "Evaluating {} prompts…"


@dataclass(frozen=True)
class PromptEvaluationStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [MAGENTA, YELLOW])
    template: str = "Evaluating {} prompt with the {} evaluator…"


@dataclass(frozen=True)
class EvaluationStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [YELLOW])
    template: str = "Evaluating prompts with the {} evaluator…"


@dataclass(frozen=True)
class PromptInjectionSuccessStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [GREEN, MAGENTA])
    template: str = "{} of the {} prompts manipulated your model into jailbreak."


@dataclass(frozen=True)
class PromptInjectionFailureStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [MAGENTA, RED])
    template: str = "The injection of {} prompts manipulated your model into jailbreak {} of the times."


@dataclass(frozen=True)
class StartSummaryStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [BLUE])
    template: str = "-" * (CHARS_LIMIT // 2 - 8) + " Summary of {} " + "-" * (CHARS_LIMIT // 2 - 8)


def xprint(
    *args,
    style: Optional[StyleBase] = None,
    filename: Optional[str] = None,
    verbose: bool = True,
    **kwargs,
):
    if not verbose:
        return

    if style is not None:
        args = style().get(*args)

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
