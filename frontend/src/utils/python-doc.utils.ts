import {CallableDTO} from "@/generated-sources";

const ARG_DELIMITERS = ['Args:', 'Arguments:'];
const RETURN_DELIMITER = 'Return:';

const ARGUMENT_REGEX = /([a-z_]+)\s?(\([A-Za-z]*\))?:(([\s\S](?!([a-z_]+\S?(\([A-Za-z]*\))?:)))*)/gm;

export type ParsedDocstring = {
    body: string;
    args: { [arg: string]: string }
}

function findArguments(body?: string) {
    if (!body) {
        return {
            argsPosition: -1,
            offset: -1
        };
    }

    for (const delimiter of ARG_DELIMITERS) {
        let argsPosition = -1;
        if ((argsPosition = body.indexOf(delimiter)) !== -1) {
            return {
                argsPosition,
                offset: delimiter.length
            }
        }
    }

    return {
        argsPosition: -1,
        offset: -1
    };
}

export function extractArgumentDocumentation(callable: CallableDTO | null): ParsedDocstring {
    const doc: ParsedDocstring = {
        body: callable?.doc ?? "",
        args: {}
    };

    const {argsPosition, offset} = findArguments(doc.body);
    if (argsPosition === -1) {
        return doc;
    }

    const returnPosition = doc.body.indexOf(RETURN_DELIMITER);

    const argsString = doc.body.slice(argsPosition + offset, returnPosition === -1 ? undefined : returnPosition);
    doc.body = doc.body.slice(0, argsPosition) + (returnPosition === -1 ? "" : doc.body.slice(returnPosition))

    let match;
    while ((match = ARGUMENT_REGEX.exec(argsString)) !== null) {
        console.log(match)
        const [, name, , docstring] = match;
        doc.args[name] = docstring
    }

    return doc;
}
