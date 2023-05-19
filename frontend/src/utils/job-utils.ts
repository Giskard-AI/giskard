import {JobDTO, JobState} from '@/generated-sources';
import {api} from '@/api';
import {computeOnValueChanged, voidFunction} from '@/utils/functional-utils';

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

/**
 * Different from setInterval since it wait the tasks to end before rescheduling
 */
export function schedulePeriodicJob(task: () => Promise<void>, delayMs: number): () => void {
    const state = {
        cancelled: false
    }

    const periodicTask = async () => {
        if (!state.cancelled) {
            await task();
            setTimeout(periodicTask, delayMs);
        }
    }
    setTimeout(periodicTask, 0);


    return () => state.cancelled = true;
}
