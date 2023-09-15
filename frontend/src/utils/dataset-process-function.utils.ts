import { DatasetDTO, DatasetProcessFunctionDTO, DatasetProcessFunctionType } from '@/generated-sources';

export class DatasetProcessFunctionUtils {

  static canApply(datasetProcessFunction: DatasetProcessFunctionDTO, dataset: DatasetDTO): boolean {

    switch (datasetProcessFunction.processType) {
      case DatasetProcessFunctionType.CLAUSES:
        return datasetProcessFunction.clauses.map(({ columnName }) => columnName)
          .every(column => Object.keys(dataset.columnDtypes).includes(column));
      case DatasetProcessFunctionType.CODE:
        return true;
    }
  }

}
