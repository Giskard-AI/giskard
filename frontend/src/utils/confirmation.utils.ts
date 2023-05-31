import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";

export async function confirm(vfm, title: string, text: string | null = null, isWarning: boolean = false): Promise<boolean> {
    return await new Promise(async resolve => {
        let resolved = false;
        await vfm.show({
            component: ConfirmModal,
            bind: {
                title,
                text,
                isWarning
            },
            on: {
                confirm(close) {
                    resolved = true;
                    resolve(true);
                    close();
                },
                closed() {
                    if (!resolved) {
                        resolved = true;
                        resolve(false);
                    }
                }
            }
        })
    })
}
