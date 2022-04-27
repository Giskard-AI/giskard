<template>
	<v-container fluid class="font-weight-light">
		<p class="caption">
			Project Unique Key: <strong>{{project.key}}</strong>
			<br>Created by: <strong>{{ getUserFullDisplayName(project.owner_details) }}</strong>
			<br>On: <strong>{{project.created_on.toLocaleDateString()}}</strong>
		</p>
		<p v-show="project.description">{{project.description}}</p>
		<v-divider class="my-4"></v-divider>
		<div class="subtitle-1">
			Guest Users
		</div>
		<div class="px-2">
			<table v-if="project.guest_list.length">
				<tr v-for="p in project.guest_list" :key="p.user_id">
					<td class="caption pr-4">{{ getUserFullDisplayName(p) }}</td>
					<td v-if="isProjectOwnerOrAdmin"><v-btn icon small color="accent" @click="cancelUserInvitation(p)"><v-icon small>person_remove</v-icon></v-btn></td>
				</tr>
			</table>
			<p v-else class="caption">None</p>
		</div>
	</v-container>
</template>

<script lang="ts">
import { Component, Vue, Prop } from 'vue-property-decorator';
import { readProject } from '@/store/main/getters';
import { dispatchUninviteUser } from '@/store/main/actions';
import { getUserFullDisplayName } from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
import FeedbackList from '@/views/main/project/FeedbackList.vue';
import { IUserProfileMinimal } from '@/interfaces';

@Component({
	components: {
		Models, Datasets, FeedbackList
	}
})
export default class ProjectOverview extends Vue {

	@Prop({ required: true }) projectId!: number;
	@Prop({type: Boolean, required: true, default: false}) isProjectOwnerOrAdmin!: boolean;

	get project() {
		return readProject(this.$store)(this.projectId)
	}

	private getUserFullDisplayName = getUserFullDisplayName

	public async cancelUserInvitation(user: IUserProfileMinimal) {
		const confirm = await this.$dialog.confirm({
			text: `Are you sure you want to cancel invitation of user <strong>${user.user_id}</strong>?`,
			title: 'Cancel user invitation'
    });
		if (this.project && confirm) {
			try {
				await dispatchUninviteUser(this.$store, {projectId: this.project.id, userId:user.id})
			}	catch (e) {
				console.error(e)
			}
		}
	}
}
</script>

<style scoped>
</style>
