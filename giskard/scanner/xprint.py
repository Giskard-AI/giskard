from colorama import Fore, Style
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
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
        possibilities = [" {} ", " {}", "{} ", "{}"]
        for p in possibilities:
            self.template = self.template.replace(p, "{}")

        return self.template.format(*self.get_styles()).split("{}")

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


@dataclass
class SingleStyleBase(StyleBase):
    num_args: int = 1

    def get(self, *args):
        self.check_num_args(*args)
        return super().get(*args)


@dataclass
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


@dataclass
class DetectorStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLUE_EX])
    template: str = "Running the {} detector."


@dataclass
class NumberOfPromptsStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTCYAN_EX])
    template: str = "Evaluating {} prompts."


@dataclass
class PromptEvaluationStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTMAGENTA_EX, Fore.LIGHTYELLOW_EX])
    template: str = "Evaluating {} prompt with the {} evaluator."


@dataclass
class PromptInjectionSuccessStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX])
    template: str = "{} of the {} prompts manipulated your model into jailbreak."


@dataclass
class PromptInjectionFailureStyle(DoubleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX])
    template: str = "The injection of {} prompts manipulated your model into jailbreak {} of the times."


@dataclass
class StartSummaryStyle(SingleStyleBase):
    colors: List = field(default_factory=lambda: [Fore.LIGHTBLUE_EX])
    template: str = "-" * 50 + " Summary of {} " + "-" * 50


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
