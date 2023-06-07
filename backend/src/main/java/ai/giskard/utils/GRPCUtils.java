package ai.giskard.utils;

import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.*;
import com.google.protobuf.util.JsonFormat;

public class GRPCUtils {
    // @formatter:off
    public static Integer convertType(Int32Value val) {return val.isInitialized() ? val.getValue() : null;}
    public static Integer convertType(UInt32Value val) {return val.isInitialized() ? val.getValue() : null;}
    public static Double convertType(DoubleValue val) {return val.isInitialized() ? val.getValue() : null;}
    // @formatter:on

    public static <T> T convertGRPCObject(Message grpcObject, Class<T> clazz) {
        try {
            return new ObjectMapper().readValue(JsonFormat.printer().print(grpcObject), clazz);
        } catch (JsonProcessingException | InvalidProtocolBufferException e) {
            throw new GiskardRuntimeException("Failed to convert grpc object", e);
        }
    }
}
