package ai.giskard.utils;

import ai.giskard.web.dto.ColumnFilterDTO;
import org.apache.logging.log4j.util.Strings;
import tech.tablesaw.api.ColumnType;
import tech.tablesaw.api.NumericColumn;
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.selection.Selection;

import java.util.List;
import java.util.function.BiPredicate;

public class SelectionBuilder {

    private final Table table;
    private Selection selection;

    public SelectionBuilder(Table table) {
        this.table = table;
    }

    public SelectionBuilder and(List<ColumnFilterDTO> slicingFunctions) {
        slicingFunctions.forEach(this::and);
        return this;
    }

    public SelectionBuilder and(ColumnFilterDTO slicingFunction) {
        return and(toSelection(slicingFunction));
    }

    private Selection toSelection(ColumnFilterDTO slicingFunctionDTO) {
        return switch (slicingFunctionDTO.getColumnType()) {
            case TEXT -> toTextSelection(slicingFunctionDTO);
            case NUMERIC -> toNumericSelection(slicingFunctionDTO);
            case CATEGORY -> toCategoricalSelection(slicingFunctionDTO);
        };
    }

    private Selection toTextSelection(ColumnFilterDTO slicingFunctionDTO) {
        StringColumn column = table.stringColumn(slicingFunctionDTO.getColumn());

        return switch (slicingFunctionDTO.getSlicingType()) {
            case IS -> column.isEqualTo(slicingFunctionDTO.getValue());
            case IS_NOT -> column.isNotEqualTo(slicingFunctionDTO.getValue());
            case CONTAINS -> column.containsString(slicingFunctionDTO.getValue());
            case DOES_NOT_CONTAINS -> column.eval(not(String::contains), slicingFunctionDTO.getValue());
            case IS_EMPTY -> column.isMissing().or(column.eval(Strings::isBlank));
            case IS_NOT_EMPTY -> column.eval(Strings::isNotBlank);
            case STARTS_WITH -> column.startsWith(slicingFunctionDTO.getValue());
            case ENDS_WITH -> column.endsWith(slicingFunctionDTO.getValue());
        };
    }

    private Selection toNumericSelection(ColumnFilterDTO slicingFunctionDTO) {
        NumericColumn<?> column = table.numberColumn(slicingFunctionDTO.getColumn());


        return switch (slicingFunctionDTO.getSlicingType()) {
            case IS -> column.isEqualTo(Double.parseDouble(slicingFunctionDTO.getValue()));
            case IS_NOT -> column.isNotEqualTo(Double.parseDouble(slicingFunctionDTO.getValue()));
            case IS_EMPTY -> column.isMissing();
            case IS_NOT_EMPTY -> column.isNotMissing();
            default ->
                throw new IllegalArgumentException(String.format("Numeric columns does not support %s filter", slicingFunctionDTO.getSlicingType()));
        };
    }

    private Selection toCategoricalSelection(ColumnFilterDTO slicingFunctionDTO) {
        NumericColumn<?> column = table.numberColumn(slicingFunctionDTO.getColumn());

        if (ColumnType.STRING.equals(column.type())) {
            return toTextSelection(slicingFunctionDTO);
        } else {
            return toNumericSelection(slicingFunctionDTO);
        }
    }

    private <T, U> BiPredicate<T, U> not(BiPredicate<T, U> biPredicate) {
        return (t, u) -> !biPredicate.test(t, u);
    }

    private SelectionBuilder and(Selection selection) {
        if (this.selection == null) {
            this.selection = selection;
        } else {
            this.selection = this.selection.and(selection);
        }
        return this;
    }

    public Selection build() {
        return selection;
    }

}
