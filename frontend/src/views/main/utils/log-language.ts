export const logLanguage = {
    tokenizer: {
        root: [
            [/ERROR.*/, "custom-error"],
            [/WARN.*/, "custom-warn"],
            [/INFO.*/, "custom-info"],
            [/DEBUG.*/, "custom-debug"],
            [/\d{4}(-\d\d(-\d\d( \d\d:\d\d(:\d\d)?(,\d+)?(([+-]\d\d:\d\d)|Z)?)?)?)?/i, "custom-date"],
        ]
    }
};

export const logTheme = {
    base: 'vs',
    inherit: false,
    rules: [
        {token: 'custom-info', foreground: '#4b71ca'},
        {token: 'custom-error', foreground: '#FF0000', fontStyle: 'bold'},
        {token: 'custom-warning', foreground: '#FFA500'},
        {token: 'custom-debug', foreground: '#555555'},
        {token: 'custom-date', foreground: '#008800'},
    ],
    colors: {
        "editor.foreground": "#000",
    },
}
