import {ref, Ref} from 'vue';
import {JobDTO, JobState} from '@/generated-sources';
import {trackJob} from '@/utils/job-utils';

type UseTrackJob = {
    trackedJobs: Ref<{ [uuid: string]: JobDTO}>,
    addJob: (uuid: string) => Promise<boolean>
};

export function useTrackJob(): UseTrackJob {
    const trackedJobs = ref<{ [uuid: string]: JobDTO}>({});
    const addJob = async uuid => {
        const result = await trackJob(uuid, (res) => trackedJobs.value = {
            ...trackedJobs.value,
            [uuid]: res
        });
        const res = {...trackedJobs.value};
        delete res[uuid]
        trackedJobs.value = res;
        return result.state === JobState.SUCCESS;
    }

    return {
        trackedJobs,
        addJob
    };
}
