from typing import Optional


class LLMLogger:
    def __init__(self):
        self.calls = []
        self.errors = []

    def log_call(
        self,
        prompt_tokens: int,
        sampled_tokens: int,
        model: Optional[str] = None,
        client_class: Optional[str] = None,
        caller_id: Optional[str] = None,
    ):
        self.calls.append(
            {
                "prompt_tokens": prompt_tokens,
                "sampled_tokens": sampled_tokens,
                "model": model,
                "client_class": client_class,
                "caller_id": caller_id,
            }
        )

    def log_error(self, error):
        self.errors.append(error)

    def reset(self):
        self.calls = []

    def get_num_calls(self):
        return len(self.calls)

    def get_num_prompt_tokens(self):
        return sum(c["prompt_tokens"] for c in self.calls)

    def get_num_sampled_tokens(self):
        return sum(c["sampled_tokens"] for c in self.calls)
