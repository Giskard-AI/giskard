package ai.giskard.utils;

import ai.giskard.domain.FunctionArgument;

public class FunctionArguments {

    public final static FunctionArgument COLUMN_NAME = FunctionArgument.builder()
        .name("column_name")
        .type("str")
        .optional(false)
        .build();

}
