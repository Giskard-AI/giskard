LLM Vulnerabilities
===================

Key vulnerability categories
----------------------------

Large Language Model (LLM) vulnerabilities are different from those in traditional ML models. It's crucial to have a comprehensive understanding of these unique critical vulnerabilities that can impact your model. Giskard provides an `automatic scan functionality <../../open_source/scan/index.md>`_ that is designed to automatically detect a variety of risks associated with your LLMs. You can learn more about the different vulnerabilities it can detect here:

.. csv-table::
   :header: "Vulnerability", "Description"

   "Hallucination and Misinformation", "These vulnerabilities often manifest themselves in the generation of fabricated content or the spread of false information, which can have far-reaching consequences such as disseminating misleading content or malicious narratives."
   "Harmful Content Generation", "This vulnerability involves the creation of harmful or malicious content, including violence, hate speech, or misinformation with malicious intent, posing a threat to individuals or communities."
   "Prompt Injection", "Users manipulating input prompts to bypass content filters or override model instructions can lead to the generation of inappropriate or biased content, circumventing intended safeguards."
   "Robustness", "The lack of robustness in model outputs makes them sensitive to small perturbations, resulting in inconsistent or unpredictable responses that may cause confusion or undesired behavior."
   "Output Formatting", "When model outputs do not align with specified format requirements, responses can be poorly structured or misformatted, failing to comply with the desired output format."
   "Information Disclosure", "This vulnerability occurs when the model inadvertently reveals sensitive or private data about individuals, organizations, or entities, posing significant privacy risks and ethical concerns."
   "Stereotypes and Discrimination", "If model's outputs are perpetuating biases, stereotypes, or discriminatory content, it leads to harmful societal consequences, undermining efforts to promote fairness, diversity, and inclusion."

By conducting a `Giskard Scan <../../open_source/scan/index.md>`_, you can proactively identify and address these vulnerabilities to ensure the reliability, fairness, and robustness of your LLMs.
