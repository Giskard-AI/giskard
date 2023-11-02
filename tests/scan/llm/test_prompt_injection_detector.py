from giskard.llm.prompt_injection.data import get_all_prompts


def test_num_samples():
    num_samples = 102

    # len of single_prompts = 14
    # 102 - 14 = 88
    # 88/4 == 88/4 == 22
    prompts = get_all_prompts(num_samples=num_samples)
    assert num_samples == len(prompts)
