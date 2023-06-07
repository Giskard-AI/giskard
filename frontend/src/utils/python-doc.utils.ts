import {CallableDTO} from "@/generated-sources";

const ARG_DELIMITER = 'Args:';
const RETURN_DELIMITER = 'Return:';

const ARGUMENT_REGEX = /([a-z_]+)(\([a-z]*\))?:\n([^\n]*)/gm;

export type ParsedDocstring = {
    body: string;
    args: { [arg: string]: string }
}

export function extractArgumentDocumentation(callable: CallableDTO | null): ParsedDocstring {
    const doc: ParsedDocstring = {
        body: callable?.doc ?? "",
        args: {}
    };

    let argsPosition = -1;
    if (!doc.body || (argsPosition = doc.body.indexOf(ARG_DELIMITER)) === -1) {
        return doc;
    }

    const returnPosition = doc.body.indexOf(RETURN_DELIMITER);

    const argsString = doc.body.slice(argsPosition + ARG_DELIMITER.length, returnPosition === -1 ? undefined : returnPosition);
    doc.body = doc.body.slice(0, argsPosition) + (returnPosition === -1 ? "" : doc.body.slice(returnPosition))

    let match;
    while ((match = ARGUMENT_REGEX.exec(argsString)) !== null) {
        const [, name, , docstring] = match;
        doc.args[name] = docstring
    }

    return doc;
}
