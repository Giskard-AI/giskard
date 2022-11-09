import {TestResult} from "@/generated-sources";

function testStatusToColor(status: TestResult) {
    switch (status) {
        case TestResult.PASSED:
            return 'green lighten-2';
        case TestResult.FAILED:
            return 'red lighten-2';
        case TestResult.ERROR:
            return 'black lighten-3';
    }
}

function testStatusToIcon(status: TestResult){
    switch (status) {
        case TestResult.PASSED:
            return 'fa-check';
        case TestResult.FAILED:
            return 'fa-xmark';
        default:
            return 'fa-exclamation';
    }
}

export {
    testStatusToColor, testStatusToIcon
}
