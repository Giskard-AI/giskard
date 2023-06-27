import { statusFilterOptions } from '@/stores/test-suite';
import { SuiteTestDTO, SuiteTestExecutionDTO, TestResult } from '@/generated-sources';
import { Colors } from '@/utils/colors';

type ResultData = {
    capitalized: string,
    icon: string,
    color: string,
    textColor: string,
    type: string
}

export const TEST_RESULT_DATA: { [testResult in TestResult]: ResultData } = {
    [TestResult.FAILED]: {
        capitalized: 'Failed',
        icon: 'close',
        color: Colors.FAIL_SURFACE,
        textColor: Colors.ON_FAIL_SURFACE,
        type: 'error'
    },
    [TestResult.PASSED]: {
        capitalized: 'Passed',
        icon: 'done',
        color: Colors.PASS_SURFACE,
        textColor: Colors.ON_PASS_SURFACE,
        type: 'success'
    },
    [TestResult.ERROR]: {
        capitalized: 'Error',
        icon: 'mdi-alert-outline',
        color: '#fff3cd',
        textColor: '#856404',
        type: 'error'
    }
};

export class TestsUtils {

    static statusFilter<T extends { result?: SuiteTestExecutionDTO }>(status: string): (T) => boolean {
        return ({ result }) => statusFilterOptions.find(opt => status === opt.label)!.filter(result);
    }

    static searchFilter<T extends { suiteTest: SuiteTestDTO }>(search: string): (T) => boolean {
        return ({ suiteTest }) => {
            const test = suiteTest.test;

            const keywords = search.split(' ')
              .map(keyword => keyword.trim().toLowerCase())
              .filter(keyword => keyword !== '');

            return keywords.filter(keyword =>
              test.name.toLowerCase().includes(keyword)
              || test.doc?.toLowerCase()?.includes(keyword)
              || test.displayName?.toLowerCase()?.includes(keyword)
              || test.tags?.filter(tag => tag.includes(keyword))?.length > 0
            ).length === keywords.length;
        };
    }
}
