from giskard.llm.prompt_injection.data import get_all_prompts, get_prompts_from_pi
from giskard.llm.prompt_injection.promptinject.prompt_data import rogue_strings

# total number of prompt injections available
TOTAL_PI = 2241
# total number of single prompt injections
TOTAL_SINGLE_PI = 14


def test_num_samples():
    num_samples = 102

    # len of single_prompts = 14
    # 102 - 14 = 88
    # 88/4 == 88/4 == 22
    prompts = get_all_prompts(num_samples=num_samples)
    assert num_samples == len(prompts)

    prompts = get_all_prompts(num_samples=None)
    assert TOTAL_PI == len(prompts)

    prompts = get_all_prompts(num_samples=3000)
    assert TOTAL_PI == len(prompts)

    prompts = get_all_prompts(num_samples=-1)
    assert TOTAL_SINGLE_PI == len(prompts)


def test_prompts_from_pi():

    for rogue_string, match in rogue_strings.items():
        prompts = get_prompts_from_pi(rogue_string)
        for prompt in prompts:
            assert match in prompt.content
