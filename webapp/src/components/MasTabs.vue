<template>
    <div class='model-tabs' ref='modelTabs'>
        <v-tabs
            fixed-tabs
            fixed
            slot="extension"
            dark
            v-model="active"
            >
            <v-tab
                v-for="n in tabHeaders"
                :key="n"
                ripple
            >
                {{ n }}

            </v-tab>

            <v-tab-item
                key="Data Selector"
            >
                <v-card class='mastabs-card' height="100%" style="overflow: auto">
                    <v-card-text>
                        <data-selector />
                    </v-card-text>
                </v-card>
            </v-tab-item>
            <v-tab-item
                key="Model Inspector"
            >
                <v-card class='mastabs-card' height="100%" style="overflow: auto">
                    <v-card-text>
                        <model-inspector
                            ref="myModelInspector" />
                    </v-card-text>
                </v-card>
            </v-tab-item>
            <v-tab-item
                key="Ablations"
            >
                <v-card class='mastabs-card' height="100%" style="overflow: auto">
                    <v-card-text>
                        <model-ablation />
                    </v-card-text>
                </v-card>
            </v-tab-item>

            <v-tab-item
                key='Queue'
            >
                <v-card class='mastabs-card' height="100%" style="overflow: auto">
                    <v-card-text>
                        <model-queue />
                    </v-card-text>
                </v-card>
            </v-tab-item>
        </v-tabs>
    </div>
</template>

<script lang="ts">
import { Component, Watch, Prop, Vue } from 'vue-property-decorator';
import * as d3 from 'd3';
import ModelInspector from './ModelInspector.vue';
import DataSelector from './DataSelector.vue';
import ModelQueue from './ModelQueue.vue';
import ModelAblation from './ModelAblation.vue';

@Component({
    components: {
        ModelInspector,
        DataSelector,
        ModelQueue,
        ModelAblation
    }
})
export default class MasTabs extends Vue {
    public active: number = 0;
    public tabHeaders = ['Data Selector', 'Model Inspector', 'Generate Models', 'Queue'];

    constructor() {
        super();
    }

    // vuetify is broken/doc is outdated and the change event doesn't fire
    // private onTabChange(tabval) {
    //     console.log("tabchange fired, val is ",tabval)
    //     this.$refs.myModelInspector.renderChart();
    // }

    @Watch('active')
    private onActiveChanged(newActive, oldActive) {
        console.log("ACTIVE CHANGED, newActive is ", newActive, " and oldActive is ", oldActive)
        if (this.tabHeaders[newActive] === 'Model Inspector') {
            console.log("changed to model Inspector");
            setTimeout(() => {
                console.log("should be rendering the freaking chart")
                this.$refs.myModelInspector.renderChart();
            }, 500);
        }
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang='scss'>
.model-tabs {
    height: 940px;
    // height: 100%;
    // overflow: scroll;

    .card__text, .card {
        padding: 2px !important;
    }

    .mastabs-card {
        min-height: 500px;
    }
}
</style>


