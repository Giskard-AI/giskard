from typing import Dict, Sequence


def format_conversation(conversation: Sequence[Dict]):
    return "\n\n".join([f"<{msg['role'].lower()}>{msg['content']}</{msg['role'].lower()}>" for msg in conversation])
