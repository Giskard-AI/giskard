#!/usr/bin/env python3
"""Base classes for probes.

Probe plugins must inherit one of these. `Probe` serves as a template showing
what expectations there are for inheriting classes. """

import copy
import logging
from typing import List

from colorama import Fore, Style
from tqdm import tqdm

from ..attempt import Attempt, ATTEMPT_STARTED


class Probe:
    """Base class for objects that define and execute LLM evaluations"""

    uri = ""
    bcp47 = None  # language this is for, in bcp47 format; * for all langs
    recommended_detector = [
        "always.Fail"
    ]  # the detectors that should be run for this probe. always.Fail is chosen as default to send a signal if this isn't overridden
    active = True
    tags = []  # MISP-format taxonomy categories
    goal = ""  # what the probe is trying to do, phrased as an imperative
    primary_detector = None  # str default detector to run, if the primary/extended way of doing it is to be used (should be a string formatted like recommended_detector above)
    extended_detectors = []  # optional extended detectors

    def __init__(self):
        self.probename = str(self.__class__).split("'")[1]
        print(f"loading {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probe: {Style.RESET_ALL}{self.probename}")
        logging.info(f"probe init: {self}")
        if "description" not in dir(self):
            if self.__doc__:
                self.description = self.__doc__.split("\n")[0]
            else:
                self.description = ""

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        return attempt

    def _generator_precall_hook(self, generator, attempt=None):
        pass

    def _postprocess_hook(self, attempt: Attempt) -> Attempt:
        return attempt

    def _mint_attempt(self, prompt, seq=None) -> Attempt:
        new_attempt = Attempt()
        new_attempt.prompt = prompt
        new_attempt.probe_classname = (
            str(self.__class__.__module__).replace("garak.probes.", "") + "." + self.__class__.__name__
        )
        new_attempt.status = ATTEMPT_STARTED
        new_attempt.goal = self.goal
        new_attempt.seq = seq
        new_attempt = self._attempt_prestore_hook(new_attempt, seq)
        return new_attempt

    def probe(self, generator) -> List[Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug(f"probe execute: {self}")

        attempts = []
        prompts = list(self.prompts)
        prompt_iterator = tqdm(prompts, leave=False)
        prompt_iterator.set_description(self.probename.replace("garak.", ""))

        for seq, prompt in enumerate(prompt_iterator):
            this_attempt = self._mint_attempt(prompt, seq)
            self._generator_precall_hook(generator, this_attempt)
            this_attempt.outputs = generator.generate(prompt)
            # print(this_attempt.as_dict())
            # _config.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            this_attempt = self._postprocess_hook(this_attempt)
            attempts.append(copy.deepcopy(this_attempt))
        return attempts
