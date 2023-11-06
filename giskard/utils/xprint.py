from colorama import Fore, Style
from typing import Optional, List
from dataclasses import dataclass, field

CHARS_LIMIT = 120


@dataclass(frozen=True)
class StyleBase:
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLACK_EX])
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
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLACK_EX] * 2)
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
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLUE_EX])
    template: str = "Running the {} detector…"


@dataclass(frozen=True)
class NumberOfPromptsStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTCYAN_EX])
    template: str = "Evaluating {} prompts…"


@dataclass(frozen=True)
class PromptEvaluationStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTMAGENTA_EX, Fore.LIGHTYELLOW_EX])
    template: str = "Evaluating {} prompt with the {} evaluator…"


@dataclass(frozen=True)
class EvaluationStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTYELLOW_EX])
    template: str = "Evaluating prompts with the {} evaluator…"


@dataclass(frozen=True)
class PromptInjectionSuccessStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX])
    template: str = "{} of the {} prompts manipulated your model into jailbreak."


@dataclass(frozen=True)
class PromptInjectionFailureStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX])
    template: str = "The injection of {} prompts manipulated your model into jailbreak {} of the times."


@dataclass(frozen=True)
class StartSummaryStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLUE_EX])
    template: str = "-" * (CHARS_LIMIT // 2 - 8) + " Summary of {} " + "-" * (CHARS_LIMIT // 2 - 8)


def xprint(
    *args,
    style: Optional[StyleBase] = StyleBase,
    filename: Optional[str] = None,
    **kwargs,
):
    styled_args = style().get(*args)

    if filename is not None:
        with open(filename, "a") as f:
            print(
                *styled_args,
                file=f,
                **kwargs,
            )
    else:
        print(
            *styled_args,
            **kwargs,
        )
