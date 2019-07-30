import * as d3 from 'd3';

export default class ColorManager {

    // from: https://www.ibm.com/design/language/resources/color-library/
    // private colorRepo = ['#34bc6e', '#fe8500', '#ff509e',
        // '#9b82f3', '#ffb000', '#95d13c'].reverse();
    // private colorRepo = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f']
    private colorRepo = ['#CF0638','#FA6632','#FECD23','#0A996F','#0A6789']
    // private colorRepo = ['#5392ff', '#a0e3f0', '#164d56', '#188291',
    private gradientRepo = ['#5392ff', '#a0e3f0', '#164d56', '#188291',
        '#00b6cb', '#a8c0f3', '#1f57a4'];
    private assignedColors = {};
    private assignedGradients = {};
    private outOfColorColor = '#aaa';

    constructor(colors?) {
        if (colors) {
            this.colorRepo = colors.map((d) => d).reverse();
        }
    }

    public getColor(id: string, create = true) {
        return this.getColorFromMapping(id, this.colorRepo, this.assignedColors, create);
    }

    public getGradient(id: string, create = true) {
        return this.getColorFromMapping(id, this.gradientRepo, this.assignedGradients, create);
    }

    // private assignedRepo = {
    //     'Conv2D': '#66c2a5',
    //     'Dense': '#fc8d62',
    //     'Activation': '#8da0cb',
    //     'Dropout': '#e78ac3',
    //     'AveragePooling2D': '#ffd92f'
    // }
    // private assignedRepo = {
    //     'Conv2D': '#CF0638',
    //     'Dense': '#FA6632',
    //     'Activation': '#FECD23',
    //     'Dropout': '#0A996F',
    //     'AveragePooling2D': '#0A6789'
    // }
    // private assignedRepo = {
    //     'Conv2D': '#FF4746',
    //     'Dense': '#E8DA5E',
    //     'Activation': '#92B55F',
    //     'Dropout': '#487D76',
    //     'AveragePooling2D': '#4B4452'
    // }
    // ["#3366cc", "#dc3912", "#ff9900", "#109618", "#990099", "#0099c6"]
    // private assignedRepo = {
    //     'Conv2D': d3.schemePaired[1],
    //     'Dense': d3.schemePaired[2],
    //     'Activation': d3.schemePaired[11],
    //     'Dropout': d3.schemePaired[6],
    //     'AveragePooling2D': d3.schemePaired[9]
    // }
    private assignedRepo = {
        'Conv2D': d3.schemePastel1[0],
        'Dense': d3.schemePastel1[1],
        'Activation': d3.schemePastel1[2],
        'Dropout': d3.schemePastel1[3],
        'AveragePooling2D': d3.schemePastel1[4]
    }
    // #FF4746,#E8DA5E,#92B55F,#487D76,#4B4452
    // 'MaxPool': '#a6d854',

    public getColorFromMapping(id: string, mappingRepo: string[], assignedRepo: {}, create = true) {
        // if (!(id in assignedRepo) && create) {
        //     let color = mappingRepo.pop();
        //     if (!color) {
        //         color = this.outOfColorColor;
        //     }
        //     assignedRepo[id] = color;
        // }

        // return assignedRepo[id];

        // For now, we're going to manually make this repo
        // Pooling layers share color
        if (id === 'MaxPool') {
            id = 'AveragePooling2D';
        }
        return this.assignedRepo[id]
    }

    public getColorKeys(): string[] {
        // return Object.keys(this.assignedColors);
        return Object.keys(this.assignedRepo);
    }

    public returnColor(id: string) {
        return this.returnColorFromMapping(id, this.colorRepo, this.assignedColors);
    }

    public returnGradient(id: string) {
        return this.returnColorFromMapping(id, this.gradientRepo, this.assignedGradients);
    }

    public returnColorFromMapping(id: string, mappingRepo: string[], assignedRepo: {}) {
        if (id in assignedRepo) {
            const color = assignedRepo[id];
            delete assignedRepo[id];

            if (color !== this.outOfColorColor) {
                mappingRepo.unshift(color);
            }
        }
    }

}
