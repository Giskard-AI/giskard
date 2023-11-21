from giskard.scanner.xprint import (
    CHARS_LIMIT,
    PLACEHOLDER,
    BLACK_COLOR,
    RED_COLOR,
    GREEN_COLOR,
    YELLOW_COLOR,
    BLUE_COLOR,
    MAGENTA_COLOR,
    CYAN_COLOR,
    WHITE_COLOR,
    RESET,
    BOLD,
    BLACK_STYLE,
    RED_STYLE,
    GREEN_STYLE,
    YELLOW_STYLE,
    BLUE_STYLE,
    MAGENTA_STYLE,
    CYAN_STYLE,
    WHITE_STYLE,
    Style,
    Template,
    get_design_templates,
    process_template,
    Catalog,
    xprint,
    style,
)


def test_constants():
    assert CHARS_LIMIT == 120
    assert PLACEHOLDER == "{}"


def test_aliases():
    assert BLACK_COLOR == "\x1b[90m"
    assert BLACK_COLOR == "\x1b[90m"
    assert RED_COLOR == "\x1b[91m"
    assert GREEN_COLOR == "\x1b[92m"
    assert YELLOW_COLOR == "\x1b[93m"
    assert BLUE_COLOR == "\x1b[94m"
    assert MAGENTA_COLOR == "\x1b[95m"
    assert CYAN_COLOR == "\x1b[96m"
    assert WHITE_COLOR == "\x1b[97m"

    assert RESET == "\x1b[0m"
    assert BOLD == "\x1b[1m"

    assert BLACK_STYLE == Style(color=BLACK_COLOR)
    assert RED_STYLE == Style(color=RED_COLOR)
    assert GREEN_STYLE == Style(color=GREEN_COLOR)
    assert YELLOW_STYLE == Style(color=YELLOW_COLOR)
    assert BLUE_STYLE == Style(color=BLUE_COLOR)
    assert MAGENTA_STYLE == Style(color=MAGENTA_COLOR)
    assert CYAN_STYLE == Style(color=CYAN_COLOR)
    assert WHITE_STYLE == Style(color=WHITE_COLOR)


def test_defaults():
    default_style = Style()
    assert default_style.color == RESET
    assert default_style.font == BOLD
    assert default_style.design == "{reset}{font}{color}{" + PLACEHOLDER + "}{reset}"

    default_template = Template()
    assert default_template.content == PLACEHOLDER
    assert len(default_template.pstyles) == 1
    assert default_template.pstyles[0] == default_style
    assert default_template.num_placeholders == 1
    assert default_template.num_styles == 1

    default_design_template = get_design_templates(default_template)
    assert default_design_template[0] == "\x1b[0m\x1b[1m\x1b[0m{}\x1b[0m"

    default_processing = process_template(default_template)
    assert len(default_processing) == 2
    assert default_processing[0] == "{}{}{}".format(RESET, BOLD, RESET)
    assert default_processing[1] == "{}".format(
        RESET,
    )

    args = style("test", default_template)
    assert args[0] == default_processing[0]
    assert args[1] == "test"
    assert args[2] == default_template
    assert args[3] == default_processing[1]


def test_catalog():
    catalog = Catalog()
    attributes = [
        "Black",
        "Red",
        "Green",
        "Yellow",
        "Blue",
        "Magenta",
        "Cyan",
        "White",
        "Detector",
        "PromptsNumber",
        "PromptEvaluation",
        "Evaluation",
        "PromptInjectionSuccess",
        "PromptInjectionFailure",
        "StartSummary",
        "DetectedIssues",
        "NoDetectedIssues",
        "ScanCostEstimate",
        "ScanCostSummary",
    ]
    for attribute in attributes:
        assert hasattr(catalog, attribute)


def test_xprint(capsys):
    xprint("test")
    captured = capsys.readouterr()
    assert captured.out == "{}{}{} test {}\n".format(RESET, BOLD, RESET, RESET)
    xprint("test", template=Catalog.Green)
    captured = capsys.readouterr()
    assert captured.out == "{}{}{} test {}\n".format(RESET, BOLD, GREEN_COLOR, RESET)
