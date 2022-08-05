import {TestResult} from "@/generated-sources";

export function testStatusToColor(status: TestResult) {
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
