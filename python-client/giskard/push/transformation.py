import random

import spacy

# Load the English language model
nlp = spacy.load('en_core_web_sm')


class TextTransformer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def replace_ethnicity(self, text):
        return self._replace_by_mask(text, "NORP", "[ETHNICITY]")

    def replace_gender(self, text):
        return self._replace_by_mask(self._replace_by_mask(text, "PRP", "[GENDER]"), "PRP$", "[GENDER]")

    def replace_loc(self, text):
        return self._replace_by_mask(text, "GPE", "[LOCATION]")

    def _replace_by_mask(self, text, ent_type, mask):
        doc = self.nlp(text)
        new_text = []
        for token in doc:
            if ent_type == "GPE" or ent_type == "NORP":
                if token.ent_type_ == ent_type:
                    new_text.append(mask)
                else:
                    new_text.append(token.text)
            else:
                if token.tag_ == ent_type:  # PRP$
                    new_text.append(mask)
                else:
                    new_text.append(token.text)

        return " ".join(new_text)

    def char_perturbation(self, text):
        """
        Perform a character-level perturbation attack on the input text by adding or deleting random characters, and
        perform a typo attack on the input text.
        """
        # Split the text into tokens
        tokens = text.split()

        # Loop over the tokens in the document
        for i in range(len(tokens)):
            # Get the token's text and apply a perturbation with probability 0.1
            if random.random() < 0.1:
                # Choose a perturbation type randomly
                perturbation_type = random.choice(['insert', 'delete', 'replace'])

                # Apply the perturbation
                if perturbation_type == 'insert':
                    idx = random.randint(0, len(tokens[i]))
                    new_char = chr(random.randint(33, 126))
                    tokens[i] = tokens[i][:idx] + new_char + tokens[i][idx:]
                elif perturbation_type == 'delete':
                    idx = random.randint(0, len(tokens[i]) - 1)
                    tokens[i] = tokens[i][:idx] + tokens[i][idx + 1:]
                elif perturbation_type == 'replace':
                    idx = random.randint(0, len(tokens[i]) - 1)
                    new_char = chr(random.randint(33, 126))
                    tokens[i] = tokens[i][:idx] + new_char + tokens[i][idx + 1:]

        # Return the modified text as a string
        return ' '.join(tokens)

    def word_perturbation(self, text):
        """
        Perform random text augmentation by deleting a word, adding a random word, or swapping two words in the input text.
        """
        # Tokenize the input text into words
        words = text.split()

        # Choose a text augmentation operation randomly
        op = random.choice(['delete', 'add', 'swap'])  # ['delete', 'add', 'swap']

        # Delete a random word from the text
        if op == 'delete':
            if len(words) > 1:
                # Choose a random word in the document (excluding the first word)
                word_idx = random.randint(1, len(words) - 1)
                # Delete the selected word
                words.pop(word_idx)

        # Add a random word to the text
        elif op == 'add':
            # Choose a random word from the vocabulary
            new_word = random.choice(list(self.nlp.vocab.strings))
            word_idx = random.randint(0, len(words))
            words.insert(word_idx, new_word)

        # Swap two random words in the text
        elif op == 'swap':
            if len(words) > 1:
                # Choose two random words in the document (excluding the first word)
                word_idx_1 = random.randint(1, len(words) - 1)
                word_idx_2 = random.randint(1, len(words) - 1)
                # Swap the selected words
                words[word_idx_1], words[word_idx_2] = words[word_idx_2], words[word_idx_1]

        # Return the modified text as a string
        return ' '.join(words)

    def upper_case(self, text):
        return text.upper()

    def lower_case(self, text):
        return text.lower()

    def title_case(self, text):
        return text.title()


text = "She her the brown fox jumps over the lazy dog in Sydney, was christian"
text_perturbation_generator = TextTransformer()
print(text_perturbation_generator.replace_gender(text))
print(text_perturbation_generator.replace_loc(text))
print(text_perturbation_generator.replace_ethnicity(text))
print(text_perturbation_generator.lower_case(text))
print(text_perturbation_generator.upper_case(text))
print(text_perturbation_generator.title_case(text))
print(text_perturbation_generator.word_perturbation(text))
print(text_perturbation_generator.char_perturbation(text))
