from giskard.scanner.llm.utils import LLMImportError

try:
    from langchain.chains.base import Chain
    from langchain.schema import BaseOutputParser
except ImportError as err:
    raise LLMImportError() from err


class AutoChainParser:
    def __init__(self, chain: Chain, parser: BaseOutputParser):
        self.chain = chain
        self.parser = parser

    def run_and_parse(self, **kwargs):
        return self.parser.parse(self.chain.run(kwargs))
