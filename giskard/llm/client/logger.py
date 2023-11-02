class LLMLogger:
    def __init__(self):
        self.calls = []
        self.errors = []

    def log_call(self, prompt_tokens, sampled_tokens):
        self.calls.append((prompt_tokens, sampled_tokens))

    def log_error(self, error):
        self.errors.append(error)

    def reset(self):
        self.calls = []

    def get_num_calls(self):
        return len(self.calls)

    def get_num_prompt_tokens(self):
        return sum(c[0] for c in self.calls)

    def get_num_sampled_tokens(self):
        return sum(c[1] for c in self.calls)
