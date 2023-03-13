export class Colors {
    static FAIL = '#F44336';
    static PASS = '#4CAF50';
}


type RGB = { r: number, g: number, b: number };

function hexToRgb(hex: string): RGB {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return {
        r: parseInt(result![1], 16),
        g: parseInt(result![2], 16),
        b: parseInt(result![3], 16)
    };
}

function pickHex(start: RGB, stop: RGB, weight: number): RGB {
    const w1 = weight;
    const w2 = 1 - w1;
    return {
        r: Math.round(start.r * w1 + stop.r * w2),
        g: Math.round(start.g * w1 + stop.g * w2),
        b: Math.round(start.b * w1 + stop.b * w2)
    };
}

export function pickHexLinear(steps: Array<RGB>, weight: number): RGB {
    const stepSize = 1 / (steps.length - 1);
    const currentStep = Math.floor(weight / stepSize);
    const stepWeight = (weight - currentStep * stepSize) / stepSize;
    return stepWeight === 0 ? steps[currentStep]
        : pickHex(steps[currentStep], steps[currentStep + 1], stepWeight);
}

export const SUCCESS_GRADIENT = [hexToRgb(Colors.FAIL), hexToRgb('#ff8d00'), hexToRgb(Colors.PASS)];

function componentToHex(c: number): string {
    const hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

export function rgbToHex(rgb: RGB): string {
    return "#" + componentToHex(rgb.r) + componentToHex(rgb.g) + componentToHex(rgb.b);
}
