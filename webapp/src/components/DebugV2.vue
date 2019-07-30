<template>

    <div id="debug-v2">
        <v-dialog
            v-model="dialog"
            width="500"
        >
            <v-btn
                slot="activator"
                color="red lighten-2"
                dark
            >
                Debug
            </v-btn>

            <v-card>
                <v-card-title
                    class="headline grey lighten-2"
                    primary-title
                >
                    Debug Options
                </v-card-title>

                <v-list wrap>
                    <v-list-tile wrap>
                        <br/>
                        <input type="radio" id="mds_otmann" value="mds_otmann" v-model="projectionType">
                        <label for="one">OTMANN MDS</label>
                        <br/>
                        <input type="radio" id="tsne_otmann" value="tsne_otmann" v-model="projectionType">
                        <label for="one">OTMANN TSNE</label>
                        <br/>
                        <input type="radio" id="mds_unweighted" value="mds_unweighted" v-model="projectionType">
                        <label for="one">edit_distance MDS</label>
                        <br/>
                        <input type="radio" id="tsne_unweighted" value="tsne_unweighted" v-model="projectionType">
                        <label for="one">edit_distance TSNE</label>
                        <br/>
                        <input type="radio" id="mds_hamming" value="mds_hamming" v-model="projectionType">
                        <label for="one">hamming MDS</label>
                        <br/>
                        <input type="radio" id="tsne_hamming" value="tsne_hamming" v-model="projectionType">
                        <label for="one">hamming TSNE</label>
                        <br/>
                        <input type="radio" id="hendrik" value="hendrik" v-model="projectionType">
                        <label for="one">hendrik (testAcc by nParam)</label>
                    </v-list-tile>
                    <!-- <v-list-tile>
                        <v-list-tile-content>
                            <input type="checkbox" v-model="fixedWidth">
                            <label for="checkbox">Toggle Fixed Width</label>
                        </v-list-tile-content>
                    </v-list-tile>
                    <v-list-tile>
                        Layer Width Scale
                        <v-slider
                            v-model="logBase"
                            min=0.05
                            max=0.5
                            step=0.05
                        ></v-slider>
                    </v-list-tile> -->
                </v-list>

                <v-divider></v-divider>

                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="primary"
                        flat
                        @click="dialog = false"
                    >
                        I accept
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';

import * as _ from 'lodash';
import * as d3 from 'd3';

@Component({
    components: {
    }
})
export default class App extends Vue {
    private dialog: boolean = false;
    private projectionType: string = 'mds_otmann';

    constructor() {
        super();
    }

    @Watch('projectionType')
    private onProjectionTypeChanged(newProjType, oldProjType) {
        this.$store.commit('CHANGE_PROJECTION_TYPE', newProjType);
    }
}
</script>

<style lang="scss">
</style>
