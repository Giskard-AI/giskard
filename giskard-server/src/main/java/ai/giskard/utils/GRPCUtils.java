package ai.giskard.utils;

import com.google.protobuf.DoubleValue;
import com.google.protobuf.Int32Value;
import com.google.protobuf.UInt32Value;

public class GRPCUtils {
    // @formatter:off
    public static Integer convertType(Int32Value val) {return val.isInitialized() ? val.getValue() : null;}
    public static Integer convertType(UInt32Value val) {return val.isInitialized() ? val.getValue() : null;}
    public static Double convertType(DoubleValue val) {return val.isInitialized() ? val.getValue() : null;}
    // @formatter:on

}
