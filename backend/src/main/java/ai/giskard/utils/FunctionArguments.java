package ai.giskard.utils;

import ai.giskard.domain.FunctionArgument;

public class FunctionArguments {

    public final static FunctionArgument COLUMN_NAME = FunctionArgument.builder()
        .name("column_name")
        .type("str")
        .optional(false)
        .build();

//    public static String funcArgumentToJson(FuncArgument funcArgument) {
//        String result = "";
//        switch (funcArgument.getArgumentCase()) {
//            case MODEL:
//                result = funcArgument.getModel().getId();
//                break;
//            case DATASET:
//                result = funcArgument.getDataset().getId();
//                break;
//            case SLICINGFUNCTION:
//                result = funcArgument.getSlicingFunction().getId();
//                break;
//            case TRANSFORMATIONFUNCTION:
//                result = funcArgument.getTransformationFunction().getId();
//                break;
//            case KWARGS:
//                // Not sure how to handle this cleanly yet.
//                break;
//            case ARGUMENT_NOT_SET:
//                break;
//            case BOOL:
//                result = String.valueOf(funcArgument.getBool());
//                break;
//            case FLOAT:
//                result = String.valueOf(funcArgument.getFloat());
//                break;
//            case INT:
//                result = String.valueOf(funcArgument.getInt());
//                break;
//            case STR:
//                result = funcArgument.getStr();
//                break;
//        }
//
//
//        Map<String, String> args = funcArgument.getArgsList().stream()
//            .collect(Collectors.toMap(FuncArgument::getName, FunctionArguments::funcArgumentToJson));
//
//        Map<String, Object> json = Map.of(
//            "value", result,
//            "args", args
//        );
//
//        // return json as a json
//        return new ObjectMapper().valueToTree(json).toString();
//    }

}
