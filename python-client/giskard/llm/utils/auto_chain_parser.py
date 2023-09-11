from giskard.scanner.llm.utils import LLMImportError

try:
    from langchain.chains.base import LLMChain
    from langchain.schema import BaseOutputParser
except ImportError as err:
    raise LLMImportError() from err


class AutoChainParser:
    def __init__(self, chain: LLMChain, parser: BaseOutputParser):
        self.chain = chain
        self.parser = parser

    def run_and_parse(self, **kwargs):
        return self.parser.parse(self.chain.run(kwargs))

    def run_and_parse_with_prompt(self, **kwargs):
        return self.parser.parse_with_prompt(self.chain.run(kwargs), self.chain.prompt.format_prompt(**kwargs))
