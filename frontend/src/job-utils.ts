import {JobDTO, JobState} from '@/generated-sources';
import {api} from '@/api';
import {computeOnValueChanged, voidFunction} from '@/functional-utils';

const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function trackJob(uuid: string, onUpdate?: (JobDTO) => void): Promise<JobDTO> {
    let job: JobDTO | null = null;
    const distinctUpdate = computeOnValueChanged<JobDTO, void>(onUpdate ?? voidFunction,
        (l, r) => l.state === r.state && l.progress === r.progress);

    do {
        if (job !== null) {
            await sleep(500);
        }
        job = await api.trackJob(uuid);
        distinctUpdate(job);
    } while (job.state !== JobState.ERROR && job.state !== JobState.SUCCESS);

    return job;
}
