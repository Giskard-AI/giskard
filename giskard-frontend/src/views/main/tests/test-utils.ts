import {TestResult} from "@/generated-sources";

function testStatusToColor(status: TestResult) {
    switch (status) {
        case TestResult.PASSED:
            return 'green lighten-2';
        case TestResult.FAILED:
            return 'red lighten-2';
        case TestResult.ERROR:
            return 'black lighten-2';
        default:
            return 'grey lighten-2';
    }
}

function testStatusToIcon(status: TestResult){
    switch (status) {
        case TestResult.PASSED:
            return 'fa-check';
        case TestResult.FAILED:
            return 'fa-xmark';
        default:
            return '';
    }
}

export {
    testStatusToColor, testStatusToIcon
}
