from pydantic import EmailStr


class CaseInsensitiveEmailStr(EmailStr):
    @classmethod
    def validate(cls, value: str) -> str:
        """
        Inspite RFC 5321 (https://www.rfc-editor.org/rfc/rfc5321.txt)
        that requires the local part of email be case sensitive
        Make the whole email address lower case to keep away from related bugs
        """
        return EmailStr.validate(value).lower()
