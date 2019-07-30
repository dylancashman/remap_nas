import LogDataInterface, {TableColumn, TableDatum} from './LogDataInterface';
import * as _ from 'lodash';

interface LogRow {
    et0: string;
    et1: string;
    et2: string;
    name: string;
    value: string;
    [key: string]: any;
}

/**
 * implementation of LDI for websocket example server
 */
export default class SocketData implements LogDataInterface {

    public data: LogRow[] = [];

    public details(projectID: string, ids: string[]): any {
        return null;
    }

    public projects(): string[] {
        return [];
    }

    public tableColumns(projectID: string): TableColumn[] {
        return [];
    }

    public getTableData(projectID: string): TableDatum[] {
        const allRows = _.groupBy(this.data, (d) => d.etime[0]);
        let i = 0;
        return Object.keys(allRows).map((k) => {
            // const row = <LogRow[]>allRows[k];
            // const row = allRows[k] as { [key: string]: LogRow[] };
            const rows = allRows[k] as LogRow[];
            const allAttributes = rows.reduce((a, r) => {
                const timestamp = r.timestamp;
                const values = r.values;
                Object.keys(values).map((myKey) => {
                    a[myKey] = a[myKey] || [];
                    a[myKey].push({timestamp, val: values[myKey]});
                });
                return a;
            }, Object.create(null));
            i += 1;
            let trainAccs: number[] = [];
            if ('train_acc' in allAttributes) {
                // trainAccs = _.sortBy(allAttributes.train_acc,
                //     (r) => Number.parseInt(r.et1) * 10000 + Number.parseInt(r.et2))
                //     .map((d) => Number.parseFloat(d.value));
                trainAccs = allAttributes.train_acc;
            }

            let valAccs: number[] = [];
            if ('val_acc' in allAttributes) {
                valAccs = allAttributes.val_acc;
            }
            if ('Accuracy1' in allAttributes) {
                valAccs = allAttributes.Accuracy1;
            }

            let loss: number[] = [];
            if ('loss' in allAttributes) {
                // loss = _.sortBy(allAttributes.loss,
                //     (r) => Number.parseInt(r.et1) * 10000 + Number.parseInt(r.et2))
                //     .map((d) => Number.parseFloat(d.value));
                loss = allAttributes.loss;
            }
            if ('SoftmaxWithLoss1' in allAttributes) {
                loss = allAttributes.SoftmaxWithLoss1;
            }

            let model = null;
            if ('model' in allAttributes) {
                model = allAttributes.model[0].NNModel;
            }

            let params = -1;
            if ('parameters' in allAttributes) {
                params = Number.parseInt(allAttributes.parameters[0].value, 10);
            }

            let memory = -1;
            if ('memory' in allAttributes) {
                memory = Number.parseInt(allAttributes.memory[0].value, 10);
            }

            let forwardTime = -1;
            if ('forward_time' in allAttributes) {
                forwardTime = Number.parseInt(allAttributes.forward_time[0].val, 10);
            }

            let backwardTime = -1;
            if ('backward_time' in allAttributes) {
                backwardTime = Number.parseInt(allAttributes.backward_time[0].val, 10);
            }
            // const accs = _.sortBy(row.filter(r => r.name === 'train_acc')
            //     , r => Number.parseInt(r.et1) * 10000 + Number.parseInt(r.et2))
            //     .map(d => Number.parseFloat(d.value));

            // const filterModel = row.filter(r => r.name === 'model');
            // let model = filterModel.length ? JSON.parse(filterModel[0].value) : null;

            // console.log(allAttributes, "--- allAttributes");

            return {
                id: k,
                trainAccs,
                valAccs,
                loss,
                model,
                params,
                memory,
                forwardTime,
                backwardTime
            };
        });
        // console.log(allRows, "--- allRows");
        //
        // return undefined;
    }

    public resetData() {
        this.data = [];
    }

    public addData(add: LogRow[]) {
        add.forEach((v) => this.data.push(v));
    }

}
