import {useProjectArtifactsStore} from "@/stores/project-artifacts";

export function $tags(input: string): string {
    if (input == undefined) {
        return input;
    }

    const store = useProjectArtifactsStore();

    // In the input, there will be tags such as: <model:uuid>, <dataset:uuid>
    // The uuid is like model:b1d7dd0e-400c-421d-8b0e-721f852e77a8
    // Grab their names from the stored data and replace it!
    let result = input;
    const modelRegex = /<model:(.*?)>/g;
    // Can match: <dataset:uuid>, <*_dataset:uuid>
    const datasetRegex = /<([a-z_]*_)?dataset:(.*?)>/g;
    const modelMatches = input.matchAll(modelRegex);
    const datasetMatches = input.matchAll(datasetRegex);

    for (const match of modelMatches) {
        const model = store.models.find(model => model.id === match[1]);
        if (model) {
            result = result.replace(match[0], $tags(model.name ?? "Unnamed model"));
        }
    }

    for (const match of datasetMatches) {
        const dataset = store.datasets.find(dataset => dataset.id === match[2]);
        if (dataset) {
            result = result.replace(match[0], $tags(dataset.name ?? "Unnamed dataset"));
        }
    }

    return result;
}