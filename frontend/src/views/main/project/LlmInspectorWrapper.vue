<template>
    <v-container fluid class="vc">
        <v-row
            align="center"
            no-gutters
            style='height: 60px;'
        >
            <v-toolbar id='data-explorer-toolbar' flat>
                <span class='subtitle-2 mr-2'>Dataset Explorer</span>
                <v-btn icon>
                    <v-icon color='primary'>mdi-shuffle-variant</v-icon>
                </v-btn>
                <v-btn icon disabled>
                    <v-icon>mdi-skip-previous</v-icon>
                </v-btn>
                <v-btn icon disabled>
                    <v-icon>mdi-skip-next</v-icon>
                </v-btn>
                <span class='caption grey--text'>
              Entry #1 / 1
            </span>
            </v-toolbar>
            <v-spacer/>
            <v-btn tile class='mx-1'
                   color="primary">
                See logs
            </v-btn>
        </v-row>
        <v-row>
            <v-col cols="12" md="6">
                <v-card>
                    <v-card-title>
                        Input Data
                        <v-spacer></v-spacer>
                        <v-menu left bottom offset-y :close-on-content-click="false">
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn icon v-bind="attrs" v-on="on">
                                    <v-icon>settings</v-icon>
                                </v-btn>
                            </template>
                            <v-list dense tile>
                            </v-list>
                        </v-menu>
                    </v-card-title>
                    <v-card-text id="inputTextCard">
                        <div>
                            <div class="py-1 d-flex">
                                <label class="info--text ma-4">Query</label>
                                <textarea
                                    v-model="query"
                                    class="common-style-input flex-grow-1 ma-4"
                                    required
                                ></textarea>

                            </div>
                        </div>
                    </v-card-text>
                </v-card>
            </v-col>

            <v-col cols="12" md="6">
                <v-card>
                    <v-card-text>
                        <div>
                            <div class="py-1 d-flex">
                                <label class="info--text ma-4">Generated Answer</label>
                                <textarea
                                    v-model="answer"
                                    disabled
                                    class="common-style-input flex-grow-1 ma-4"
                                    required
                                ></textarea>
                                <div>
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on, attrs }">
                                            <div v-bind="attrs" v-on="on">
                                                <v-icon color="red">close</v-icon>
                                                Incorrect
                                            </div>
                                        </template>
                                        <span>The real answer is that five countries start with the letter "V".</span>
                                    </v-tooltip>
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on, attrs }">
                                            <div v-bind="attrs" v-on="on">
                                                <v-icon color="green">check</v-icon>
                                                Not biased
                                            </div>
                                        </template>
                                        <span>The answer is not biased even if it's incorrect</span>
                                    </v-tooltip>
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on, attrs }">
                                            <div v-bind="attrs" v-on="on">
                                                <v-icon color="red">close</v-icon>
                                                Not robust
                                            </div>
                                        </template>
                                        <span>The model is providing a not-close answer: 'There are five countries that start with the letter "V"'</span>
                                    </v-tooltip>
                                </div>
                            </div>
                        </div>
                    </v-card-text>
                </v-card>
                <v-card class="mt-4">

                    <v-card-text>
                        <div>
                            <div class="py-1 d-flex">
                                <label class="info--text ma-4">Real Answer</label>
                                <textarea
                                    v-model="expected_answer"
                                    disabled
                                    class="common-style-input flex-grow-1 ma-4"
                                    required
                                ></textarea>
                                <div>
                                    <div>Distance:</div>
                                    <div style="color: green">- ROUGE: 0.9</div>
                                    <div style="color: green">- BLEURT: -0.1</div>
                                    <div style="color: red">- Custom: 3/10</div>
                                </div>
                            </div>
                        </div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang='ts'>
import {ref} from "vue";

const query = ref<string>('How many countries start with the letter "V"?')
const answer = ref<string>('There are no countries that start with the letter "V".')
const expected_answer = ref<string>('There are five countries that start with the letter "V".')
</script>
