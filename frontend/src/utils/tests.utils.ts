import {statusFilterOptions} from "@/stores/test-suite";
import {SuiteTestDTO, SuiteTestExecutionDTO} from "@/generated-sources";

export class TestsUtils {

    static statusFilter<T extends { result?: SuiteTestExecutionDTO }>(status: string): (T) => boolean {
        return ({result}) => statusFilterOptions.find(opt => status === opt.label)!.filter(result)
    }

    static searchFilter<T extends { suiteTest: SuiteTestDTO }>(search: string): (T) => boolean {
        return ({suiteTest}) => {
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
        }
    }
}
