import re
import random
import pandas as pd

from .entity_swap import typos, gender_switch_en
from ...core.core import DatasetProcessFunctionMeta
from ...ml_worker.testing.registry.registry import get_object_uuid
from ...ml_worker.testing.registry.transformation_function import TransformationFunction


class TextTransformation(TransformationFunction):
    name: str

    def __init__(self, column):
        super().__init__(None, row_level=False, cell_level=False)
        self.column = column
        self.meta = DatasetProcessFunctionMeta(type='TRANSFORMATION')
        self.meta.uuid = get_object_uuid(self)
        self.meta.code = self.name
        self.meta.name = self.name
        self.meta.display_name = self.name
        self.meta.tags = ["pickle", "scan"]
        self.meta.doc = 'Automatically generated transformation function'

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.apply(self.make_perturbation)
        return data

    def make_perturbation(self, text: str) -> str:
        raise NotImplementedError()

    def _should_save_locally(self) -> bool:
        return True


class TextUppercase(TextTransformation):
    name = "Transform to uppercase"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.upper()
        return data


class TextLowercase(TextTransformation):
    name = "Transform to lowercase"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.lower()
        return data


class TextTitleCase(TextTransformation):
    name = "Transform to title case"

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_data = data[self.column].dropna().astype(str)
        data.loc[feature_data.index, self.column] = feature_data.str.title()
        return data


class TextTypoTransformation(TextTransformation):
    name = "Add typos"

    def make_perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._add_typos(token))
        return " ".join(new_text)

    def _add_typos(self, word):
        # Get the token's word and apply a perturbation with probability 0.1
        if random.random() < 0.2 and len(word) > 1:
            # Choose a perturbation type randomly
            perturbation_type = random.choice(['insert', 'delete', 'replace'])
            # Apply the perturbation
            if perturbation_type == 'insert':
                idx = random.randint(0, len(word))
                new_char = chr(random.randint(33, 126))
                word = word[:idx] + new_char + word[idx:]
                return word
            elif perturbation_type == 'delete':
                idx = random.randint(0, len(word) - 1)
                word = word[:idx] + word[idx + 1 :]
                return word
            elif perturbation_type == 'replace':
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in typos:
                    replacement = random.choice(typos[c])
                    text_modified = word[:j] + replacement + word[j + 1 :]
                    return text_modified
        return word


class TextPunctuationRemovalTransformation(TextTransformation):
    name = "Punctuation Removal"

    _punctuation = """'・﹝꛳※；〈๚“𑙢⁑៚︵｠؉︿﹜᯿｢〈＆⸲᳀࠽＿།၍𑑛［᪨𑇝።᭞፧᪩︲⸦〜᚜᳄❳࿑⁜?፣𒑱՞⸧꘍﹏᪦❭𐽗༈৽⹍𖺚﹄︑܌⸄಄࠳⦊⸑𑪞_࠲⳺⧘꛵𑗈⸳⧼‷᛭᨟܁﹃᠁﹁𑅴＠،′֊‱፡–⦃⸸﹆༄࿚𐽘܉꧟𖬷⸛❬⹋፠﹅𑈽𐩓﹎჻⦘︘𑙦*𑗕꣸％@‼᜶⁾;〟༑〕𝪉⁗︰⦋𐡗𑻷𑁊𐬺𑻸⟨⸰·︴𐮜⟬𖬹〙⁂—⸴܊𑗎𖬻࿓⸱&꧍׃〗𑗖‶𑙧？⸕𐫲𑑏༅𑱱૰࠴﹖‗𑁍𑩁܀⸷＇𑈻𑇆𖿢‸꙳⸼־؍⁘⟧₎߷𑱂⸔﹨︶࠵﹈｡𑙂꩝⳹᥅•𐫱⁔⸀«゠𑙁𛲟⟩𐮛៘⁖⸜᱿⹈𑗓࠰⵰﹐⁕﹊⸪﹟𐩕༻𑱁៙¿។࠼⸐／𑗊〉⸻﹔𐩿꓾𑩄᙮⧚𐩗᪥⸒】＊᠃𑪜𖭄❫𑑋𑪟܍٬⁀⸙〞⸌᰼𑙃𑩅⦉꛲꧉𐩔𑙩〖"౷‖﹍⁇꧞]𑇞᚛𝪋᯼⦖𑩆፥𑅵𑁇𑜾؊!⁁﹚𞥟᪫٭᜵⁆𑇟᠉。𐫶⸫؛꣼࠸𑁌‚𑱄𑥆､〽᳓﹡꓿⸞࠺𐕯”᭛″׳᰾⹁⸶𑩃꧃︳𖩯〉𑊩𑅂﹇‘＂⸺⸉෴༏᛫︓𐽖᰻⟯᳁𑂿᳇࠶₍፦𑈹，𑗌⁉𑪢！%॰𒑰⦌𑧢⸖᭜⹒༊𑑎⳼⸟⹌.𝪇︱𑑚⁋⟅၊᪭︹꡴』𑙣⸂﹫『𑗃᳆⌈՛𑗋‒𑅁：𐬻⁎𑜽︽𑙡𑁋᪤⦕𐄀⁈⸭𑁈𖬸︻༼𐄁⸬⹄﹪⌋］࿒❰𝪊๏/⹎᐀⦔„⁛﴿𑈺〛︸﹕⟪꧋﹀﹑𑗔⸘︾⸋︼⸝՝៕)࠾་𑑝‰⦍【⁚꩞⸅꫰꫱𑿿׀－𑇅꯫᪬𖺗𑈸𐩘꥟𑙬-༎𖬺𑑌‾߸⦗⁓᥄‿⦐𒑴𑃀＃𑪛៖𑂼‑꧇𑙤〰⁌︐⦅︺»‧⟮𑅀𐄂〚᳅⦄၎𐩑𑨿𑱅︒﹉᠈𑗑꤯﹂᱾⦎𑙫❪＼༆࡞༒‛𑇈᪪᪡꫟𑠻\'·𑥄𑪡܈⟦༽⸵𐤟𐮚⳾՟⸓﹗⦑؟𖺙﹋⸎#״࠷︕︙𑂻⦏⧛⦆⳻︷၌𑗂︗꧁⸠⸈᭠𞥞꧄（{𑗗⸩⦓߹⹅𑂾⁽⸡𒑳}⹃𐎟܂｣𑇍𑇇᪠𐩖੶᨞．𐫰॥﹘꧂｛𑥅⁏꧌᠄༔⸏࿔𑗍᰽⦇܆࠻؞𑗏𖩮⸇𑱃𑪠¡﴾࿐(‴、꣏⸥᯽꙾𐽕𑜼¶᯾꛴𝪈,❩꧅⁞⸢⸾⹇𐬿𑗉⸣꛷﹣⳿⸿〝܅᛬𐩒⸍;꩟𐬼§⁐⁅﹠❵᠊꣹⁙𑩀︔𐫵𖫵։⌊⟆‵܋❴‥𑪚𐬽٫⧙﹛𐽙𑈼﹌‹❱၏꩜՚፤٪꘏࿙⟭྅）〔》𑗅⹏〃𐩐⦈܄⹂𑑍𑓆𑗐❲။᭟―᭝｝𑗒᠅𑩂᳂᠀‣⟫꧈’𑙠𑱰⸤𑗁༉❯⸨۔༇⸽⹊𐏐꛶𖺘𑁉‡:፨꡷﹙᭚｟❨꫞᪣︖꣺𐫳𐫴܇꘎𒑲᠇՜﹞𐺭《𑗇꧊›।⸗⸃⸚꣎⧽꧆𑙥᪢⁊…‽᰿꤮𐬾𑙪[࠹﹒･𑗆․𐤿⹉⸹❮༐༌‟⁃⌉⸮𐮙𑙨𑃁⸁𐬹⹀\\᳃⹆׆܃༺「𑗄࠱๛⁝⸆꡵𑇛⁍᠂᠆⦒」〘𑅃⸊꡶‐†'"""

    def make_perturbation(self, x):
        split_text = x.split(" ")
        new_text = []
        for token in split_text:
            new_text.append(self._remove_punc(token))
        return " ".join(new_text)

    def _remove_punc(self, text):
        return text.translate(str.maketrans('', '', self._punctuation))


class TextGenderTransformation(TextTransformation):
    name = "Switch gender"

    def make_perturbation(self, x):
        split_text = x.split()
        new_words = []
        for token in split_text:
            new_word = self._switch(token)
            if new_word != token:
                new_words.append(new_word)

        new_text = x
        for original_word, switched_word in new_words:
            new_text = re.sub(fr"\b{original_word}\b", switched_word, new_text)
        return new_text

    def _switch(self, word):
        if word.lower() in gender_switch_en:
            return [word, gender_switch_en[word.lower()]]
        else:
            return word
